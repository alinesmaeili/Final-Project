# -*- coding: utf-8 -*-
"""
This script performs the third and final step in the data preparation pipeline:
embedding and indexing the text chunks.

Its purpose is to create a searchable vector database from the cleaned and chunked
text. The script reads the text chunks from the JSONL file, generates a numerical
vector representation (an "embedding") for each chunk using the OpenAI API, and
then stores these embeddings along with their corresponding text and metadata in a
ChromaDB collection. This indexed collection forms the core knowledge base for the
retrieval-augmented generation (RAG) system.
"""

# --- Core Python Libraries ---
import os
import json
from typing import Dict, Iterable, List

# --- Environment and Configuration ---
# Loads environment variables from a .env file, which is a best practice for
# managing sensitive information like API keys.
from dotenv import load_dotenv
load_dotenv()

# --- Third-Party Libraries ---
# chromadb is the vector database used to store and query the text embeddings.
import chromadb
from chromadb.config import Settings
# tqdm provides a progress bar for monitoring the status of long-running loops.
from tqdm import tqdm
# requests is used to make HTTP requests to the OpenAI API for generating embeddings.
import requests

# --- Configuration Settings ---
# This section defines the necessary configuration parameters, loaded from
# environment variables for flexibility.
CHUNKS_JSONL = os.environ.get("CHUNKS_JSONL", "/workspace/data/chunks/chunks.jsonl")
CHROMA_DIR = os.environ.get("CHROMA_DIR", "/workspace/data/chroma")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "psych_textbook")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-large")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# A critical check to ensure the OpenAI API key is available.
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not set. Set it in your environment or .env before running.")


def read_jsonl(path: str) -> Iterable[Dict]:
    """
    Reads a JSON Lines (JSONL) file and yields each line as a dictionary.

    This function is memory-efficient because it reads the file line by line
    using a generator, rather than loading the entire file into memory.

    Args:
        path: The path to the JSONL file.

    Yields:
        A dictionary for each JSON object in the file.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def get_or_create_collection(client: chromadb.Client, name: str):
    """
    Safely retrieves a ChromaDB collection by name, or creates it if it doesn't exist.

    This function prevents errors that would occur if the script tried to access a
    collection that has not yet been created.

    Args:
        client: An active chromadb.Client instance.
        name: The name of the collection to get or create.

    Returns:
        The ChromaDB collection object.
    """
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name)


def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Sends a batch of text documents to the OpenAI API to generate embeddings.

    This function handles the communication with the OpenAI embeddings endpoint.
    Batching the requests is more efficient than sending one request per document.

    Args:
        texts: A list of text strings to be embedded.

    Returns:
        A list of embedding vectors, where each vector corresponds to a text string
        in the input batch.
    """
    url = f"{OPENAI_BASE_URL}/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    # The payload specifies the model to use and the input texts.
    payload = {"model": EMBED_MODEL, "input": texts}
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    # This will raise an HTTPError if the API returns a non-2xx status code.
    resp.raise_for_status()
    data = resp.json()
    # Extracts the embedding vectors from the API response.
    return [d["embedding"] for d in data["data"]]


if __name__ == "__main__":
    # Main execution block of the script.

    # Ensure the directory for the ChromaDB database exists.
    os.makedirs(CHROMA_DIR, exist_ok=True)
    # Initialize the ChromaDB client to create a persistent on-disk database.
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    # Get or create the specific collection where embeddings will be stored.
    collection = get_or_create_collection(chroma_client, COLLECTION_NAME)

    # Prepare lists to hold the data loaded from the chunks file.
    ids: List[str] = []
    metadatas: List[Dict] = []
    documents: List[str] = []

    # Load all the chunk records from the JSONL file into memory.
    for rec in tqdm(read_jsonl(CHUNKS_JSONL), desc="Loading chunks"):
        ids.append(rec["id"])
        metadatas.append({
            "page_number": rec.get("page_number"),
            "chunk_index": rec.get("chunk_index"),
        })
        documents.append(rec["text"])

    print(f"Embedding {len(documents)} chunks with the '{EMBED_MODEL}' model...")
    # Process the documents in batches to work within API and memory limits.
    batch_size = 128
    for start in tqdm(range(0, len(documents), batch_size), desc="Embedding"):
        # Slice the data for the current batch.
        batch_docs = documents[start:start + batch_size]
        batch_ids = ids[start:start + batch_size]
        batch_metas = metadatas[start:start + batch_size]
        
        # Call the OpenAI API to get embeddings for the batch.
        vectors = embed_batch(batch_docs)
        
        # Add the batch of embeddings, documents, and metadata to the Chroma collection.
        collection.add(ids=batch_ids, embeddings=vectors, metadatas=batch_metas, documents=batch_docs)

    print(f"\nSuccessfully populated Chroma collection '{COLLECTION_NAME}' at {CHROMA_DIR}")
    print(f"Total items in collection: {collection.count()}")
