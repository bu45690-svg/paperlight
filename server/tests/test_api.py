import pytest

from app.models.paper import PaperStatus


def _upload(client, data, name="paper.pdf"):
    return client.post("/api/v1/papers/upload", files={"file": (name, data, "application/pdf")})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


@pytest.mark.parametrize(
    "name,data",
    [("notes.txt", b"%PDF-1.4 fake"), ("empty.pdf", b""), ("fake.pdf", b"not a pdf at all")],
)
def test_upload_rejects_invalid_files(client, name, data):
    r = _upload(client, data, name)
    assert r.status_code == 400


def test_upload_rejects_oversized(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)
    r = _upload(client, b"%PDF-1.4 " + b"x" * 100)
    assert r.status_code == 400 and "maximum" in r.json()["detail"]


def test_full_workflow(client, sample_pdf_bytes):
    # upload -> background pipeline runs (TestClient executes background tasks before returning)
    r = _upload(client, sample_pdf_bytes, "attention.pdf")
    assert r.status_code == 201
    pid = r.json()["id"]

    status = client.get(f"/api/v1/papers/{pid}/status").json()
    assert status["status"] == PaperStatus.READY.value, status

    paper = client.get(f"/api/v1/papers/{pid}").json()
    assert paper["title"] == "Stubbed Paper Title"
    assert paper["total_pages"] > 0 and paper["key_contributions"] == ["c1", "c2"]

    assert any(p["id"] == pid for p in client.get("/api/v1/papers").json())

    # RAG chat (real FAISS retrieval over the real extracted PDF text)
    ans = client.post(f"/api/v1/chat/{pid}/ask", json={"question": "What is attention?"})
    assert ans.status_code == 200 and ans.json()["answer"] == "Stubbed answer."
    assert len(client.get(f"/api/v1/chat/{pid}/history").json()) == 1
    assert client.get("/api/v1/chat/history/all").json()[0]["paper_id"] == pid
    assert client.post(f"/api/v1/chat/{pid}/ask", json={"question": "   "}).status_code == 400

    # semantic search
    hits = client.post("/api/v1/search", json={"query": "attention", "top_k": 3}).json()
    assert hits["results"] and hits["results"][0]["paper_id"] == pid
    assert client.post(f"/api/v1/search/{pid}", json={"query": "attention"}).json()["results"]

    # study notes + exports
    assert client.get(f"/api/v1/notes/{pid}").status_code == 404
    assert client.post(f"/api/v1/notes/{pid}/generate").status_code == 200
    assert client.get(f"/api/v1/notes/{pid}").json()["mcqs"][0]["correct_answer_index"] == 0
    for kind in ("summary", "study-notes", "flashcards"):
        e = client.get(f"/api/v1/export/{pid}/{kind}")
        assert e.status_code == 200 and e.content.startswith(b"%PDF"), kind

    # bonus features + dashboard
    assert client.patch(f"/api/v1/papers/{pid}/favorite", json={"is_favorite": True}).json()["is_favorite"]
    assert client.patch(f"/api/v1/papers/{pid}/progress", json={"reading_progress_percent": 250}).json()[
        "reading_progress_percent"
    ] == 100
    assert client.post(f"/api/v1/papers/{pid}/open").status_code == 200
    dash = client.get("/api/v1/dashboard").json()
    assert dash["total_papers"] >= 1 and any(p["id"] == pid for p in dash["favorite_papers"])

    # delete cleans up file + index
    from app.services.vector_store import _index_paths

    idx, meta = _index_paths(pid)
    assert idx.exists() and meta.exists()
    assert client.delete(f"/api/v1/papers/{pid}").status_code == 204
    assert not idx.exists() and not meta.exists()
    assert client.get(f"/api/v1/papers/{pid}").status_code == 404


def test_unknown_paper_404s(client):
    for method, url in [("get", "/api/v1/papers/nope"), ("get", "/api/v1/papers/nope/status"),
                        ("post", "/api/v1/chat/nope/ask"), ("post", "/api/v1/notes/nope/generate")]:
        kwargs = {"json": {"question": "x"}} if "chat" in url else {}
        assert getattr(client, method)(url, **kwargs).status_code == 404, url


def test_gemini_error_becomes_502(client, sample_pdf_bytes, monkeypatch):
    from app.services import gemini_service

    pid = _upload(client, sample_pdf_bytes).json()["id"]

    def boom(prompt):
        raise gemini_service.GeminiError("quota exceeded")

    monkeypatch.setattr(gemini_service, "_call_gemini_json", boom)
    r = client.post(f"/api/v1/chat/{pid}/ask", json={"question": "anything"})
    assert r.status_code == 502 and "quota" in r.json()["detail"]
