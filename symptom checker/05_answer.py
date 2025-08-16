# -*- coding: utf-8 -*-
"""
This script represents the final "generation" step of the RAG (Retrieval-Augmented
Generation) pipeline.

Its primary function is to synthesize information to answer a user's query. It
orchestrates the entire end-to-end process for a single request:
1.  It takes a user's report (e.g., a description of symptoms) as input.
2.  It calls the `hybrid_retrieve` function from the retrieval module to fetch the
    most relevant context from the indexed knowledge base.
3.  It constructs a detailed prompt that includes the user's report, the retrieved
    context, and a strict JSON schema for the desired output.
4.  It sends this prompt to a powerful language model (e.g., GPT-4o-mini) via the
    OpenAI API.
5.  Finally, it parses the model's structured JSON response and returns it.
"""

# --- Core Python Libraries ---
import os
import json
from typing import List, Dict

# --- Environment and Configuration ---
# Loads environment variables from a .env file to manage configuration settings
# like API keys and model names securely.
from dotenv import load_dotenv
load_dotenv()

# --- Third-Party and Local Imports ---
# The OpenAI library provides a convenient client for interacting with the API.
from openai import OpenAI
# This imports the core retrieval logic developed in the previous step.
from src.retrieve import hybrid_retrieve

# --- Configuration Settings ---
# These parameters, loaded from environment variables, define the behavior of
# the generation step.
PROMPT_PATH = os.environ.get("PROMPT_PATH", "/workspace/prompts/psych_guardrail.txt")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- Output Schema Definition ---
# This dictionary defines the exact structure and data types for the JSON output
# that the language model is required to produce. This ensures that the output is
# consistent, predictable, and easily parsable by other applications.
SCHEMA = {
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


def load_system_prompt(path: str) -> str:
    """
    Loads the system prompt from a specified text file.

    The system prompt provides high-level instructions to the language model,
    guiding its persona, tone, and overall behavior for the task.

    Args:
        path: The file path to the system prompt.

    Returns:
        The content of the file as a string.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_context(retrieved: List[Dict]) -> str:
    """
    Formats the list of retrieved document chunks into a single, readable string.

    This function prepares the context to be inserted into the main prompt. Each
    chunk is clearly marked with its source page number, which helps the model
    generate accurate citations.

    Args:
        retrieved: A list of document dictionaries returned by the retrieval function.

    Returns:
        A formatted string containing all the retrieved text.
    """
    lines = []
    for r in retrieved:
        page = r.get("metadata", {}).get("page_number")
        lines.append(f"[Page {page}] {r['text']}")
    return "\n\n".join(lines)


def answer(user_report: str) -> Dict:
    """
    Orchestrates the full RAG process to generate a structured answer.

    This function ties everything together: it retrieves relevant documents,
    constructs a comprehensive prompt, queries the OpenAI model, and parses
    the final JSON response.

    Args:
        user_report: The user's input query (e.g., symptom description).

    Returns:
        A dictionary containing the structured analysis from the language model,
        adhering to the defined SCHEMA.
    """
    # Initialize the OpenAI API client.
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Step 1: Load the guiding system prompt.
    system_prompt = load_system_prompt(PROMPT_PATH)
    
    # Step 2: Retrieve relevant context based on the user's report.
    retrieved = hybrid_retrieve(user_report, k=8)
    context = format_context(retrieved)

    # Step 3: Construct the final user prompt with all necessary information.
    schema_str = json.dumps(SCHEMA, indent=2)
    user_prompt = (
        f"User symptoms/report:\n{user_report}\n\n"
        f"Retrieved textbook excerpts (cite pages):\n{context}\n\n"
        f"Output strict JSON exactly in this schema (keys and types):\n{schema_str}"
    )

    # Step 4: Call the OpenAI Chat Completions API.
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,  # Lower temperature for more deterministic, factual output.
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},  # Enforce JSON output.
    )
    content = resp.choices[0].message.content
    
    # Step 5: Parse the response, with a fallback for malformed JSON.
    try:
        data = json.loads(content)
    except Exception:
        # If the model fails to produce valid JSON, return the raw string.
        data = {"raw": content}
    return data


if __name__ == "__main__":
    # This block serves as a simple demonstration of the script's functionality.
    # It defines a sample query and prints the resulting structured JSON answer.
    
    demo_query = "low mood most days, loss of interest, fatigue, sleep difficulty for 6 weeks"
    print(f"--- Running Generation Demo for Query: '{demo_query}' ---")
    
    # Call the main answer function and print the formatted output.
    final_answer = answer(demo_query)
    print(json.dumps(final_answer, indent=2))
