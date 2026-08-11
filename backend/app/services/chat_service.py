"""Complete RAG Q&A Orchestration Service."""

import uuid
import logging
from typing import List, Dict, Any, Optional

from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService
from app.db.conversation_store import ConversationStore
from app.schemas.chat import SourceCitation, ChatResponse

logger = logging.getLogger("rag_app.chat_service")

# Minimum similarity score threshold for considering context relevant
MIN_RELEVANCE_THRESHOLD = 0.35
FALLBACK_GROUNDED_ANSWER = "I am unable to find the answer in the uploaded documents."


class ChatService:
    """Service orchestrating RAG Q&A: query validation, vector retrieval, prompt building, LLM generation, and citations."""

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
            header = (
                f"--- RETRIEVED CHUNK #{idx + 1} "
                f"(Source: {res['filename']}, Page: {res['page_number']}, ChunkID: {res['chunk_id']}) ---"
            )
            text_body = res["text"].strip()
            context_parts.append(f"{header}\n{text_body}\n")

        return "\n".join(context_parts)

    def extract_sources(self, results: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Extract unique source citations from retrieved context chunks."""
        sources: List[SourceCitation] = []
        seen_chunks = set()

        for res in results:
            chunk_id = res["chunk_id"]
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            sources.append(
                SourceCitation(
                    document_id=res["document_id"],
                    filename=res["filename"],
                    page_number=res["page_number"],
                    chunk_id=chunk_id,
                    relevance_score=res["score"]
                )
            )

        return sources

    async def answer_question(
        self,
        message: str,
        document_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """Process natural language question through complete RAG pipeline.
        
        Args:
            message: User question string
            document_id: Optional document UUID filter
            conversation_id: Optional session identifier string
            
        Returns:
            ChatResponse containing conversation_id, grounded answer, and source citations.
        """
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
