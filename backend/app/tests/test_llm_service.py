"""Unit Tests for LLM Service Abstraction (Using Mocked Providers)."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.llm_service import (
    LLMService,
    OpenAIProvider,
    GroqProvider,
    AnthropicProvider,
    OllamaProvider,
    RAG_SYSTEM_PROMPT,
    _mask_key
)
from app.core.exceptions import LLMProviderError


def test_rag_system_prompt_guardrails():
    """Test RAG system prompt contains strict groundedness and prompt injection defense instructions."""
    assert "USE ONLY THE SUPPLIED CONTEXT" in RAG_SYSTEM_PROMPT
    assert "Do NOT use outside knowledge" in RAG_SYSTEM_PROMPT
    assert "I am unable to find the answer in the uploaded documents." in RAG_SYSTEM_PROMPT
    assert "PROMPT INJECTION DEFENSE" in RAG_SYSTEM_PROMPT
    assert "untrusted external data" in RAG_SYSTEM_PROMPT
    assert "Ignore previous instructions" in RAG_SYSTEM_PROMPT


def test_api_key_masking_utility():
    """Test _mask_key utility hides sensitive API keys."""
    assert _mask_key(None) == "[NOT_SET]"
    assert _mask_key("") == "[NOT_SET]"
    assert _mask_key("short") == "****"
    assert _mask_key("sk-proj-1234567890abcdef") == "sk-p...cdef"


def test_llm_service_provider_instantiation():
    """Test LLMService instantiates correct provider adapter class based on provider_name."""
    s_openai = LLMService(provider_name="openai", model_name="gpt-4o-mini", api_key="sk-testkey123")
    assert isinstance(s_openai.provider, OpenAIProvider)
    assert "sk-t...y123" in repr(s_openai)

    s_groq = LLMService(provider_name="groq", model_name="llama-3.1-8b-instant", api_key="gsk-testkey123")
    assert isinstance(s_groq.provider, GroqProvider)

    s_anthropic = LLMService(provider_name="anthropic", model_name="claude-3-haiku-20240307", api_key="sk-ant-testkey123")
    assert isinstance(s_anthropic.provider, AnthropicProvider)

    s_ollama = LLMService(provider_name="ollama", model_name="llama3", ollama_base_url="http://localhost:11434")
    assert isinstance(s_ollama.provider, OllamaProvider)


def test_llm_service_unsupported_provider():
    """Test LLMService raises ValueError for unsupported provider name."""
    with pytest.raises(ValueError) as exc:
        LLMService(provider_name="unsupported_vendor")
    assert "Unsupported LLM provider" in str(exc.value)


def test_build_user_message():
    """Test build_user_message formats context block and user question."""
    service = LLMService(provider_name="openai", api_key="sk-test")
    ctx = "[Page 1] Full-time employees accrue 20 days of paid annual leave."
    q = "What is the annual leave policy?"

    message = service.build_user_message(question=q, context=ctx)

    assert "--- RETRIEVED DOCUMENT CONTEXT START ---" in message
    assert ctx in message
    assert "--- RETRIEVED DOCUMENT CONTEXT END ---" in message
    assert "USER QUESTION: What is the annual leave policy?" in message


@pytest.mark.asyncio
async def test_openai_provider_mocked_generate_answer():
    """Test OpenAIProvider generate_answer using mocked AsyncOpenAI client."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Full-time employees receive 20 days of annual leave."

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    service = LLMService(provider_name="openai", api_key="sk-testkey")
    
    with patch.object(service.provider, "_get_client", return_value=mock_client):
        answer = await service.generate_answer(
            question="What is the leave policy?",
            context="[Page 1] Employees accrue 20 days paid leave."
        )

        assert answer == "Full-time employees receive 20 days of annual leave."
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.0
        assert call_kwargs["messages"][0]["role"] == "system"
        assert RAG_SYSTEM_PROMPT == call_kwargs["messages"][0]["content"]


@pytest.mark.asyncio
async def test_openai_provider_mocked_generate_answer_stream():
    """Test OpenAIProvider generate_answer_stream using mocked AsyncOpenAI streaming client."""
    async def mock_stream_generator():
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Full-time "
        yield chunk1

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "employees receive 20 days."
        yield chunk2

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream_generator())

    service = LLMService(provider_name="openai", api_key="sk-testkey")

    with patch.object(service.provider, "_get_client", return_value=mock_client):
        stream_chunks = []
        async for chunk in service.generate_answer_stream(
            question="What is the leave policy?",
            context="[Page 1] Employees accrue 20 days paid leave."
        ):
            stream_chunks.append(chunk)

        assert stream_chunks == ["Full-time ", "employees receive 20 days."]


@pytest.mark.asyncio
async def test_ollama_provider_mocked_generate_answer():
    """Test OllamaProvider generate_answer using mocked httpx.AsyncClient."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "message": {"content": "Ollama response: 20 days annual leave."}
    }

    mock_post = AsyncMock(return_value=mock_resp)

    service = LLMService(provider_name="ollama", model_name="llama3")

    with patch("httpx.AsyncClient.post", mock_post):
        answer = await service.generate_answer(
            question="What is the leave policy?",
            context="[Page 1] Employees accrue 20 days paid leave."
        )

        assert answer == "Ollama response: 20 days annual leave."
        mock_post.assert_called_once()
        url_called = mock_post.call_args[0][0]
        assert url_called == "http://localhost:11434/api/chat"


@pytest.mark.asyncio
async def test_missing_api_key_raises_exception():
    """Test attempting to generate answer without an API key raises LLMProviderError."""
    service = LLMService(provider_name="openai", api_key=None)
    # Clear settings API key for isolation
    with patch("app.config.settings.OPENAI_API_KEY", None), patch("app.config.settings.LLM_API_KEY", None):
        with pytest.raises(LLMProviderError) as exc:
            await service.generate_answer(question="Question?", context="Context")
        assert "OpenAI API key is missing" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_empty_question_rejection():
    """Test generate_answer raises ValueError if question is empty."""
    service = LLMService(provider_name="openai", api_key="sk-test")
    with pytest.raises(ValueError) as exc:
        await service.generate_answer(question="   \t ", context="Context")
    assert "Question cannot be empty" in str(exc.value)
