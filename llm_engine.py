import os
from typing import Any, Dict

from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Please add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)


def generate_sustainability_answer(question: str, kpi_context: Dict[str, Any]) -> str:
    """
    Calls the LLM (Groq) to generate a professional English answer
    based strictly on the provided context.
    """

    system_prompt = """
You are a senior sustainability reporting consultant helping to prepare
corporate sustainability reports aligned with GRI standards.

You ALWAYS:
- Use ONLY the KPI data provided in the context.
- Never invent or guess numbers.
- Provide concise, professional English suitable for ESG reports.
- Highlight changes, trends, and performance insights neutrally.
"""

    context_text = (
        "Structured KPI context (do NOT change numbers):\n"
        f"{kpi_context}\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"KPI context:\n{context_text}\n"
                f"User question:\n{question}\n\n"
                "Write a structured, professional answer using ONLY the provided data."
            ),
        },
    ]

    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=800,
    )

    return completion.choices[0].message.content.strip()
