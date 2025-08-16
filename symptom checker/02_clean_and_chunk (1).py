import os
import re
import json
from typing import Dict, Iterable, List
from tqdm import tqdm

INPUT_JSONL = os.environ.get("INPUT_JSONL", "/workspace/data/chunks/pages.jsonl")
OUTPUT_JSONL = os.environ.get("OUTPUT_JSONL", "/workspace/data/chunks/chunks.jsonl")
CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", "1200"))
CHUNK_OVERLAP_TOKENS = int(os.environ.get("CHUNK_OVERLAP_TOKENS", "200"))

os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00ad", "")  # soft hyphen
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def simple_word_count_tokenizer(text: str) -> List[str]:
    return re.findall(r"\w+|[^\w\s]", text)


def chunk_text(text: str, max_tokens: int, overlap_tokens: int) -> List[str]:
    tokens = simple_word_count_tokenizer(text)
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        if end == len(tokens):
            break
        start = end - overlap_tokens
        if start < 0:
            start = 0
    return chunks


def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(records: Iterable[Dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if not os.path.exists(INPUT_JSONL):
        raise FileNotFoundError(f"Missing input pages at {INPUT_JSONL}")
    out_records: List[Dict] = []
    for rec in tqdm(read_jsonl(INPUT_JSONL), desc="Chunking"):
        page_num = rec.get("page_number")
        text = normalize_whitespace(rec.get("text", ""))
        if not text:
            continue
        chunks = chunk_text(text, CHUNK_TOKENS, CHUNK_OVERLAP_TOKENS)
        for idx, chunk in enumerate(chunks):
            out_records.append({
                "id": f"page{page_num}_chunk{idx}",
                "page_number": page_num,
                "chunk_index": idx,
                "text": chunk,
            })
    write_jsonl(out_records, OUTPUT_JSONL)
    print(f"Wrote {len(out_records)} chunks to {OUTPUT_JSONL}")