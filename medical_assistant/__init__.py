"""Multi-Agent Medical Assistant: RAG specialists for diabetes, oncology,
psychiatry and cardiology, routed by a keyword-based orchestrator.

For educational and research use only. Not a substitute for clinical judgement.
"""

import os

# Must run before chromadb is imported anywhere: the installed chromadb version
# logs a telemetry error on every query. Users can still override this in .env.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from medical_assistant.domains import MedicalDomain  # noqa: E402
from medical_assistant.orchestrator import MedicalAssistantOrchestrator  # noqa: E402

__all__ = ["MedicalDomain", "MedicalAssistantOrchestrator"]
__version__ = "1.0.0"
