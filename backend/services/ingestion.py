
import hashlib
from pathlib import Path

import pymupdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import UPLOAD_DIR
from backend.db.chroma_store import get_vector_store


def extract_pdf_pages(pdf_path: Path) -> list[Document]:
    """Extract text from a PDF, preserving its page numbers."""

    documents = []

    with pymupdf.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            # Skip pages that contain no extractable text.
            if not text:
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": pdf_path.name,
                        "page": page_number,
                    },
                )
            )

    if not documents:
        raise ValueError(
            "No extractable text found. The PDF may be scanned."
        )

    return documents


def split_documents(
    documents: list[Document],
) -> list[Document]:
    """Split page text into smaller, overlapping chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        add_start_index=True,
    )

    return splitter.split_documents(documents)


def generate_chunk_id(document: Document, index: int) -> str:
    """Generate a repeatable ID for each text chunk."""

    unique_text = (
        f"{document.metadata['source']}"
        f"|{document.metadata['page']}"
        f"|{index}"
        f"|{document.page_content}"
    )

    return hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()


def store_chunks(chunks: list[Document]) -> int:
    """Store text chunks and generate their embeddings."""

    if not chunks:
        return 0

    vector_store = get_vector_store()

    ids = [
        generate_chunk_id(chunk, index)
        for index, chunk in enumerate(chunks)
    ]

    vector_store.add_documents(
        documents=chunks,
        ids=ids,
    )

    return len(chunks)


def ingest_pdf(pdf_path: str | Path) -> dict:
    """Run the complete PDF ingestion pipeline."""

    pdf_path = Path(pdf_path)

    if not pdf_path.is_absolute():
        pdf_path = UPLOAD_DIR / pdf_path

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    pages = extract_pdf_pages(pdf_path)
    chunks = split_documents(pages)
    stored_count = store_chunks(chunks)

    return {
        "filename": pdf_path.name,
        "pages_extracted": len(pages),
        "chunks_created": len(chunks),
        "chunks_submitted": stored_count,
        "status": "success",
    }
