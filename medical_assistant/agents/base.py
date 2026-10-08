"""Base class for every specialist agent.

A specialist agent is a retrieval-augmented generation (RAG) pipeline:

1. ``load_knowledge_base``  - PDFs -> chunks -> embeddings -> Chroma vector store
2. ``setup_conversation_chain`` - retriever + LLM + prompt + memory
3. ``ask_question``         - retrieve top-k chunks, answer with the LLM
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage

from medical_assistant.config import MEMORY, RETRIEVAL
from medical_assistant.domains import MedicalDomain
from medical_assistant.knowledge import build_demo_documents, load_pdfs, split_into_chunks
from medical_assistant.llm import create_embeddings, create_llm
from medical_assistant.prompts import build_prompt

logger = logging.getLogger(__name__)


class BaseMedicalAgent:
    """Shared RAG behaviour. Subclasses set ``domain`` and ``display_name``."""

    domain: MedicalDomain = MedicalDomain.GENERAL
    display_name: str = "General"

    def __init__(
        self,
        llm: Any = None,
        embeddings: Any = None,
        memory_window: int = MEMORY.agent_window,
        top_k: int = RETRIEVAL.top_k,
    ):
        # Dependency injection: production code uses watsonx, tests pass fakes.
        self.llm = llm if llm is not None else create_llm()
        self.embeddings = embeddings if embeddings is not None else create_embeddings()
        self.memory_window = memory_window
        self.top_k = top_k
        self.knowledge_base: Optional[Chroma] = None
        self.conversation_chain: Optional[ConversationalRetrievalChain] = None

    # ------------------------------------------------------------------ #
    # Knowledge base
    # ------------------------------------------------------------------ #
    def load_knowledge_base(self, pdf_paths: List[str]) -> Tuple[int, int]:
        """Build the vector store from PDFs.

        Returns ``(number_of_chunks, number_of_files_loaded)``. If no PDF can
        be read, the agent falls back to built-in demo content.
        """
        result = load_pdfs(pdf_paths, self.domain)

        if not result.pages:
            logger.warning("No %s textbooks loaded; using demo content.", self.display_name)
            return self.create_demo_knowledge_base()

        chunks = split_into_chunks(result.pages)
        logger.info("%s: created %d chunks from %d files", self.display_name, len(chunks), result.files_loaded)

        try:
            self.knowledge_base = Chroma.from_documents(
                chunks,
                self.embeddings,
                collection_name=f"{self.domain.value}_knowledge",
            )
            return len(chunks), result.files_loaded
        except Exception as embed_error:
            # Large batches can exceed API limits; retry in smaller pieces.
            logger.warning("Embedding failed for %s (%s); retrying in batches.", self.display_name, embed_error)
            return self._create_knowledge_base_in_batches(chunks), result.files_loaded

    def _create_knowledge_base_in_batches(self, chunks: Sequence[Document], batch_size: int = 50) -> int:
        """Embed chunks ``batch_size`` at a time. Returns how many chunks were stored."""
        stored = 0
        for start in range(0, len(chunks), batch_size):
            batch = list(chunks[start:start + batch_size])
            try:
                if self.knowledge_base is None:
                    self.knowledge_base = Chroma.from_documents(
                        batch,
                        self.embeddings,
                        collection_name=f"{self.domain.value}_knowledge",
                    )
                else:
                    self.knowledge_base.add_documents(batch)
                stored += len(batch)
            except Exception as batch_error:
                logger.error("%s batch starting at %d failed: %s", self.display_name, start, batch_error)
        return stored

    def create_demo_knowledge_base(self) -> Tuple[int, int]:
        """Embed the built-in demo sections. Returns ``(documents, 1)``."""
        documents = build_demo_documents(self.domain)
        self.knowledge_base = Chroma.from_documents(
            documents,
            self.embeddings,
            collection_name=f"{self.domain.value}_demo",
        )
        logger.info("%s demo knowledge base ready with %d sections", self.display_name, len(documents))
        return len(documents), 1

    # ------------------------------------------------------------------ #
    # Chain
    # ------------------------------------------------------------------ #
    def create_medical_prompt(self):
        """Specialty prompt (see ``medical_assistant.prompts``)."""
        return build_prompt(self.domain)

    def setup_conversation_chain(self) -> None:
        """Wire retriever, LLM, prompt and per-agent memory together."""
        if self.knowledge_base is None:
            raise ValueError(f"{self.display_name} knowledge base not loaded.")

        retriever = self.knowledge_base.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )
        # Memory is seeded from the orchestrator's shared history on every call.
        memory = ConversationBufferWindowMemory(
            k=self.memory_window,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )
        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": self.create_medical_prompt()},
            verbose=False,
        )

    @property
    def is_ready(self) -> bool:
        return self.knowledge_base is not None and self.conversation_chain is not None

    # ------------------------------------------------------------------ #
    # Question answering
    # ------------------------------------------------------------------ #
    def ask_question(self, question: str, chat_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """Answer one question. Errors are returned as an apology, never raised."""
        if self.conversation_chain is None:
            raise ValueError(f"{self.display_name} conversation chain not setup.")

        # Copy the list: the chain writes into its memory, and we must not
        # mutate the orchestrator's shared history from here.
        self.conversation_chain.memory.chat_memory.messages = list(chat_history or [])

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        formatted_question = f"[{self.display_name} Query - {timestamp}] {question}"

        try:
            result = self.conversation_chain.invoke({"question": formatted_question})
            sources = result.get("source_documents", [])
            return {
                "answer": result["answer"],
                "source_documents": sources,
                "confidence": "High" if len(sources) >= 3 else "Medium",
                "domain": self.domain.value,
                "agent": self.display_name,
            }
        except Exception as exc:
            logger.exception("%s agent failed", self.display_name)
            return {
                "answer": (
                    f"I apologize, but I encountered an error processing your {self.display_name} "
                    f"query: {exc}. Please try rephrasing your question."
                ),
                "source_documents": [],
                "confidence": "Low",
                "domain": self.domain.value,
                "agent": self.display_name,
            }
