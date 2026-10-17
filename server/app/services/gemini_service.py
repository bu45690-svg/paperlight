"""
Gemini AI service.

Wraps Google Gemini 2.5 Flash for:
  1. Structured full-paper analysis (summary, contributions, methodology, etc.)
  2. RAG-grounded question answering with citations + confidence scores
  3. Study material generation (exam notes, flashcards, MCQs, etc.)

All prompts instruct the model to return strict JSON so responses can be parsed
reliably. A hard timeout guards every call so the API can never hang indefinitely.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from google import genai
from google.genai import types as genai_types

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


class GeminiError(Exception):
    pass


def _get_client() -> genai.Client:
    global _client
    if not settings.GEMINI_API_KEY:
        raise GeminiError(
            "GEMINI_API_KEY is not set. Add it to your .env file to enable AI features."
        )
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _extract_json(raw_text: str) -> Dict[str, Any]:
    """Gemini sometimes wraps JSON in markdown fences — strip them before parsing."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to locate the outermost {...} block.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise GeminiError("Gemini returned a response that could not be parsed as JSON.")


def _call_gemini_json(prompt: str) -> Dict[str, Any]:
    """Call Gemini with a request-timeout guard and parse the JSON response."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
                http_options=genai_types.HttpOptions(timeout=settings.GEMINI_TIMEOUT_SECONDS * 1000),
            ),
        )
    except Exception as exc:
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    if not response.candidates:
        raise GeminiError("Gemini returned no candidates (likely blocked by safety filters).")

    if not response.text:
        raise GeminiError("Gemini returned an empty response (possibly blocked by safety filters).")

    return _extract_json(response.text)


# --------------------------------------------------------------------------
# 1. Full paper analysis
# --------------------------------------------------------------------------

ANALYSIS_PROMPT_TEMPLATE = """You are an expert research paper analyst. Read the paper text below \
(it may be truncated to fit context) and produce a structured analysis.

Return ONLY valid JSON matching exactly this schema, no extra commentary:
{{
  "title": "string - the paper's title",
  "executive_summary": "string - 3-5 sentence high level summary for a busy reader",
  "abstract_summary": "string - concise rewrite of the abstract in plain language",
  "key_contributions": ["string", "..."],
  "methodology": "string - description of methods/approach used",
  "results": "string - description of key results/findings",
  "limitations": "string - limitations acknowledged or implied",
  "future_work": "string - suggested or stated future research directions",
  "keywords": ["string", "..."],
  "important_equations": ["string - short LaTeX-ish or plain description of each key equation, if any"],
  "important_figures": ["string - figure title/caption only, if figures are referenced in text"]
}}

If a field cannot be determined from the text, use an empty string or empty list rather than \
omitting the field.

PAPER TEXT:
---
{paper_text}
---
"""


def analyze_paper(paper_text: str) -> Dict[str, Any]:
    """Run full structured analysis on a paper's extracted text."""
    truncated = paper_text[:60000]  # keep prompt within a safe context budget
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(paper_text=truncated)
    result = _call_gemini_json(prompt)

    defaults = {
        "title": "",
        "executive_summary": "",
        "abstract_summary": "",
        "key_contributions": [],
        "methodology": "",
        "results": "",
        "limitations": "",
        "future_work": "",
        "keywords": [],
        "important_equations": [],
        "important_figures": [],
    }
    defaults.update(result)
    return defaults


# --------------------------------------------------------------------------
# 2. RAG question answering
# --------------------------------------------------------------------------

RAG_PROMPT_TEMPLATE = """You are a research assistant answering questions strictly using the \
provided excerpts from a single research paper. Do NOT use outside knowledge. If the excerpts \
do not contain enough information to answer, say so explicitly in the answer field.

Return ONLY valid JSON matching exactly this schema:
{{
  "answer": "string - the answer, grounded only in the excerpts below",
  "page_numbers": [int, "..."],
  "citations": ["string - short verbatim-ish snippet (under 20 words) from the excerpt that supports the answer"],
  "confidence_score": 0.0
}}

confidence_score must be a float between 0 and 1 reflecting how well the excerpts support the answer \
(1.0 = fully supported and unambiguous, 0.0 = excerpts are irrelevant).

QUESTION: {question}

EXCERPTS (each tagged with its source page number):
---
{excerpts}
---
"""


def answer_question(question: str, excerpts: List[tuple[str, int]]) -> Dict[str, Any]:
    """excerpts: list of (chunk_text, page_number) tuples retrieved from the vector store."""
    if not excerpts:
        return {
            "answer": "I couldn't find relevant content in this paper to answer that question.",
            "page_numbers": [],
            "citations": [],
            "confidence_score": 0.0,
        }

    excerpt_block = "\n\n".join(f"[Page {page}]: {text}" for text, page in excerpts)
    prompt = RAG_PROMPT_TEMPLATE.format(question=question, excerpts=excerpt_block[:40000])
    result = _call_gemini_json(prompt)

    defaults = {"answer": "", "page_numbers": [], "citations": [], "confidence_score": 0.0}
    defaults.update(result)
    try:
        defaults["confidence_score"] = float(defaults["confidence_score"])
    except (TypeError, ValueError):
        defaults["confidence_score"] = 0.0
    return defaults


# --------------------------------------------------------------------------
# 3. Study notes generation
# --------------------------------------------------------------------------

NOTES_PROMPT_TEMPLATE = """You are an expert educator creating study materials from the research \
paper text below. Return ONLY valid JSON matching exactly this schema:
{{
  "exam_notes": ["string - a concise, exam-ready note/point", "..."],
  "flashcards": [{{"question": "string", "answer": "string"}}, "..."],
  "bullet_notes": ["string - short bullet summarizing one key idea", "..."],
  "interview_questions": ["string - a job-interview-style question about this paper's topic", "..."],
  "viva_questions": ["string - a viva/oral-exam style question probing deep understanding", "..."],
  "mcqs": [
    {{"question": "string", "options": ["A", "B", "C", "D"], "correct_answer_index": 0, "explanation": "string"}}
  ]
}}

Produce at least 8 exam_notes, 8 flashcards, 8 bullet_notes, 6 interview_questions, 6 viva_questions, \
and EXACTLY 10 mcqs.

PAPER TEXT:
---
{paper_text}
---
"""


def generate_study_notes(paper_text: str) -> Dict[str, Any]:
    truncated = paper_text[:60000]
    prompt = NOTES_PROMPT_TEMPLATE.format(paper_text=truncated)
    result = _call_gemini_json(prompt)

    defaults = {
        "exam_notes": [],
        "flashcards": [],
        "bullet_notes": [],
        "interview_questions": [],
        "viva_questions": [],
        "mcqs": [],
    }
    defaults.update(result)
    return defaults
