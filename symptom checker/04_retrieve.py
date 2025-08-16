# -*- coding: utf-8 -*-
"""
This script implements the retrieval logic for the RAG (Retrieval-Augmented
Generation) pipeline.

Its core function is to perform a hybrid search, which combines the strengths of
dense vector search (for semantic similarity) and sparse keyword search (BM25, for
relevance). Given a user query, this script retrieves the most relevant text chunks
from the indexed ChromaDB collection. This two-stage retrieval process—a broad
semantic search followed by a keyword-based re-ranking—is designed to yield more
accurate and relevant context for the final generation step.
"""

# --- Core Python Libraries ---
import os
from typing import List, Dict, Tuple

# --- Third-Party Libraries ---
# chromadb is the client library for interacting with the vector database.
import chromadb
from chromadb.config import Settings
# rank_bm25 provides an efficient implementation of the BM25 algorithm for keyword search.
from rank_bm25 import BM25Okapi
# tqdm is used for displaying progress bars (though not in the final version of this script,
# it's a common utility in the project).
from tqdm import tqdm


# --- Configuration ---
# This section defines the location of the vector database and the name of the
# collection to be queried. These are set via environment variables for flexibility.
CHROMA_DIR = os.environ.get("CHROMA_DIR", "/workspace/data/chroma")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "psych_textbook")


def build_bm25_index(docs: List[str]) -> BM25Okapi:
    """
    Constructs a BM25Okapi index from a list of documents.

    This index is used for efficient keyword-based scoring and re-ranking of search results.

    Args:
        docs: A list of text documents (strings) to be indexed.

    Returns:
        An initialized BM25Okapi object ready for querying.
    """
    # The documents are tokenized by splitting on whitespace for the BM25 algorithm.
    tokenized_corpus = [doc.split() for doc in docs]
    return BM25Okapi(tokenized_corpus)


def bm25_scores(bm25: BM25Okapi, query: str, docs: List[str]) -> List[float]:
    """
    Calculates BM25 relevance scores for a query against a list of documents.

    Args:
        bm25: A pre-built BM25Okapi index.
        query: The user's search query string.
        docs: The list of documents to score the query against.

    Returns:
        A list of float scores, one for each document.
    """
    # The query is also tokenized before scoring.
    return bm25.get_scores(query.split()).tolist()


def vector_search(collection, query: str, k: int = 10) -> Tuple[List[str], List[Dict], List[str]]:
    """
    Performs a semantic vector search against the ChromaDB collection.

    This function queries the vector database to find the top `k` documents that are
    semantically most similar to the user's query.

    Args:
        collection: The ChromaDB collection object to query.
        query: The user's search query string.
        k: The number of top results to retrieve.

    Returns:
        A tuple containing lists of the retrieved document IDs, metadatas, and texts.
    """
    # The `query` method in ChromaDB handles the embedding of the query and the search.
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
    Executes a hybrid retrieval process combining vector search and BM25 re-ranking.

    This is the main retrieval function. The strategy is:
    1.  Perform a fast vector search in ChromaDB to get a set of `k` candidate
        documents that are semantically related to the query.
    2.  Create a small, on-the-fly BM25 index from only these candidate documents.
    3.  Re-rank the candidates based on their BM25 keyword relevance scores.
    This approach leverages the semantic understanding of vector search with the
    keyword precision of BM25 for highly relevant results.

    Args:
        query: The user's search query string.
        k: The final number of results to return after re-ranking.

    Returns:
        A list of dictionaries, each representing a retrieved document, sorted
        by relevance.
    """
    # Initialize the ChromaDB client and get the collection.
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    col = client.get_collection(COLLECTION_NAME)

    # Step 1: Perform the initial vector search to get candidate documents.
    v_ids, v_metas, v_docs = vector_search(col, query, k=k)

    # Step 2: Use BM25 to re-rank the vector search results.
    if v_docs:
        bm25 = build_bm25_index(v_docs)
        scores = bm25_scores(bm25, query, v_docs)
        # Combine the results and sort by the new BM25 score in descending order.
        ranked = sorted(zip(v_ids, v_metas, v_docs, scores), key=lambda x: x[3], reverse=True)
    else:
        ranked = []

    # Format the final results into a clean list of dictionaries.
    results: List[Dict] = []
    for rid, meta, doc, score in ranked[:k]:
        results.append({
            "id": rid,
            "metadata": meta,
            "text": doc,
            "score": float(score),
        })
    return results


if __name__ == "__main__":
    # This block demonstrates the usage of the hybrid_retrieve function.
    # It runs a few example queries and prints the top results to the console,
    # showing the page number, relevance score, and a snippet of the retrieved text.
    
    examples = [
        "persistent low mood, anhedonia, sleep disturbance, fatigue",
        "panic attacks, palpitations, fear of dying",
    ]
    
    print("--- Running Retrieval Demo ---")
    for q in examples:
        print("\nQUERY:", q)
        retrieved_docs = hybrid_retrieve(q, k=5)
        if not retrieved_docs:
            print("  -> No results found.")
            continue
            
        for r in retrieved_docs:
            page_num = r['metadata'].get('page_number', 'N/A')
            score = r['score']
            text_snippet = r['text'][:200].replace('\n', ' ')
            print(f"- p{page_num} (score={score:.2f}): '{text_snippet}...'")
