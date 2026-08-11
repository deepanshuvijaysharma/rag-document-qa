"""Developer Inspection Utility for Visualizing Chunking Output."""

import os
import sys
import asyncio
from pathlib import Path

# Add backend directory to sys.path if running as script
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.document_service import DocumentService


async def inspect_pdf_chunks(pdf_path: str) -> None:
    """Read a PDF file from disk, run chunking, and print structured chunk output."""
    if not os.path.exists(pdf_path):
        print(f"[ERROR] File not found: {pdf_path}")
        return

    print("=" * 80)
    print("         DOCUMENT CHUNKER DEVELOPER INSPECTION UTILITY         ")
    print("=" * 80)
    print(f"Target PDF File      : {os.path.basename(pdf_path)}")
    print(f"Configured Chunk Size: {settings.CHUNK_SIZE} characters")
    print(f"Configured Overlap   : {settings.CHUNK_OVERLAP} characters")
    print("-" * 80)

    with open(pdf_path, "rb") as f:
        content = f.read()

    doc_service = DocumentService()
    result = await doc_service.process_pdf_upload(
        raw_filename=os.path.basename(pdf_path),
        content=content,
        content_type="application/pdf"
    )

    print(f"\n[SUMMARY] Document Processing Complete")
    print(f"  * Document ID  : {result['document_id']}")
    print(f"  * Filename     : {result['filename']}")
    print(f"  * File Size    : {result['file_size']} bytes")
    print(f"  * Total Pages  : {result['page_count']}")
    print(f"  * Total Chunks : {result['chunk_count']}\n")

    print("=" * 80)
    print("                       EXTRACTED CHUNKS DETAIL                         ")
    print("=" * 80)

    for chunk in result["chunks"]:
        print(f"\n+-- CHUNK #{chunk['chunk_index'] + 1} --------------------------------------------------------")
        print(f"| Chunk ID        : {chunk['chunk_id']}")
        print(f"| Source Filename : {chunk['source_filename']}")
        print(f"| Page Number     : Page {chunk['page_number']}")
        print(f"| Position Index  : {chunk['chunk_index']}")
        print(f"| Text Length     : {len(chunk['text'])} characters")
        print("+-- TEXT CONTENT ----------------------------------------------------------")
        for line in chunk["text"].split("\n"):
            print(f"|   {line}")
        print("+--------------------------------------------------------------------------")

    print("\n[SUCCESS] Inspection completed successfully.\n")


if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    default_pdf = os.path.join(root_dir, "documents", "sample_architecture.pdf")
    
    target_file = sys.argv[1] if len(sys.argv) > 1 else default_pdf
    asyncio.run(inspect_pdf_chunks(target_file))
