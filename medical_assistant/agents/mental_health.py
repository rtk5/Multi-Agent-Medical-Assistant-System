"""Mental health / psychiatry specialist (PsychiatryGPT)."""

from medical_assistant.agents.base import BaseMedicalAgent
from medical_assistant.domains import MedicalDomain


class MentalHealthAgent(BaseMedicalAgent):
    """Answers psychiatry questions (DSM-5 criteria, medications, psychotherapy)."""

    domain = MedicalDomain.MENTAL_HEALTH
    display_name = "Mental Health/Psychiatry"
