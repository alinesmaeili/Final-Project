# -*- coding: utf-8 -*-
"""
This script, "Eureka Symptom Checker," implements a complete Retrieval-Augmented
Generation (RAG) pipeline designed for psychological symptom analysis.

The primary function of this application is to process a source PDF textbook,
transform it into a searchable knowledge base, and use that base to provide
structured, evidence-based responses to user queries about mental health symptoms.

The end-to-end workflow consists of several key stages:
1.  Data Ingestion and Processing: The script first reads a specified PDF file,
    extracts the text from each page, and then breaks down the text into smaller,
    more manageable chunks. This chunking process is vital for creating effective
    and contextually relevant embeddings.

2.  Indexing and Storage: Each text chunk is then converted into a numerical vector
    (an embedding) using a sophisticated language model from OpenAI. These embeddings
    are stored in a ChromaDB vector database, creating a highly efficient and searchable
    index of the textbook's content.

3.  Retrieval Mechanism: When a user provides a query (a description of their
    symptoms), the script employs a hybrid search strategy. It combines semantic
    search (via vector embeddings) and keyword-based search (BM25) to retrieve the
    most relevant passages from the indexed textbook.

4.  AI-Powered Generation: The retrieved text passages are combined with the user's
    original query and a system prompt, which are then sent to a powerful chat model
    (like GPT-4o-mini). The model's task is to synthesize this information and generate
    a structured JSON response, detailing potential conditions, recommended actions,
    and important red flags, all based on the textbook's content.
"""

# --- Core Python Libraries ---
# These are standard Python libraries used for file system operations, data handling,
# timing, and generating randomness.
import os
import json
import time
import random
from typing import List, Dict, Iterable, Optional

# --- Environment Configuration ---
# The dotenv library is used to load environment variables from a `.env` file.
# This is a best practice for managing configuration settings securely and separately
# from the application code.
from dotenv import load_dotenv
load_dotenv()

# --- Global Configuration Settings ---
# This section defines all the key configuration parameters for the application.
# It pulls values from environment variables, providing sensible defaults if they
# are not set. This approach makes the application flexible and easy to configure
# for different environments (development, testing, production) without code changes.

# File and Directory Paths
RAW_PDF_PATH = os.environ.get("RAW_PDF_PATH", "/workspace/data/raw/textbook.pdf")
PAGES_JSONL = os.environ.get("PAGES_JSONL", "/workspace/data/chunks/pages.jsonl")
CHUNKS_JSONL = os.environ.get("CHUNKS_JSONL", "/workspace/data/chunks/chunks.jsonl")
CHROMA_DIR = os.environ.get("CHROMA_DIR", "/workspace/data/chroma")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "psych_textbook")
PROMPT_PATH = os.environ.get("PROMPT_PATH", "/workspace/prompts/psych_guardrail.txt")

