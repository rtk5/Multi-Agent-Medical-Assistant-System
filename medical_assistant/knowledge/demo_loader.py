"""Turn the built-in demo text into Documents (used when no PDF is usable)."""

from __future__ import annotations

import textwrap
from typing import List

from langchain_core.documents import Document

from medical_assistant.domains import MedicalDomain
from medical_assistant.knowledge.demo_content import DEMO_DOCUMENTS


def build_demo_documents(domain: MedicalDomain) -> List[Document]:
    """Return one Document per demo section for ``domain`` (empty if none)."""
    sections = DEMO_DOCUMENTS.get(domain.value, [])
    documents: List[Document] = []
    for index, (topic, text) in enumerate(sections, start=1):
        documents.append(Document(
            page_content=textwrap.dedent(text).strip(),
            metadata={
                "source": f"{domain.value}_demo_section_{index}",
                "topic": topic,
                "domain": domain.value,
            },
        ))
    return documents
