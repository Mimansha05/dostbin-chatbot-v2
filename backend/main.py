import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import (
    ALLOWED_ORIGINS,
    MAX_QUESTION_LENGTH,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    groq_configured,
    validate_startup,
)
from backend.llm import (
    LLMConfigurationError,
    LLMGenerationError,
    LLMRateLimitError,
    LLMTimeoutError,
    generate_answer,
)
from backend.rate_limit import InMemoryRateLimiter
from backend.retriever import DEFAULT_TOP_K, search_faqs


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("dostbin")

MIN_CONTEXT_RANKING_SCORE = 0.4
MIN_CONTEXT_LEXICAL_SCORE = 0.15
MIN_CONTEXT_SEMANTIC_SCORE = 0.45
NO_CONTEXT_ANSWER = (
    "The current DOSTBin knowledge base does not contain enough information "
    "to answer that. Please contact DOSTBin support."
)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    status = validate_startup()
    logger.info(
        "DOSTBin API started. Groq configured=%s model=%s",
        status["groq_configured"],
        status["model"],
    )
    yield


app = FastAPI(
    title="DOSTBin Chatbot API",
    description="RAG chatbot backend for DOSTBin, powered by Groq.",
    version="2.0.0",
    lifespan=lifespan,
)
rate_limiter = InMemoryRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LENGTH)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_QUESTION_LENGTH)


def is_grounded_source(result):
    ranking_score = result.get("ranking_score", result.get("similarity_score", 0.0))
    lexical_score = result.get("lexical_score", 0.0)
    similarity_score = result.get("similarity_score", 0.0)

    has_enough_signal = ranking_score >= MIN_CONTEXT_RANKING_SCORE
    has_specific_match = (
        lexical_score >= MIN_CONTEXT_LEXICAL_SCORE
        or similarity_score >= MIN_CONTEXT_SEMANTIC_SCORE
    )

    return has_enough_signal and has_specific_match


def client_key(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request):
    allowed, retry_after = rate_limiter.allow(client_key(request))
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait and try again.",
            headers={"Retry-After": str(retry_after)},
        )


def retrieve_grounded_results(question):
    try:
        results = search_faqs(question, top_k=DEFAULT_TOP_K)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.error("Retrieval failed: %s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Retrieval failed.") from error

    return [result for result in results if is_grounded_source(result)]


def source_payload(grounded_results):
    return [
        {
            "id": result.get("id"),
            "question": result.get("question"),
            "score": result.get("similarity_score"),
        }
        for result in grounded_results
    ]


def generate_grounded_answer(question, grounded_results):
    if not grounded_results:
        return NO_CONTEXT_ANSWER

    try:
        return generate_answer(question, grounded_results)
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except LLMRateLimitError as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except LLMGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/health")
def health():
    return {
        "status": "ok",
        "groq_configured": groq_configured(),
        "frontend": FRONTEND_DIR.exists(),
    }


@app.get("/")
def demo_page():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse({"status": "ok", "docs": "/docs"})
    return FileResponse(index_file)


@app.get("/embed")
def embed_page():
    embed_file = FRONTEND_DIR / "embed.html"
    if not embed_file.exists():
        raise HTTPException(status_code=404, detail="Embed UI is not available.")
    return FileResponse(embed_file)


@app.post("/ask")
def ask(request_body: AskRequest, request: Request):
    enforce_rate_limit(request)
    question = request_body.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    grounded_results = retrieve_grounded_results(question)
    answer = generate_grounded_answer(question, grounded_results)

    return {
        "question": question,
        "answer": answer,
        "sources": source_payload(grounded_results),
    }


@app.post("/api/chat")
def chat(request_body: ChatRequest, request: Request):
    enforce_rate_limit(request)
    message = request_body.message.strip()

    if not message:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Message cannot be empty."},
        )

    try:
        grounded_results = retrieve_grounded_results(message)
        response_text = generate_grounded_answer(message, grounded_results)
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"success": False, "error": error.detail},
            headers=dict(error.headers or {}),
        )

    return {
        "success": True,
        "response": response_text,
        "sources": source_payload(grounded_results),
    }
