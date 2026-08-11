"""RAG Chat API Endpoints with Streaming & SSE Support."""

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.core.exceptions import InvalidFileError

logger = logging.getLogger("rag_app.api.chat")

router = APIRouter()


def get_chat_service() -> ChatService:
    """Dependency provider for ChatService instance."""
    return ChatService()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG Question Answering Endpoint (Non-Streaming)",
    description="Processes user question through RAG pipeline and returns grounded response."
)
async def chat_endpoint(
    payload: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Endpoint executing complete grounded RAG Q&A pipeline (non-streaming)."""
    if not payload.message or not payload.message.strip():
        raise InvalidFileError("Message question cannot be empty.")

    return await chat_service.answer_question(
        message=payload.message,
        document_id=payload.document_id,
        conversation_id=payload.conversation_id
    )


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="RAG Question Answering Endpoint (Streaming SSE)",
    description="Processes user question through RAG pipeline and streams answer tokens progressively via Server-Sent Events (SSE)."
)
async def chat_stream_endpoint(
    payload: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    """Endpoint streaming grounded RAG Q&A tokens via SSE (text/event-stream)."""
    if not payload.message or not payload.message.strip():
        raise InvalidFileError("Message question cannot be empty.")

    return StreamingResponse(
        chat_service.answer_question_stream(
            message=payload.message,
            document_id=payload.document_id,
            conversation_id=payload.conversation_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
