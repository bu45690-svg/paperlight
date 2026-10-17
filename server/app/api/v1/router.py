from fastapi import APIRouter

from app.api.v1 import chat, dashboard, export, notes, papers, search

api_router = APIRouter()
api_router.include_router(papers.router)
api_router.include_router(chat.router)
api_router.include_router(notes.router)
api_router.include_router(search.router)
api_router.include_router(dashboard.router)
api_router.include_router(export.router)
