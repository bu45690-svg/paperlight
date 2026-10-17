from pathlib import Path

import pytest

from app.services import gemini_service, pdf_service, vector_store

SAMPLES = Path(__file__).resolve().parent.parent / "storage" / "samples"


def test_pdf_extraction_on_real_samples():
    for pdf in SAMPLES.glob("*.pdf"):
        doc = pdf_service.extract_text(pdf)
        assert doc.total_pages > 0 and doc.char_count > 500, pdf.name


def test_faiss_roundtrip_and_ranking():
    pages = [
        pdf_service.PageText(1, "Transformers use self attention over token sequences."),
        pdf_service.PageText(2, "Federated learning trains models across hospitals without sharing data."),
    ]
    vector_store.build_index("unit-test-paper", pages)
    try:
        top, _ = vector_store.search_index("unit-test-paper", "federated hospitals learning", top_k=1)[0]
        assert top.page_number == 2
    finally:
        vector_store.delete_index("unit-test-paper")
    assert vector_store.search_index("unit-test-paper", "x") == []


def test_build_index_rejects_empty_text():
    with pytest.raises(ValueError):
        vector_store.build_index("empty-paper", [pdf_service.PageText(1, "   ")])


@pytest.mark.parametrize(
    "raw",
    ['{"a": 1}', '```json\n{"a": 1}\n```', 'Sure! Here you go: {"a": 1} hope it helps'],
)
def test_extract_json_variants(raw):
    assert gemini_service._extract_json(raw) == {"a": 1}


def test_extract_json_garbage_raises():
    with pytest.raises(gemini_service.GeminiError):
        gemini_service._extract_json("no json here")


def test_missing_api_key_raises(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(gemini_service, "_client", None)
    with pytest.raises(gemini_service.GeminiError):
        gemini_service._get_client()
