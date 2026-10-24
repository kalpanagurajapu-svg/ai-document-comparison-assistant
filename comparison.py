
import json
import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


def compare_documents(text_a, text_b):
    """Summarize and compare two PDF documents using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. "
            "Add GEMINI_API_KEY to your .env file."
        )

    if not text_a.strip() or not text_b.strip():
        raise ValueError(
            "Both documents must contain readable text."
        )

    # Keep input size within a practical initial limit.
    max_chars = 40000

    if len(text_a) + len(text_b) > max_chars:
        raise ValueError(
            "The documents are too long for this version. "
            "Please use shorter PDFs (40,000 combined characters maximum)."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an AI Document Comparison Assistant.

Use ONLY the text supplied below as evidence.
Never invent facts. Keep the two documents separate.
If information is missing, say:
"Not found in the provided text."

Return ONLY valid JSON with these exact keys:
{{
  "summary_a": "Summary of Document A",
  "summary_b": "Summary of Document B",
  "similarities": ["Shared point with evidence"],
  "differences": [
    {{
      "topic": "Topic",
      "document_a": "Fact from A or Not found in the provided text",
      "document_b": "Fact from B or Not found in the provided text",
      "change_type": "Added, Removed, Changed, or Conflict",
      "evidence_a": "Short supporting excerpt from A",
      "evidence_b": "Short supporting excerpt from B"
    }}
  ],
  "key_details": [
    {{
      "detail": "Date, name, amount, deadline, or requirement",
      "document_a": "Value in A or Not found in the provided text",
      "document_b": "Value in B or Not found in the provided text"
    }}
  ],
  "conclusion": "Neutral summary of the main changes",
  "limitations": ["Uncertainty or limitation, if any"]
}}

Report only meaningful differences supported by the text.
Do not treat missing information as proof of a contradiction.
Use short evidence excerpts when possible.
If the documents are mostly identical, say so.

DOCUMENT A:
{text_a}

DOCUMENT B:
{text_b}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )

        if not response.text:
            raise ValueError("The AI returned an empty response.")

        result = json.loads(response.text)

        required_keys = {
            "summary_a",
            "summary_b",
            "similarities",
            "differences",
            "key_details",
            "conclusion",
            "limitations",
        }

        if not isinstance(result, dict):
            raise ValueError("The AI response has an invalid format.")

        if not required_keys.issubset(result.keys()):
            raise ValueError("The AI response is missing required sections.")

        for key in ("summary_a", "summary_b", "conclusion"):
            if not isinstance(result[key], str):
                raise ValueError("The AI returned an invalid text section.")

        for key in ("similarities", "differences", "key_details", "limitations"):
            if not isinstance(result[key], list):
                raise ValueError("The AI returned an invalid list section.")

        return result

    
    except ValueError:
        raise
    except Exception as error:
        raise RuntimeError(
            f"AI Error: {type(error).__name__}: {error}"
        ) from error
