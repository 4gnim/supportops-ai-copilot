
import hmac
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from supportops import __version__
from supportops.config import settings
from supportops.feedback import initialize_feedback_db, save_feedback
from supportops.schemas import (
    AskRequest,
    AskResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from supportops.service import RAGService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("supportops")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize application resources when the API starts."""
    initialize_feedback_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Grounded IT-support Q&A over an indexed knowledge base, with citations, feedback, "
        "basic API-key protection, and request telemetry."
    ),
    lifespan=lifespan,
)


def get_rag_service() -> RAGService:
    return RAGService()


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    expected = settings.api_key

    if not expected or expected == "change-me-local-only":
        # Keep the development default explicit rather than implying secure auth.
        if x_api_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        return

    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.middleware("http")
async def request_telemetry(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        logger.exception(
            json.dumps(
                {
                    "event": "request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                }
            )
        )
        raise
    finally:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                }
            )
        )

    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness endpoint; intentionally does not load embedding or LLM models."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
    }


@app.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(require_api_key)],
)
def ask(
    body: AskRequest,
    request: Request,
    service: Annotated[RAGService, Depends(get_rag_service)],
) -> AskResponse:
    started = time.perf_counter()

    try:
        result = service.answer(body.query)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "RAG request failed (request_id=%s)",
            request.state.request_id,
        )
        raise HTTPException(
            status_code=500,
            detail="The knowledge retrieval request failed.",
        ) from exc

    return AskResponse(
        request_id=request.state.request_id,
        answer=result["answer"],
        sources=result["sources"],
        latency_ms=round((time.perf_counter() - started) * 1000, 2),
    )


@app.post(
    "/feedback",
    response_model=FeedbackResponse,
    dependencies=[Depends(require_api_key)],
)
def feedback(body: FeedbackRequest) -> FeedbackResponse:
    try:
        feedback_id = save_feedback(
            body.request_id,
            body.rating,
            body.comment,
        )
    except Exception as exc:
        logger.exception("Could not save user feedback")
        raise HTTPException(
            status_code=500,
            detail="Could not save feedback.",
        ) from exc

    return FeedbackResponse(
        status="saved",
        feedback_id=feedback_id,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
