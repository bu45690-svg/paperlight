"""
Vector store service.

Chunks page text with LangChain's RecursiveCharacterTextSplitter, embeds chunks using
a sentence-transformers-compatible MiniLM model (served via `fastembed`'s ONNX runtime
backend — same model family/quality as `sentence-transformers`, but without pulling in
a multi-gigabyte PyTorch+CUDA dependency chain), and stores/retrieves them with a
per-paper FAISS index on disk.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List

import faiss
import numpy as np
from fastembed import TextEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.pdf_service import PageText

_model: TextEmbedding | None = None

# fastembed's naming for the standard MiniLM-L6-v2 sentence-transformers model.
_FASTEMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedding_model() -> TextEmbedding:
    """Lazily load (and cache) the embedding model — loaded once per process."""
    global _model
    if _model is None:
        kwargs = {"cache_dir": settings.FASTEMBED_CACHE_DIR} if settings.FASTEMBED_CACHE_DIR else {}
        _model = TextEmbedding(model_name=_FASTEMBED_MODEL_NAME, **kwargs)
    return _model


def _embed(texts: List[str]) -> np.ndarray:
    """Embed a list of texts and L2-normalize so inner product == cosine similarity."""
    model = get_embedding_model()
    vectors = np.array(list(model.embed(texts)), dtype="float32")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


@dataclass
class Chunk:
    text: str
    page_number: int
    chunk_index: int


def chunk_pages(pages: List[PageText]) -> List[Chunk]:
    """Split each page's text into overlapping chunks, tracking source page numbers."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: List[Chunk] = []
    idx = 0
    for page in pages:
        if not page.text or not page.text.strip():
            continue
        for piece in splitter.split_text(page.text):
            if piece.strip():
                chunks.append(Chunk(text=piece, page_number=page.page_number, chunk_index=idx))
                idx += 1
    return chunks


def _index_paths(paper_id: str) -> tuple[Path, Path]:
    base = settings.FAISS_INDEX_DIR / paper_id
    return base.with_suffix(".index"), base.with_suffix(".meta.pkl")


def build_index(paper_id: str, pages: List[PageText]) -> str:
    """Build and persist a FAISS index for a paper's chunked text. Returns the index base path."""
    chunks = chunk_pages(pages)
    if not chunks:
        raise ValueError("No extractable text found in this PDF (it may be scanned/image-only).")

    embeddings = _embed([c.text for c in chunks])

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors == cosine similarity
    index.add(embeddings)

    index_path, meta_path = _index_paths(paper_id)
    # Serialize via bytes + pathlib instead of faiss.write_index(str(path)): faiss's C++ file
    # I/O is fragile with non-ASCII / OneDrive Windows paths. The on-disk format is identical.
    index_path.write_bytes(faiss.serialize_index(index).tobytes())
    with open(meta_path, "wb") as f:
        pickle.dump(chunks, f)

    return str(settings.FAISS_INDEX_DIR / paper_id)


def search_index(paper_id: str, query: str, top_k: int | None = None) -> List[tuple[Chunk, float]]:
    """Return the top-k most relevant chunks for a query within a single paper's index."""
    top_k = top_k or settings.RETRIEVAL_TOP_K
    index_path, meta_path = _index_paths(paper_id)
    if not index_path.exists() or not meta_path.exists():
        return []

    index = faiss.deserialize_index(np.frombuffer(index_path.read_bytes(), dtype="uint8"))
    with open(meta_path, "rb") as f:
        chunks: List[Chunk] = pickle.load(f)

    query_vec = _embed([query])

    scores, indices = index.search(query_vec, min(top_k, len(chunks)))
    results: List[tuple[Chunk, float]] = []
    for score, i in zip(scores[0], indices[0]):
        if i == -1:
            continue
        results.append((chunks[i], float(score)))
    return results


def search_all_papers(paper_ids: List[str], query: str, top_k: int = 5) -> List[tuple[str, Chunk, float]]:
    """Semantic search across multiple papers' indexes; returns (paper_id, chunk, score) sorted by score."""
    all_results: List[tuple[str, Chunk, float]] = []
    for pid in paper_ids:
        for chunk, score in search_index(pid, query, top_k=top_k):
            all_results.append((pid, chunk, score))
    all_results.sort(key=lambda r: r[2], reverse=True)
    return all_results[:top_k]


def delete_index(paper_id: str) -> None:
    index_path, meta_path = _index_paths(paper_id)
    index_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)
