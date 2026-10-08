"""Knowledge-base ingestion: PDF loading, chunking and demo content."""

from medical_assistant.knowledge.demo_loader import build_demo_documents
from medical_assistant.knowledge.pdf_loader import LoadResult, load_pdfs, split_into_chunks

__all__ = ["LoadResult", "load_pdfs", "split_into_chunks", "build_demo_documents"]
