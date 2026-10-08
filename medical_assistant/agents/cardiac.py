"""Cardiac / cardiovascular specialist (CardiologyGPT)."""

from medical_assistant.agents.base import BaseMedicalAgent
from medical_assistant.domains import MedicalDomain


class CardiacAgent(BaseMedicalAgent):
    """Answers cardiology questions (MI, heart failure, hypertension)."""

    domain = MedicalDomain.CARDIAC
    display_name = "Cardiac/Cardiovascular"
