import os
import json
import time
import random
from typing import List, Dict, Iterable, Optional

from dotenv import load_dotenv
load_dotenv()

# Paths and settings
RAW_PDF_PATH = os.environ.get("RAW_PDF_PATH", "/workspace/data/raw/textbook.pdf")
PAGES_JSONL = os.environ.get("PAGES_JSONL", "/workspace/data/chunks/pages.jsonl")
CHUNKS_JSONL = os.environ.get("CHUNKS_JSONL", "/workspace/data/chunks/chunks.jsonl")
CHROMA_DIR = os.environ.get("CHROMA_DIR", "/workspace/data/chroma")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "psych_textbook")
PROMPT_PATH = os.environ.get("PROMPT_PATH", "/workspace/prompts/psych_guardrail.txt")

EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-large")
CHAT_MODEL = os.environ.get("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MAX_DOCS = int(os.environ.get("MAX_DOCS", "0"))  # 0 means no limit
SKIP_EMBEDDING = os.environ.get("SKIP_EMBEDDING", "0") == "1"

# Ensure env for downstream modules
os.environ.setdefault("CHROMA_DIR", CHROMA_DIR)
os.environ.setdefault("COLLECTION_NAME", COLLECTION_NAME)

import requests
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

# Reuse existing retrieval module if available
try:
    from src.retrieve import hybrid_retrieve as lib_hybrid_retrieve  # type: ignore
except Exception:
    lib_hybrid_retrieve = None


def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(records: Iterable[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def ensure_pages_extracted() -> None:
    if os.path.exists(PAGES_JSONL):
        return
    if not os.path.exists(RAW_PDF_PATH):
        raise FileNotFoundError(f"PDF not found at {RAW_PDF_PATH}")
    reader = PdfReader(RAW_PDF_PATH)
    pages: List[Dict] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({"page_number": i + 1, "text": text})
    write_jsonl(pages, PAGES_JSONL)


def normalize_whitespace(text: str) -> str:
    import re
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def simple_tokenize(text: str) -> List[str]:
    import re
    return re.findall(r"\w+|[^\w\s]", text)


def chunk_text(text: str, max_tokens: int = 1200, overlap_tokens: int = 200) -> List[str]:
    tokens = simple_tokenize(text)
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        if end == len(tokens):
            break
        start = max(0, end - overlap_tokens)
    return chunks


def ensure_chunks_built() -> None:
    if os.path.exists(CHUNKS_JSONL):
        return
    ensure_pages_extracted()
    outputs: List[Dict] = []
    for rec in read_jsonl(PAGES_JSONL):
        page_num = rec.get("page_number")
        text = normalize_whitespace(rec.get("text", ""))
        if not text:
            continue
        for idx, chunk in enumerate(chunk_text(text)):
            outputs.append({
                "id": f"page{page_num}_chunk{idx}",
                "page_number": page_num,
                "chunk_index": idx,
                "text": chunk,
            })
    write_jsonl(outputs, CHUNKS_JSONL)


def count_chunks() -> int:
    count = 0
    if not os.path.exists(CHUNKS_JSONL):
        return 0
    for _ in read_jsonl(CHUNKS_JSONL):
        count += 1
    return count


def get_collection(client: chromadb.Client, name: str):
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name)


def get_collection_count(collection) -> int:
    try:
        return collection.count()  # type: ignore
    except Exception:
        return 0


def embed_batch(texts: List[str]) -> List[List[float]]:
    url = f"{OPENAI_BASE_URL}/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"model": EMBED_MODEL, "input": texts}, timeout=120)
    if resp.status_code == 429:
        raise requests.HTTPError("429 Too Many Requests", response=resp)
    resp.raise_for_status()
    data = resp.json()
    return [d["embedding"] for d in data["data"]]


def build_embeddings_with_backoff() -> None:
    if SKIP_EMBEDDING:
        print("SKIP_EMBEDDING=1; skipping embedding step.")
        return
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set; add it to /workspace/.env")

    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    collection = get_collection(client, COLLECTION_NAME)

    total_chunks = count_chunks()
    existing = get_collection_count(collection)

    if existing >= total_chunks and total_chunks > 0 and (MAX_DOCS == 0 or existing >= min(total_chunks, MAX_DOCS)):
        print(f"Index already built: {existing}/{total_chunks} vectors present")
        return

    if existing > 0 and (MAX_DOCS == 0 and existing < total_chunks):
        print(f"Rebuilding collection to avoid partial index ({existing}/{total_chunks})...")
        client.delete_collection(COLLECTION_NAME)
        collection = client.create_collection(COLLECTION_NAME)

    ids: List[str] = []
    metadatas: List[Dict] = []
    documents: List[str] = []
    for rec in read_jsonl(CHUNKS_JSONL):
        ids.append(rec["id"])
        metadatas.append({"page_number": rec.get("page_number"), "chunk_index": rec.get("chunk_index")})
        documents.append(rec["text"])

    if MAX_DOCS > 0:
        ids = ids[:MAX_DOCS]
        metadatas = metadatas[:MAX_DOCS]
        documents = documents[:MAX_DOCS]
        print(f"Limiting embedding to first {MAX_DOCS} chunks for quick run")

    print(f"Embedding {len(documents)} chunks with {EMBED_MODEL}...")
    batch_size = 32
    start = 0
    while start < len(documents):
        batch_docs = documents[start:start + batch_size]
        batch_ids = ids[start:start + batch_size]
        batch_metas = metadatas[start:start + batch_size]
        attempt = 0
        while True:
            try:
                vectors = embed_batch(batch_docs)
                break
            except requests.HTTPError as e:
                status = e.response.status_code if getattr(e, 'response', None) is not None else None
                if status == 429 and attempt < 8:
                    sleep_s = min(60, (2 ** attempt)) + random.uniform(0, 0.5)
                    print(f"Rate limited; retrying in {sleep_s:.1f}s (attempt {attempt+1})")
                    time.sleep(sleep_s)
                    attempt += 1
                    continue
                print("Embedding failed for this batch; skipping due to repeated rate limits.")
                vectors = [[0.0] * 1536 for _ in batch_docs]
                break
        collection.add(ids=batch_ids, embeddings=vectors, metadatas=batch_metas, documents=batch_docs)
        start += batch_size
        print(f"Indexed {min(start, len(documents))}/{len(documents)}")

    print(f"Chroma collection '{COLLECTION_NAME}' built at {CHROMA_DIR}")


def load_system_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def format_context(ctx: List[Dict]) -> str:
    lines = []
    for r in ctx:
        page = r.get("metadata", {}).get("page_number")
        lines.append(f"[Page {page}] {r['text']}")
    return "\n\n".join(lines)


def chat_json(system_prompt: str, user_prompt: str) -> Dict:
    url = f"{OPENAI_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": CHAT_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except Exception:
        return {"raw": content}


def bm25_retrieve_all(query: str, k: int = 8) -> List[Dict]:
    docs: List[str] = []
    metas: List[Dict] = []
    for rec in read_jsonl(CHUNKS_JSONL):
        docs.append(rec.get("text", ""))
        metas.append({"page_number": rec.get("page_number"), "chunk_index": rec.get("chunk_index")})
    if not docs:
        return []
    bm25 = BM25Okapi([d.split() for d in docs])
    scores = bm25.get_scores(query.split()).tolist()
    ranked = sorted(zip(range(len(docs)), metas, docs, scores), key=lambda x: x[3], reverse=True)
    results: List[Dict] = []
    for idx, meta, doc, score in ranked[:k]:
        results.append({"id": f"bm25_{idx}", "metadata": meta, "text": doc, "score": float(score)})
    return results


def hybrid_retrieve(query: str, k: int = 8) -> List[Dict]:
    if lib_hybrid_retrieve is not None:
        try:
            return lib_hybrid_retrieve(query, k=k)
        except Exception:
            pass
    # Try Chroma directly; on error fallback to BM25 over all chunks
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
        col = client.get_collection(COLLECTION_NAME)
        res = col.query(query_texts=[query], n_results=k, include=["documents", "metadatas"])  # type: ignore
        ids = res.get("ids", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        documents = res.get("documents", [[]])[0]
        bm25 = BM25Okapi([doc.split() for doc in documents]) if documents else None
        scores = bm25.get_scores(query.split()).tolist() if bm25 else [0.0] * len(documents)
        ranked = sorted(zip(ids, metadatas, documents, scores), key=lambda x: x[3], reverse=True)
        return [{"id": i, "metadata": m, "text": d, "score": float(s)} for i, m, d, s in ranked[:k]]
    except Exception:
        return bm25_retrieve_all(query, k=k)


def answer(user_report: str) -> Dict:
    system_prompt = load_system_prompt()
    ctx = hybrid_retrieve(user_report, k=8)
    context = format_context(ctx)
    schema = {
        "triage_level": "emergency | urgent | routine | self-care",
        "red_flags": [{"flag": "string", "evidence": "string"}],
        "likely_conditions": [
            {
                "name": "string",
                "confidence": 0.0,
                "rationale": "string",
                "differentials": ["string"],
                "citations": [{"source": "Textbook", "section": "", "pages": [0]}],
            }
        ],
        "recommended_actions": {
            "self_care": ["string"],
            "professional": ["string"],
            "crisis": "string",
        },
        "limitations": "string",
    }
    user_prompt = (
        f"User symptoms/report:\n{user_report}\n\nRetrieved textbook excerpts (cite pages):\n{context}\n\n"
        f"Output strict JSON exactly in this schema (keys and types):\n{json.dumps(schema)}"
    )
    return chat_json(system_prompt, user_prompt)


def run_demo() -> None:
    demo = "low mood most days, loss of interest, fatigue, poor sleep for 6 weeks; work impairment"
    print(json.dumps(answer(demo), indent=2))


if __name__ == "__main__":
    # Ensure chunks and index exist
    ensure_chunks_built()
    build_embeddings_with_backoff()
    # Demo run
    run_demo()