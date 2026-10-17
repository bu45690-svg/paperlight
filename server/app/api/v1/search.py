"""
Semantic search across all uploaded papers (and optionally scoped to one paper).
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.paper import Paper, PaperStatus
from app.schemas.misc import SearchQuery, SearchResponse, SearchResultItem
from app.services import vector_store

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_papers(payload: SearchQuery, db: Session = Depends(get_db)):
    ready_papers = db.query(Paper).filter(Paper.status == PaperStatus.READY).all()
    paper_ids = [p.id for p in ready_papers]
    id_to_paper = {p.id: p for p in ready_papers}

    results = await asyncio.to_thread(
        vector_store.search_all_papers, paper_ids, payload.query, payload.top_k
    )

    items = [
        SearchResultItem(
            paper_id=pid,
            paper_title=id_to_paper[pid].title or id_to_paper[pid].original_filename,
            page_number=chunk.page_number,
            snippet=chunk.text[:400],
            score=round(score, 4),
        )
        for pid, chunk, score in results
    ]
    return SearchResponse(query=payload.query, results=items)


@router.post("/{paper_id}", response_model=SearchResponse)
async def search_within_paper(paper_id: str, payload: SearchQuery, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    title = paper.title if paper and paper.title else (paper.original_filename if paper else None)

    results = await asyncio.to_thread(vector_store.search_index, paper_id, payload.query, payload.top_k)
    items = [
        SearchResultItem(paper_id=paper_id, paper_title=title, page_number=chunk.page_number, snippet=chunk.text[:400], score=round(score, 4))
        for chunk, score in results
    ]
    return SearchResponse(query=payload.query, results=items)
