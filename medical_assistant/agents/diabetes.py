"""Diabetes specialist (DiabetesGPT)."""

from medical_assistant.agents.base import BaseMedicalAgent
from medical_assistant.domains import MedicalDomain


class DiabeticAgent(BaseMedicalAgent):
    """Answers diabetes questions from diabetes guidelines and insulin references."""

    domain = MedicalDomain.DIABETES
    display_name = "Diabetes"
