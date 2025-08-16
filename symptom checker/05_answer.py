import os
import json
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from src.retrieve import hybrid_retrieve  # fixed import

PROMPT_PATH = os.environ.get("PROMPT_PATH", "/workspace/prompts/psych_guardrail.txt")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

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
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_context(retrieved: List[Dict]) -> str:
    lines = []
    for r in retrieved:
        page = r.get("metadata", {}).get("page_number")
        lines.append(f"[Page {page}] {r['text']}")
    return "\n\n".join(lines)


def answer(user_report: str) -> Dict:
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = load_system_prompt(PROMPT_PATH)
    retrieved = hybrid_retrieve(user_report, k=8)
    context = format_context(retrieved)

    schema_str = json.dumps(SCHEMA, indent=2)
    user_prompt = (
        f"User symptoms/report:\n{user_report}\n\nRetrieved textbook excerpts (cite pages):\n{context}\n\n"
        f"Output strict JSON exactly in this schema (keys and types):\n{schema_str}"
    )

    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        data = {"raw": content}
    return data


if __name__ == "__main__":
    demo = "low mood most days, loss of interest, fatigue, sleep difficulty for 6 weeks"
    print(json.dumps(answer(demo), indent=2))