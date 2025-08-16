# -*- coding: utf-8 -*-
"""
This script performs the second step in a data processing pipeline: cleaning and
chunking text.

It reads the JSONL file containing extracted PDF pages (produced by the previous
script), normalizes the text content of each page, and then splits the text into
smaller, overlapping chunks of a specified size. The primary goal is to create
manageable text segments that are suitable for language model embedding while
preserving context across chunk boundaries. The final output is another JSONL
file where each line represents a single text chunk.
"""

# --- Core Python Libraries ---
import os
import re
import json
from typing import Dict, Iterable, List

# --- Third-Party Libraries ---
# tqdm is used to display a progress bar, providing visual feedback on the
# progress of the chunking process, which can be time-consuming for large documents.
from tqdm import tqdm

# --- Configuration ---
# This section defines the input/output files and chunking parameters. Using
# environment variables allows for easy configuration without altering the code.
INPUT_JSONL = os.environ.get("INPUT_JSONL", "/workspace/data/chunks/pages.jsonl")
OUTPUT_JSONL = os.environ.get("OUTPUT_JSONL", "/workspace/data/chunks/chunks.jsonl")
CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", "1200"))
CHUNK_OVERLAP_TOKENS = int(os.environ.get("CHUNK_OVERLAP_TOKENS", "200"))

# Ensure the output directory exists before the script attempts to write the file.
os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)


def normalize_whitespace(text: str) -> str:
    """
    Cleans up and standardizes whitespace and special characters in a text string.

    This function is important for text consistency. It removes soft hyphens,
    which can be artifacts of PDF extraction, and collapses multiple whitespace
    characters into a single space.

    Args:
        text: The input string to be cleaned.

    Returns:
        The normalized text string.
    """
    text = text.replace("\u00ad", "")  # Remove soft hyphen
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def simple_word_count_tokenizer(text: str) -> List[str]:
    """
    A simple tokenizer that splits text into a list of words and punctuation.

    This tokenizer is used to approximate the number of "tokens" in a text for the
    purpose of creating chunks of a specific size.

    Args:
        text: The string to be tokenized.

    Returns:
        A list of string tokens.
    """
    return re.findall(r"\w+|[^\w\s]", text)


def chunk_text(text: str, max_tokens: int, overlap_tokens: int) -> List[str]:
    """
    Splits a long text into smaller chunks of a specified maximum size with overlap.

    The overlapping of chunks is a key strategy in RAG to ensure that semantic
    context is not lost at the boundary between two chunks.

    Args:
        text: The input text to be chunked.
        max_tokens: The maximum number of tokens allowed in a single chunk.
        overlap_tokens: The number of tokens from the end of one chunk to include
                        at the beginning of the next.

    Returns:
        A list of text chunks.
    """
    tokens = simple_word_count_tokenizer(text)
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        # If we've reached the end of the tokens, stop.
        if end == len(tokens):
            break
        # Otherwise, move the start pointer back by the overlap amount.
        start = end - overlap_tokens
        # Ensure the start pointer doesn't go negative.
        if start < 0:
            start = 0
    return chunks


def read_jsonl(path: str) -> Iterable[Dict]:
    """
    Reads a JSON Lines (JSONL) file and yields each line as a dictionary.

    This generator function is memory-efficient as it reads and processes the
    file one line at a time, which is ideal for large files.

    Args:
        path: The path to the JSONL file.

    Yields:
        A dictionary for each line in the file.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(records: Iterable[Dict], path: str) -> None:
    """
    Writes an iterable of dictionaries to a JSON Lines (JSONL) file.

    Each dictionary is written as a JSON string on a new line, creating a file
    that is easy for other programs to parse line by line.

    Args:
        records: An iterable of dictionaries to write.
        path: The path to the output file.
    """
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # This block is the main entry point for the script execution.

    # First, it checks if the required input file from the previous step exists.
    if not os.path.exists(INPUT_JSONL):
        raise FileNotFoundError(f"Missing input pages at {INPUT_JSONL}")

    out_records: List[Dict] = []
    # It then iterates through each record (page) in the input file.
    # The tqdm wrapper provides a progress bar for the user.
    for rec in tqdm(read_jsonl(INPUT_JSONL), desc="Chunking"):
        page_num = rec.get("page_number")
        # The text is normalized to ensure consistency.
        text = normalize_whitespace(rec.get("text", ""))

        # Skip any pages that are empty after normalization.
        if not text:
            continue

        # The core chunking logic is applied here.
        chunks = chunk_text(text, CHUNK_TOKENS, CHUNK_OVERLAP_TOKENS)

        # A new record is created for each chunk with a unique ID and metadata.
        for idx, chunk in enumerate(chunks):
            out_records.append({
                "id": f"page{page_num}_chunk{idx}",
                "page_number": page_num,
                "chunk_index": idx,
                "text": chunk,
            })

    # Finally, all the generated chunk records are written to the output file.
    write_jsonl(out_records, OUTPUT_JSONL)
    print(f"Successfully wrote {len(out_records)} chunks to {OUTPUT_JSONL}")
