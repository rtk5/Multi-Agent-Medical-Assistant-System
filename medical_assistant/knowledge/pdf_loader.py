"""Load textbook PDFs and split them into chunks ready for embedding.

Pipeline for one agent:  PDF files -> pages (Documents) -> chunks (Documents)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from medical_assistant.config import CHUNKING, ChunkingSettings
from medical_assistant.domains import MedicalDomain

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Outcome of loading a set of PDFs for one domain."""

    pages: List[Document] = field(default_factory=list)
    files_loaded: int = 0
    files_skipped: List[str] = field(default_factory=list)


def load_pdfs(pdf_paths: List[str], domain: MedicalDomain) -> LoadResult:
    """Read every readable PDF and tag each page with source metadata.

    Missing or unreadable files are logged and skipped instead of raising, so
    one bad file never stops the whole assistant from starting.
    """
    result = LoadResult()

    for index, pdf_path in enumerate(pdf_paths, start=1):
        if not os.path.exists(pdf_path):
            logger.warning("File not found, skipping: %s", pdf_path)
            result.files_skipped.append(pdf_path)
            continue
        if not os.access(pdf_path, os.R_OK):
            logger.warning("Cannot read file, skipping: %s", pdf_path)
            result.files_skipped.append(pdf_path)
            continue

        try:
            pages = PyPDFLoader(pdf_path).load()
        except Exception as exc:  # corrupt PDF, encryption, etc.
            logger.error("Error loading %s: %s", pdf_path, exc)
            result.files_skipped.append(pdf_path)
            continue

        if not pages:
            logger.warning("No pages extracted from %s", pdf_path)
            result.files_skipped.append(pdf_path)
            continue

        for page in pages:
            page.metadata.update({
                "source_textbook": f"{domain.value}_textbook_{index}",
                "source_path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "domain": domain.value,
            })

        result.pages.extend(pages)
        result.files_loaded += 1
        logger.info("Loaded %d pages from %s", len(pages), pdf_path)

    return result


def split_into_chunks(pages: List[Document], settings: ChunkingSettings = CHUNKING) -> List[Document]:
    """Split pages into overlapping chunks.

    ``chunk_size`` is measured in characters. The overlap keeps sentences that
    straddle a boundary available in both neighbouring chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=list(settings.separators),
        length_function=len,
    )
    return splitter.split_documents(pages)
