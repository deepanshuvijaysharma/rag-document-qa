"""LLM Provider Abstraction Service Interface."""

from typing import AsyncGenerator, List, Dict, Any


class LLMService:
    """Provider-agnostic interface for streaming answer generation."""

    def __init__(self, provider: str = "openai") -> None:
        """Initialize LLMService with provider selection."""
        self.provider = provider

    async def generate_answer_stream(
        self, prompt: str, context_chunks: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """Stream generated answer tokens grounded in retrieved context.
        
        To be implemented in Phase 3.
        """
        raise NotImplementedError("LLM generation stream will be implemented in Phase 3.")
        yield ""  # For type checker compliance
