"""Complete RAG Q&A Orchestration Service with Streaming Support."""

import json
import uuid
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService
from app.db.conversation_store import ConversationStore
from app.schemas.chat import SourceCitation, ChatResponse

logger = logging.getLogger("rag_app.chat_service")

# Minimum similarity score threshold for considering context relevant
MIN_RELEVANCE_THRESHOLD = 0.35
FALLBACK_GROUNDED_ANSWER = "I am unable to find the answer in the uploaded documents."


class ChatService:
    """Service orchestrating RAG Q&A: query validation, vector retrieval, prompt building, LLM generation, streaming, and citations."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMService] = None,
        conversation_store: Optional[ConversationStore] = None
    ) -> None:
        """Initialize ChatService with dependency injection."""
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_service = llm_service or LLMService()
        self.conversation_store = conversation_store or ConversationStore()

    def format_context_block(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieved chunk results into a structured context string for prompt injection defense."""
        if not results:
            return "No relevant context found in uploaded documents."

        context_parts: List[str] = []
        for idx, res in enumerate(results):
            filename = res.get("filename") or res.get("source_filename", "Document")
            page_num = res.get("page_number", "N/A")
            chunk_id = res.get("chunk_id", "unknown")
            header = (
                f"--- RETRIEVED CHUNK #{idx + 1} "
                f"(Source: {filename}, Page: {page_num}, ChunkID: {chunk_id}) ---"
            )
            text_body = res.get("text", "").strip()
            context_parts.append(f"{header}\n{text_body}\n")

        return "\n".join(context_parts)

    def extract_sources(self, results: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Extract unique source citations with optional snippet text from retrieved context chunks."""
        sources: List[SourceCitation] = []
        seen_chunks = set()

        for res in results:
            chunk_id = res.get("chunk_id")
            if not chunk_id or chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            snippet_text = res.get("text", "").strip()
            if len(snippet_text) > 250:
                snippet_text = snippet_text[:247] + "..."

            sources.append(
                SourceCitation(
                    document_id=res.get("document_id", "unknown"),
                    filename=res.get("filename") or res.get("source_filename", "Document"),
                    page_number=res.get("page_number"),
                    chunk_id=chunk_id,
                    relevance_score=float(res.get("score", 0.0)),
                    snippet=snippet_text or None
                )
            )

        return sources

    async def answer_question(
        self,
        message: str,
        document_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """Process natural language question through complete RAG pipeline (non-streaming)."""
        if not message or not message.strip():
            logger.warning("Chat request rejected: empty message.")
            raise ValueError("Message question cannot be empty or whitespace-only.")

        clean_message = message.strip()
        session_id = conversation_id.strip() if conversation_id and conversation_id.strip() else str(uuid.uuid4())

        # 1. Retrieve top-K relevant chunks from vector store
        retrieval_data = self.retrieval_service.search(
            query=clean_message,
            top_k=4,
            document_id=document_id
        )

        retrieved_results = retrieval_data.get("results", [])

        # 2. Grounded relevance evaluation: check if any chunk meets relevance threshold
        is_relevant = False
        if retrieved_results:
            top_score = retrieved_results[0].get("score", 0.0)
            if top_score >= MIN_RELEVANCE_THRESHOLD:
                is_relevant = True

        if not is_relevant:
            logger.info(f"Insufficient context for query '{clean_message}'. Returning grounded fallback answer.")
            answer = FALLBACK_GROUNDED_ANSWER
            sources: List[SourceCitation] = []

            # Save chat turn in conversation history
            self.conversation_store.append_turns(
                conversation_id=session_id,
                user_message=clean_message,
                assistant_message=answer
            )

            return ChatResponse(
                conversation_id=session_id,
                answer=answer,
                sources=sources
            )

        # 3. Format retrieved context block
        context_block = self.format_context_block(retrieved_results)

        # 4. Extract source citations from retrieved chunks
        sources = self.extract_sources(retrieved_results)

        # 5. Fetch recent conversation history turns
        history = self.conversation_store.get_history(session_id, max_messages=6)

        # 6. Generate grounded answer via provider-agnostic LLM service
        answer = await self.llm_service.generate_answer(
            question=clean_message,
            context=context_block,
            conversation_history=history
        )

        # 7. Persist session history turn
        self.conversation_store.append_turns(
            conversation_id=session_id,
            user_message=clean_message,
            assistant_message=answer
        )

        logger.info(
            f"Successfully generated grounded answer for conversation '{session_id}' "
            f"with {len(sources)} source citations."
        )

        return ChatResponse(
            conversation_id=session_id,
            answer=answer,
            sources=sources
        )

    async def answer_question_stream(
        self,
        message: str,
        document_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream RAG Q&A response token-by-token using Server-Sent Events (SSE)."""
        if not message or not message.strip():
            err_data = json.dumps({"detail": "Message question cannot be empty."})
            yield f"event: error\ndata: {err_data}\n\n"
            return

        clean_message = message.strip()
        session_id = conversation_id.strip() if conversation_id and conversation_id.strip() else str(uuid.uuid4())

        try:
            # 1. Vector retrieval
            retrieval_data = self.retrieval_service.search(
                query=clean_message,
                top_k=4,
                document_id=document_id
            )
            retrieved_results = retrieval_data.get("results", [])

            # 2. Grounded relevance evaluation
            is_relevant = False
            if retrieved_results:
                top_score = retrieved_results[0].get("score", 0.0)
                if top_score >= MIN_RELEVANCE_THRESHOLD:
                    is_relevant = True

            if not is_relevant:
                # Stream fallback answer and empty sources
                meta_data = json.dumps({
                    "conversation_id": session_id,
                    "sources": []
                })
                yield f"event: metadata\ndata: {meta_data}\n\n"

                token_data = json.dumps({"token": FALLBACK_GROUNDED_ANSWER})
                yield f"event: token\ndata: {token_data}\n\n"

                # Persist turn
                self.conversation_store.append_turns(
                    conversation_id=session_id,
                    user_message=clean_message,
                    assistant_message=FALLBACK_GROUNDED_ANSWER
                )

                done_data = json.dumps({"status": "complete"})
                yield f"event: done\ndata: {done_data}\n\n"
                return

            # 3. Format context & sources
            context_block = self.format_context_block(retrieved_results)
            sources = self.extract_sources(retrieved_results)

            # Yield metadata event containing sources & conversation_id
            meta_payload = json.dumps({
                "conversation_id": session_id,
                "sources": [s.model_dump() for s in sources]
            })
            yield f"event: metadata\ndata: {meta_payload}\n\n"

            # 4. Fetch history & generate streaming tokens
            history = self.conversation_store.get_history(session_id, max_messages=6)
            full_answer_chunks: List[str] = []

            async for token in self.llm_service.generate_answer_stream(
                question=clean_message,
                context=context_block,
                conversation_history=history
            ):
                full_answer_chunks.append(token)
                tok_data = json.dumps({"token": token})
                yield f"event: token\ndata: {tok_data}\n\n"

            # 5. Complete stream and persist full answer
            complete_answer = "".join(full_answer_chunks)
            self.conversation_store.append_turns(
                conversation_id=session_id,
                user_message=clean_message,
                assistant_message=complete_answer
            )

            done_data = json.dumps({"status": "complete"})
            yield f"event: done\ndata: {done_data}\n\n"

        except Exception as err:
            logger.error(f"Error in streaming chat Q&A: {err}")
            err_payload = json.dumps({"detail": str(err)})
            yield f"event: error\ndata: {err_payload}\n\n"
