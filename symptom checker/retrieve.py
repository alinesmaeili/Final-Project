# -*- coding: utf-8 -*-
"""
This module provides the core retrieval functionality for the RAG pipeline.

Its primary purpose is to execute a sophisticated "hybrid search" to find the most
relevant text chunks for a given user query. This approach combines the semantic
understanding of dense vector search with the keyword precision of a traditional
sparse search algorithm (BM25). By first retrieving a set of semantically similar
documents and then re-ranking them for keyword relevance, the system can achieve
more accurate and contextually appropriate results than either method could alone.
"""

# --- Core Python Libraries ---
import os
from typing import List, Dict, Tuple

# --- Third-Party Libraries ---
# chromadb is the client for the vector database, used for the initial semantic search.
import chromadb
from chromadb.config import Settings
# rank_bm25 provides the BM25 algorithm for efficient keyword-based re-ranking.
from rank_bm25 import BM25Okapi

# --- Configuration ---
# These environment variables point the retriever to the correct ChromaDB database
# and the specific collection where the document embeddings are stored.
CHROMA_DIR = os.environ.get("CHROMA_DIR", "/workspace/data/chroma")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "psych_textbook")


def _build_bm25_index(docs: List[str]) -> BM25Okapi:
    """
    Internal helper to build a BM25 index from a list of documents.

    Args:
        docs: A list of text strings to be indexed.

    Returns:
        An initialized BM25Okapi object ready for scoring.
    """
    tokenized_corpus = [doc.split() for doc in docs]
    return BM25Okapi(tokenized_corpus)


def _bm25_scores(bm25: BM25Okapi, query: str, docs: List[str]) -> List[float]:
    """
    Internal helper to calculate BM25 scores for a query against documents.

    Args:
        bm25: A pre-built BM25Okapi index.
        query: The user's search query.
        docs: The list of documents the query is scored against (used for context,
              though the scores come from the pre-built index).

    Returns:
        A list of relevance scores.
    """
    return bm25.get_scores(query.split()).tolist()


def _vector_search(collection, query: str, k: int = 10) -> Tuple[List[str], List[Dict], List[str]]:
    """
    Internal helper to perform a semantic vector search in ChromaDB.

    Args:
        collection: The ChromaDB collection object.
        query: The user's search query.
        k: The number of top results to retrieve.

    Returns:
        A tuple containing the IDs, metadata, and document texts of the results.
    """
    res = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )  # type: ignore
    ids = res.get("ids", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    documents = res.get("documents", [[]])[0]
    return ids, metadatas, documents


def hybrid_retrieve(query: str, k: int = 10) -> List[Dict]:
    """
    Performs a hybrid search combining vector search with BM25 re-ranking.

    This function is the public interface for the retrieval module. It follows a
    two-stage process to get the best possible results:
    1.  **Candidate Retrieval:** It first performs a fast, semantic search using
        ChromaDB's vector index to find a set of `k` candidate documents that are
        conceptually related to the query.
    2.  **Re-ranking:** It then takes these candidates and re-ranks them using the
        BM25 algorithm, which scores them based on keyword relevance.

    This hybrid approach ensures that the final results are not only semantically
    aligned with the query's intent but also contain the specific keywords from it,
    leading to higher overall relevance.

    Args:
        query: The user's search query string.
        k: The number of final, ranked results to return.

    Returns:
        A list of dictionaries, each representing a retrieved document, sorted
        by their final BM25 relevance score.
    """
    # Initialize the database client and get the target collection.
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    col = client.get_collection(COLLECTION_NAME)

    # Step 1: Get initial candidates from the vector search.
    v_ids, v_metas, v_docs = _vector_search(col, query, k=k)

    # Step 2: Re-rank the candidates using BM25 if any were found.
    if v_docs:
        bm25 = _build_bm25_index(v_docs)
        scores = _bm25_scores(bm25, query, v_docs)
        # Combine all data and sort by the new BM25 score.
        ranked = sorted(zip(v_ids, v_metas, v_docs, scores), key=lambda x: x[3], reverse=True)
    else:
        ranked = []

    # Format the ranked results into a clean list of dictionaries for the caller.
    results: List[Dict] = []
    for rid, meta, doc, score in ranked[:k]:
        results.append({
            "id": rid,
            "metadata": meta,
            "text": doc,
            "score": float(score),
        })
    return results
