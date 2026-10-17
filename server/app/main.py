"""
AI Research Paper Summarizer — FastAPI application entrypoint.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Database initialized. %s starting in %s mode.", settings.APP_NAME, settings.ENVIRONMENT)
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set — AI features will return errors until configured.")
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    description="Upload research papers, get automatic AI analysis, chat with your papers via RAG, "
    "and generate study materials — all backed by Gemini 2.5 Flash.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
