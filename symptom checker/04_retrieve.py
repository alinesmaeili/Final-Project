import os
from typing import List, Dict, Tuple

import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from tqdm import tqdm

CHROMA_DIR = os.environ.get("CHROMA_DIR", "/workspace/data/chroma")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "psych_textbook")


def build_bm25_index(docs: List[str]) -> BM25Okapi:
    tokenized_corpus = [doc.split() for doc in docs]
    return BM25Okapi(tokenized_corpus)


def bm25_scores(bm25: BM25Okapi, query: str, docs: List[str]) -> List[float]:
    return bm25.get_scores(query.split()).tolist()


def vector_search(collection, query: str, k: int = 10) -> Tuple[List[str], List[Dict], List[str]]:
    res = collection.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"])  # type: ignore
    ids = res.get("ids", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    documents = res.get("documents", [[]])[0]
    return ids, metadatas, documents


def hybrid_retrieve(query: str, k: int = 10) -> List[Dict]:
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    col = client.get_collection(COLLECTION_NAME)

    # Vector search
    v_ids, v_metas, v_docs = vector_search(col, query, k=k)

    # BM25 over vector candidates for fast rerank
    if v_docs:
        bm25 = build_bm25_index(v_docs)
        scores = bm25_scores(bm25, query, v_docs)
        ranked = sorted(zip(v_ids, v_metas, v_docs, scores), key=lambda x: x[3], reverse=True)
    else:
        ranked = []

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
    examples = [
        "persistent low mood, anhedonia, sleep disturbance, fatigue",
        "panic attacks, palpitations, fear of dying",
    ]
    for q in examples:
        print("\nQUERY:", q)
        for r in hybrid_retrieve(q, k=5):
            print(f"- p{r['metadata'].get('page_number')} s={r['score']:.2f} :: {r['text'][:200]}...")