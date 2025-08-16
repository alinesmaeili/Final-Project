# -*- coding: utf-8 -*-
"""
This script performs the first step in a data processing pipeline: extracting raw
text from a PDF document.

Its primary responsibility is to read a specified PDF file, iterate through each page,
extract the text content, and then save the output into a JSON Lines (JSONL) file.
Each line in the output file corresponds to a single page from the PDF, containing
the page number and its extracted text. This structured output serves as the input
for subsequent chunking and embedding processes.
"""

# --- Core Python Libraries ---
import os
import json
from typing import List, Dict

# --- Third-Party Libraries ---
# pypdf is used for its robust PDF reading and text extraction capabilities.
from pypdf import PdfReader
# tqdm provides a simple and effective way to display a progress bar for long-running loops.
from tqdm import tqdm

# --- Configuration ---
# This section defines the input and output paths for the script.
# Using environment variables allows for flexible configuration without modifying the code.
RAW_PDF_PATH = os.environ.get("RAW_PDF_PATH", "/workspace/data/raw/textbook.pdf")
OUTPUT_JSONL = os.environ.get("OUTPUT_JSONL", "/workspace/data/chunks/pages.jsonl")

# Ensure the directory for the output file exists before writing to it.
os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)


def extract_pages(pdf_path: str) -> List[Dict]:
    """
    Reads a PDF file and extracts the text from each page.

    This function iterates through all pages of the specified PDF, extracts the raw
    text content from each, and structures it into a list of dictionaries. A progress

    bar is displayed to provide feedback on the extraction process.

    Args:
        pdf_path: The full path to the input PDF file.

    Returns:
        A list of dictionaries, where each dictionary represents a page and
        contains the 'page_number' and its 'text' content.
    """
    reader = PdfReader(pdf_path)
    pages: List[Dict] = []
    # Use tqdm to show a progress bar, which is helpful for large PDFs.
    for i, page in enumerate(tqdm(reader.pages, desc="Extracting PDF pages")):
        try:
            # Attempt to extract text; handle potential errors gracefully.
            text = page.extract_text() or ""
        except Exception:
            text = ""  # If extraction fails for a page, save an empty string.
        pages.append({
            "page_number": i + 1,
            "text": text,
        })
    return pages


def write_jsonl(records: List[Dict], output_path: str) -> None:
    """
    Writes a list of dictionary records to a JSON Lines (JSONL) file.

    Each dictionary in the list is converted to a JSON string and written to a
    new line in the output file. This format is efficient for line-by-line
    processing in downstream tasks.

    Args:
        records: A list of dictionaries to be written to the file.
        output_path: The path of the file to write to.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # This block serves as the main entry point for the script.
    
    # First, validate that the required input PDF file actually exists.
    if not os.path.exists(RAW_PDF_PATH):
        raise FileNotFoundError(f"PDF not found at {RAW_PDF_PATH}. Place your textbook at this path.")
    
    # Run the extraction and writing processes.
    print(f"Starting text extraction from: {RAW_PDF_PATH}")
    pages = extract_pages(RAW_PDF_PATH)
    write_jsonl(pages, OUTPUT_JSONL)
    
    # Print a confirmation message to the user.
    print(f"Successfully wrote {len(pages)} page records to {OUTPUT_JSONL}")
