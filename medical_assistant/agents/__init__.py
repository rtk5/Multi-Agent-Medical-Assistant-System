"""Specialist RAG agents, one per medical domain."""

from medical_assistant.agents.base import BaseMedicalAgent
from medical_assistant.agents.cancer import CancerAgent
from medical_assistant.agents.cardiac import CardiacAgent
from medical_assistant.agents.diabetes import DiabeticAgent
from medical_assistant.agents.mental_health import MentalHealthAgent

__all__ = [
    "BaseMedicalAgent",
    "DiabeticAgent",
    "CancerAgent",
    "MentalHealthAgent",
    "CardiacAgent",
]
