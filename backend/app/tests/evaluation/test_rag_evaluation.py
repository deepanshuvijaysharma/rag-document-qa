"""Automated RAG Evaluation & Benchmark Suite."""

import os
import sys
import json
import shutil
import tempfile
import pytest

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.document_service import DocumentService
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService
from app.services.chat_service import ChatService
from app.db.metadata_store import MetadataStore
from app.db.conversation_store import ConversationStore

EVAL_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(EVAL_DIR, "../../../"))
DATASET_PATH = os.path.join(EVAL_DIR, "rag_evaluation_dataset.json")


@pytest.fixture
async def eval_rag_environment():
    """Fixture initializing vector store with sample documents for benchmark evaluation."""
    temp_dir = tempfile.mkdtemp(prefix="rag_eval_bench_")
    chroma_dir = os.path.join(temp_dir, "chroma")
    meta_file = os.path.join(temp_dir, "documents.json")
    conv_file = os.path.join(temp_dir, "conversations.json")

    pdf_service = PDFService()
    chunking_service = ChunkingService(chunk_size=1000, chunk_overlap=200)
    embedding_service = EmbeddingService()
    vector_service = VectorService(persist_directory=chroma_dir, collection_name="eval_test_col")
    metadata_store = MetadataStore(file_path=meta_file)
    conversation_store = ConversationStore(file_path=conv_file)

    doc_service = DocumentService(
        pdf_service=pdf_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        vector_service=vector_service,
        metadata_store=metadata_store
    )

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_service=vector_service
    )

    # Ingest sample_employee_handbook.pdf
    hb_path = os.path.join(ROOT_DIR, "documents", "sample_employee_handbook.pdf")
    with open(hb_path, "rb") as f:
        hb_bytes = f.read()
    rec_hb = await doc_service.process_pdf_upload("sample_employee_handbook.pdf", hb_bytes, "application/pdf")

    # Ingest sample_architecture.pdf
    arch_path = os.path.join(ROOT_DIR, "documents", "sample_architecture.pdf")
    with open(arch_path, "rb") as f:
        arch_bytes = f.read()
    rec_arch = await doc_service.process_pdf_upload("sample_architecture.pdf", arch_bytes, "application/pdf")

    chat_service = ChatService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(),
        conversation_store=conversation_store
    )

    yield {
        "doc_service": doc_service,
        "retrieval_service": retrieval_service,
        "chat_service": chat_service,
        "hb_id": rec_hb["document_id"],
        "arch_id": rec_arch["document_id"],
        "temp_dir": temp_dir
    }

    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def load_eval_dataset():
    """Load benchmark evaluation dataset items."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_run_rag_evaluation_suite(eval_rag_environment):
    """Execute complete 10-item benchmark dataset and compute quantitative metrics."""
    dataset = load_eval_dataset()
    chat_service = eval_rag_environment["chat_service"]

    total_queries = len(dataset)
    retrieval_hits = 0
    groundedness_matches = 0
    citation_page_matches = 0
    evaluated_grounded_queries = 0

    print("\n" + "=" * 80)
    print(f"RUNNING RAG EVALUATION SUITE ({total_queries} Benchmark Items)")
    print("=" * 80)

    for item in dataset:
        item_id = item["id"]
        category = item["category"]
        question = item["question"]
        expected_sources = item.get("expected_sources", [])
        expected_substrings = item.get("expected_answer_contains", [])
        should_be_grounded = item.get("should_be_grounded", True)

        # Handle empty whitespace edge case
        if not question.strip():
            with pytest.raises(ValueError):
                await chat_service.answer_question(question)
            print(f"[{item_id}] Category '{category}': PASSED (Empty question rejected cleanly)")
            total_queries -= 1  # Exclude non-executable input from retrieval ratio
            continue

        response = await chat_service.answer_question(question)

        answer_text = response.answer
        returned_sources = response.sources

        # 1. Evaluate Retrieval Hit Rate
        hit_found = False
        if expected_sources:
            evaluated_grounded_queries += 1
            for exp_src in expected_sources:
                exp_file = exp_src["filename"]
                exp_page = exp_src["page_number"]

                for ret_src in returned_sources:
                    if ret_src.filename == exp_file:
                        hit_found = True
                        if ret_src.page_number == exp_page:
                            citation_page_matches += 1
                        break
            if hit_found:
                retrieval_hits += 1

        # 2. Evaluate Groundedness Answer Compliance
        if should_be_grounded:
            matches_sub = any(sub.lower() in answer_text.lower() for sub in expected_substrings)
            if matches_sub:
                groundedness_matches += 1
        else:
            if answer_text == "I am unable to find the answer in the uploaded documents.":
                groundedness_matches += 1

        print(f"[{item_id}] Category '{category}':")
        print(f"   Q: {question}")
        print(f"   A: {answer_text[:100]}...")
        print(f"   Sources Found: {len(returned_sources)}")

    # Calculate final metric percentages
    retrieval_hit_rate = (retrieval_hits / evaluated_grounded_queries * 100) if evaluated_grounded_queries else 0.0
    grounded_accuracy = (groundedness_matches / (total_queries) * 100) if total_queries else 0.0

    print("-" * 80)
    print("RAG BENCHMARK EVALUATION SUMMARY METRICS:")
    print(f"  • Total Benchmark Items Evaluated: {total_queries}")
    print(f"  • Grounded Information Queries:   {evaluated_grounded_queries}")
    print(f"  • Retrieval Recall@K (Hit Rate):  {retrieval_hit_rate:.1f}%")
    print(f"  • Grounded Answer Accuracy:       {grounded_accuracy:.1f}%")
    print("=" * 80)

    assert retrieval_hit_rate >= 80.0
    assert grounded_accuracy >= 80.0
