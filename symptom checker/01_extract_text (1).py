import os
import json
from typing import List, Dict
from pypdf import PdfReader
from tqdm import tqdm

RAW_PDF_PATH = os.environ.get("RAW_PDF_PATH", "/workspace/data/raw/textbook.pdf")
OUTPUT_JSONL = os.environ.get("OUTPUT_JSONL", "/workspace/data/chunks/pages.jsonl")
os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)


def extract_pages(pdf_path: str) -> List[Dict]:
    reader = PdfReader(pdf_path)
    pages: List[Dict] = []
    for i, page in enumerate(tqdm(reader.pages, desc="Extracting PDF pages")):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({
            "page_number": i + 1,
            "text": text,
        })
    return pages


def write_jsonl(records: List[Dict], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if not os.path.exists(RAW_PDF_PATH):
        raise FileNotFoundError(f"PDF not found at {RAW_PDF_PATH}. Place your textbook at this path.")
    pages = extract_pages(RAW_PDF_PATH)
    write_jsonl(pages, OUTPUT_JSONL)
    print(f"Wrote {len(pages)} page records to {OUTPUT_JSONL}")