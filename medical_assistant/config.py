"""Central configuration for the Multi-Agent Medical Assistant.

Everything that used to be hard-coded in the notebook (model id, LLM
parameters, watsonx endpoint, PDF file list) lives here so it can be changed
in one place. Secrets are read from environment variables / a local `.env`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from medical_assistant.domains import MedicalDomain

# Chroma tries to send anonymous telemetry; the installed version logs an
# error for every query. Disable it unless the user explicitly re-enables it.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# Read a local .env file (if present) into os.environ before we read settings.
load_dotenv()

# Repository root = the folder that contains the `medical_assistant` package.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
TEXTBOOKS_DIR: Path = PROJECT_ROOT / "textbooks"


@dataclass(frozen=True)
class WatsonxSettings:
    """Connection + generation settings for IBM watsonx.ai."""

    url: str = field(default_factory=lambda: os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"))
    project_id: str = field(default_factory=lambda: os.getenv("WATSONX_PROJECT_ID", ""))
    api_key: str = field(default_factory=lambda: os.getenv("WATSONX_APIKEY", ""))

    # Generation model (same as the notebook)
    llm_model_id: str = "mistralai/mistral-large"
    max_new_tokens: int = 512
    temperature: float = 0.1       # low = more deterministic / factual
    top_p: float = 0.9
    repetition_penalty: float = 1.1

    # Embedding model (768-dimensional vectors)
    embedding_model_id: str = "ibm/slate-125m-english-rtrvr"
    embedding_truncate_tokens: int = 3

    def validate(self) -> None:
        """Raise a clear error if the credentials are missing."""
        missing = [name for name, value in (
            ("WATSONX_PROJECT_ID", self.project_id),
            ("WATSONX_APIKEY", self.api_key),
        ) if not value]
        if missing:
            raise RuntimeError(
                "Missing watsonx.ai settings: " + ", ".join(missing)
                + ". Copy .env.example to .env and fill them in."
            )


@dataclass(frozen=True)
class ChunkingSettings:
    """How PDF pages are split into chunks before embedding."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: tuple = ("\n\n", "\n", ". ", " ", "")


@dataclass(frozen=True)
class RetrievalSettings:
    """How many chunks each agent retrieves per question."""

    top_k: int = 5


@dataclass(frozen=True)
class MemorySettings:
    """Conversation memory windows (number of user/assistant exchanges)."""

    agent_window: int = 10     # per-agent ConversationBufferWindowMemory
    shared_window: int = 20    # orchestrator-level memory shared by all agents


# Which PDFs each specialist agent reads. Paths are relative to TEXTBOOKS_DIR.
# Files that do not exist are skipped with a warning, and an agent with no
# readable PDFs falls back to built-in demo content.
PDF_CONFIGS: dict[MedicalDomain, list[str]] = {
    MedicalDomain.DIABETES: [
        "diabetes_guidelines.pdf",
        "insulin_therapy.pdf",
    ],
    MedicalDomain.CANCER: [
        "chemotherapy_protocols.pdf",
        "oncology_textbook.pdf",
    ],
    MedicalDomain.MENTAL_HEALTH: [
        "psychiatry_textbook.pdf",
    ],
    MedicalDomain.CARDIAC: [
        "heart_failure_guidelines.pdf",
        "cardiology_textbook.pdf",
    ],
}


def resolve_pdf_paths(relative_names: list[str], base_dir: Path = TEXTBOOKS_DIR) -> list[str]:
    """Turn the configured file names into absolute path strings."""
    return [str(base_dir / name) for name in relative_names]


WATSONX = WatsonxSettings()
CHUNKING = ChunkingSettings()
RETRIEVAL = RetrievalSettings()
MEMORY = MemorySettings()


def default_pdf_configs() -> dict[MedicalDomain, list[str]]:
    """PDF_CONFIGS with every file name resolved to a full path under textbooks/."""
    return {domain: resolve_pdf_paths(names) for domain, names in PDF_CONFIGS.items()}