# OpenAI Model and API Configuration
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-large")
CHAT_MODEL = os.environ.get("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Script Execution Control
MAX_DOCS = int(os.environ.get("MAX_DOCS", "0"))  # Use 0 for no limit, or a number for quick tests
SKIP_EMBEDDING = os.environ.get("SKIP_EMBEDDING", "0") == "1"

# Propagate essential environment variables to be accessible by other modules.
os.environ.setdefault("CHROMA_DIR", CHROMA_DIR)
os.environ.setdefault("COLLECTION_NAME", COLLECTION_NAME)


# --- Third-Party Library Imports ---
# These libraries provide the core functionalities of the RAG pipeline.
import requests                 # Used for making API calls to the OpenAI services.
import chromadb                 # The client for the Chroma vector database.
from chromadb.config import Settings
from pypdf import PdfReader     # A powerful library for reading and extracting text from PDF files.
from rank_bm25 import BM25Okapi # An implementation of the BM25 algorithm for efficient keyword-based search.

# --- Optional Module Import ---
# This attempts to import a potentially more advanced or customized retrieval function
# from a local `src` directory. If this module is not available, the script gracefully
# falls back to its own built-in `hybrid_retrieve` function.
try:
    from src.retrieve import hybrid_retrieve as lib_hybrid_retrieve  # type: ignore
except Exception:
    lib_hybrid_retrieve = None


def read_jsonl(path: str) -> Iterable[Dict]:
    """
    Reads a JSON Lines (JSONL) file and yields each line as a dictionary.
    This function is memory-efficient as it processes the file line by line,
    making it suitable for very large datasets.

    Args:
        path: The file path to the JSONL file.

    Yields:
        A dictionary representation of each JSON object in the file.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(records: Iterable[Dict], path: str) -> None:
    """
    Writes an iterable of dictionaries to a JSON Lines (JSONL) file.
    Each dictionary is serialized to a JSON string and written as a separate line.
    This function also ensures that the target directory exists before writing.

    Args:
        records: An iterable (e.g., a list) of dictionaries to be written.
        path: The destination file path.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def ensure_pages_extracted() -> None:
    """
    Checks if the PDF has been processed; if not, it extracts text from each page.
    The function reads the PDF specified by `RAW_PDF_PATH`, extracts its text content
    page by page, and saves the result into the `PAGES_JSONL` file. This prevents
    re-processing the PDF on every run.
    """
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
            text = ""  # Handle cases where text extraction might fail for a page.
        pages.append({"page_number": i + 1, "text": text})
    write_jsonl(pages, PAGES_JSONL)


def normalize_whitespace(text: str) -> str:
    """
    Cleans and standardizes whitespace in a string.
    This function removes unwanted characters like soft hyphens and collapses
    multiple whitespace characters into a single space for consistency.

    Args:
        text: The input string.

    Returns:
        The normalized string.
    """
    import re
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def simple_tokenize(text: str) -> List[str]:
    """
    A basic text tokenizer that splits a string into words and punctuation.

    Args:
        text: The string to tokenize.

    Returns:
        A list of tokens (words and punctuation).
    """
    import re
    return re.findall(r"\w+|[^\w\s]", text)


def chunk_text(text: str, max_tokens: int = 1200, overlap_tokens: int = 200) -> List[str]:
    """
    Splits a long text into smaller, overlapping chunks.
    Chunking is essential for RAG because it breaks down large documents into
    manageable pieces that can be effectively embedded and retrieved. The overlap
    helps maintain context between adjacent chunks.

    Args:
        text: The text to be chunked.
        max_tokens: The maximum size of each chunk in tokens.
        overlap_tokens: The number of tokens to include from the end of the previous
                        chunk at the beginning of the next.

    Returns:
        A list of text chunks.
    """
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
    """
    Ensures that the text from the PDF pages has been chunked and saved.
    This function reads the extracted pages from `PAGES_JSONL`, processes the text
    from each page (normalization and chunking), and writes the resulting chunks
    to `CHUNKS_JSONL`. It skips the process if the output file already exists.
    """
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
    """
    Counts the total number of chunks available in the `CHUNKS_JSONL` file.

    Returns:
        The total count of chunks.
    """
    count = 0
    if not os.path.exists(CHUNKS_JSONL):
        return 0
    for _ in read_jsonl(CHUNKS_JSONL):
        count += 1
    return count


def get_collection(client: chromadb.Client, name: str):
    """
    Retrieves a ChromaDB collection by name, creating it if it doesn't exist.

    Args:
        client: The ChromaDB client instance.
        name: The name of the collection.

    Returns:
        A ChromaDB collection object.
    """
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name)


def get_collection_count(collection) -> int:
    """
    Safely retrieves the number of items currently in a ChromaDB collection.

    Args:
        collection: The ChromaDB collection object.

    Returns:
        The number of items in the collection, or 0 on error.
    """
    try:
        return collection.count()  # type: ignore
    except Exception:
        return 0


