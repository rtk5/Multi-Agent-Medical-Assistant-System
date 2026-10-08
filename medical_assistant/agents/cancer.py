"""Cancer / oncology specialist (OncologyGPT)."""

from medical_assistant.agents.base import BaseMedicalAgent
from medical_assistant.domains import MedicalDomain


class CancerAgent(BaseMedicalAgent):
    """Answers oncology questions (staging, chemotherapy, treatment protocols)."""

    domain = MedicalDomain.CANCER
    display_name = "Cancer/Oncology"
