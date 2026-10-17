"""
Test setup.

Settings are pointed at a throwaway temp directory *before* the app is imported, so tests never
touch the real database, uploads, FAISS indexes, or .env secrets.

Only two external boundaries are stubbed (everything else — PDF parsing, SQLite, FAISS, routes,
PDF export — runs for real):
  * the Gemini network call (needs an API key + internet)
  * the embedding model download (fastembed fetches ONNX weights from Hugging Face)
"""
import hashlib
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

_TMP = Path(tempfile.mkdtemp(prefix="rps-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TMP / "uploads")
os.environ["FAISS_INDEX_DIR"] = str(_TMP / "faiss")
os.environ["GEMINI_API_KEY"] = "test-key-not-real"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import gemini_service, vector_store  # noqa: E402

SAMPLES = Path(__file__).resolve().parent.parent / "storage" / "samples"


def _fake_embed(texts):
    """Deterministic bag-of-words hashing embedder: similar words -> similar vectors."""
    dim = 64
    out = np.zeros((len(texts), dim), dtype="float32")
    for row, text in enumerate(texts):
        for word in text.lower().split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            out[row, h % dim] += 1.0
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return out / norms


_FAKE_JSON = {
    "title": "Stubbed Paper Title",
    "executive_summary": "Summary.",
    "abstract_summary": "Abstract.",
    "key_contributions": ["c1", "c2"],
    "methodology": "m",
    "results": "r",
    "limitations": "l",
    "future_work": "f",
    "keywords": ["k1"],
    "important_equations": [],
    "important_figures": [],
    "answer": "Stubbed answer.",
    "page_numbers": [1],
    "citations": ["snippet"],
    "confidence_score": 0.9,
    "exam_notes": ["e1"],
    "flashcards": [{"question": "q", "answer": "a"}],
    "bullet_notes": ["b1"],
    "interview_questions": ["i1"],
    "viva_questions": ["v1"],
    "mcqs": [{"question": "q", "options": ["A", "B", "C", "D"], "correct_answer_index": 0, "explanation": "x"}],
}


@pytest.fixture(autouse=True)
def stub_external(monkeypatch):
    monkeypatch.setattr(vector_store, "_embed", _fake_embed)
    monkeypatch.setattr(gemini_service, "_call_gemini_json", lambda prompt: dict(_FAKE_JSON))


@pytest.fixture()
def client():
    with TestClient(app) as c:  # context manager runs the lifespan (init_db)
        yield c


@pytest.fixture()
def sample_pdf_bytes():
    return (SAMPLES / "attention_mechanisms_survey.pdf").read_bytes()