def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a batch of texts using the OpenAI API.

    Args:
        texts: A list of text strings to embed.

    Returns:
        A list of embedding vectors, where each vector is a list of floats.
    """
    url = f"{OPENAI_BASE_URL}/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"model": EMBED_MODEL, "input": texts}, timeout=120)
    if resp.status_code == 429:
        raise requests.HTTPError("429 Too Many Requests", response=resp)
    resp.raise_for_status()
    data = resp.json()
    return [d["embedding"] for d in data["data"]]


def build_embeddings_with_backoff() -> None:
    """
    Orchestrates the process of embedding all text chunks and storing them in ChromaDB.
    This function handles batching, API calls, and includes an exponential backoff
    retry mechanism to gracefully manage API rate limits. It also includes logic to
    avoid re-embedding if the index is already complete.
    """
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
    """
    Loads the system prompt from the file specified by `PROMPT_PATH`.
    The system prompt provides high-level instructions to the chat model on how
    to behave and what kind of output to generate.

    Returns:
        The content of the system prompt file as a string.
    """
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def format_context(ctx: List[Dict]) -> str:
    """
    Formats the retrieved document chunks into a single string for the prompt.
    Each chunk is prepended with its page number to provide clear citation context
    for the language model.

    Args:
        ctx: A list of retrieved document objects.

    Returns:
        A formatted string containing all the context information.
    """
    lines = []
    for r in ctx:
        page = r.get("metadata", {}).get("page_number")
        lines.append(f"[Page {page}] {r['text']}")
    return "\n\n".join(lines)


def chat_json(system_prompt: str, user_prompt: str) -> Dict:
    """
    Sends a request to the OpenAI Chat Completions API and returns a JSON response.
    This function constructs the API payload, including the system and user prompts,
    and requests a JSON object as the response format.

    Args:
        system_prompt: The instructional prompt for the model.
        user_prompt: The user's query combined with the retrieved context.

    Returns:
        A dictionary parsed from the model's JSON response.
    """
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
    """
    Performs a BM25 keyword search over all chunks in the `CHUNKS_JSONL` file.
    This serves as a fallback retrieval method if ChromaDB is unavailable.

    Args:
        query: The user's search query.
        k: The number of top results to return.

    Returns:
        A list of the top k matching document chunks.
    """
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
    """
    Performs a hybrid search to retrieve the most relevant document chunks.
    It first attempts to use a pre-imported retrieval library. If that fails, it
    queries ChromaDB for a semantic search and then re-ranks the results using BM25
    for keyword relevance. If ChromaDB fails, it falls back to a full BM25 search.

    Args:
        query: The user's search query.
        k: The number of results to return.

    Returns:
        A list of the top k relevant document chunks.
    """
    if lib_hybrid_retrieve is not None:
        try:
            return lib_hybrid_retrieve(query, k=k)
        except Exception:
            pass
    # Try Chroma first, then fallback to BM25 if there's an error.
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
        col = client.get_collection(COLLECTION_NAME)
        res = col.query(query_texts=[query], n_results=k, include=["documents", "metadatas"])  # type: ignore
        ids = res.get("ids", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        documents = res.get("documents", [[]])[0]
        # Re-rank the semantic search results with BM25 for keyword relevance.
        bm25 = BM25Okapi([doc.split() for doc in documents]) if documents else None
        scores = bm25.get_scores(query.split()).tolist() if bm25 else [0.0] * len(documents)
        ranked = sorted(zip(ids, metadatas, documents, scores), key=lambda x: x[3], reverse=True)
        return [{"id": i, "metadata": m, "text": d, "score": float(s)} for i, m, d, s in ranked[:k]]
    except Exception:
        return bm25_retrieve_all(query, k=k)


def answer(user_report: str) -> Dict:
    """
    The main function that orchestrates the RAG pipeline for a given user query.
    It retrieves relevant context, constructs a detailed prompt with a specific JSON
    schema, and calls the chat model to generate a structured answer.

    Args:
        user_report: The user's query describing their symptoms.

    Returns:
        A dictionary containing the structured, AI-generated response.
    """
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
    # This detailed prompt guides the model to use the provided context and
    # adhere strictly to the requested JSON output format.
    user_prompt = (
        f"User symptoms/report:\n{user_report}\n\nRetrieved textbook excerpts (cite pages):\n{context}\n\n"
        f"Output strict JSON exactly in this schema (keys and types):\n{json.dumps(schema)}"
    )
    return chat_json(system_prompt, user_prompt)


def run_demo() -> None:
    """
    Runs a demonstration of the symptom checker with a sample query.
    This function calls the main `answer` function with a predefined symptom report
    and prints the structured JSON response to the console.
    """
    demo_query = "low mood most days, loss of interest, fatigue, poor sleep for 6 weeks; work impairment"
    print(f"Running demo with query: '{demo_query}'")
    response = answer(demo_query)
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    # This is the main entry point of the script.
    # When the script is executed directly, it first ensures that all necessary
    # data processing steps (chunking and embedding) are complete.
    print("--- Starting Eureka Symptom Checker Pipeline ---")

    # Step 1: Ensure the PDF is processed into text chunks.
    print("Step 1: Checking for processed text chunks...")
    ensure_chunks_built()
    print("Done.")

    # Step 2: Build or verify the vector database embeddings.
    print("\nStep 2: Building or verifying embeddings in ChromaDB...")
    build_embeddings_with_backoff()
    print("Done.")

    # Step 3: Run a demonstration query.
    print("\nStep 3: Running a demo analysis...")
    run_demo()
    print("\n--- Pipeline Demo Finished ---")
