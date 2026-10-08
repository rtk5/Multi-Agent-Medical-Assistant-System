"""Medical domains supported by the assistant."""

from enum import Enum


class MedicalDomain(Enum):
    """Each value is the domain key used in metadata, collection names and logs."""

    DIABETES = "diabetes"
    CANCER = "cancer"
    MENTAL_HEALTH = "mental_health"
    CARDIAC = "cardiac"
    GENERAL = "general"  # not an agent; used when no specialty matches
