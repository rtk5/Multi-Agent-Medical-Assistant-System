"""Keyword-based query router.

Decides which specialist agent should answer a question. Each domain has a
list of keywords; the domain with the most keyword hits wins. If nothing
matches, the query goes to the GENERAL handler.
"""

from __future__ import annotations

import re
from typing import Dict, List, Pattern

from medical_assistant.domains import MedicalDomain

DOMAIN_KEYWORDS: Dict[MedicalDomain, List[str]] = {
    MedicalDomain.DIABETES: [
        "diabetes", "diabetic", "insulin", "glucose", "blood sugar", "hba1c", "metformin",
        "type 1 diabetes", "type 2 diabetes", "dka", "diabetic ketoacidosis", "hyperglycemia",
        "hypoglycemia", "diabetic nephropathy", "diabetic retinopathy", "gestational diabetes",
    ],
    MedicalDomain.CANCER: [
        "cancer", "oncology", "tumor", "malignancy", "chemotherapy", "radiation therapy",
        "metastasis", "carcinoma", "lymphoma", "leukemia", "staging", "biopsy",
        "breast cancer", "lung cancer", "colon cancer", "prostate cancer", "melanoma",
    ],
    MedicalDomain.MENTAL_HEALTH: [
        "depression", "anxiety", "bipolar", "schizophrenia", "psychiatric", "mental health",
        "antidepressant", "mood disorder", "panic", "ptsd", "adhd", "autism",
        "psychotherapy", "ssri", "snri", "antipsychotic", "mood stabilizer",
    ],
    MedicalDomain.CARDIAC: [
        "heart", "cardiac", "cardiovascular", "cardiology", "myocardial infarction", "mi",
        "stemi", "nstemi", "heart failure", "cardiomyopathy", "hypertension", "blood pressure",
        "arrhythmia", "ecg", "ekg", "chest pain", "angina", "coronary", "valve", "pericardial",
        "aortic", "mitral",
    ],
}


def _compile_keyword(keyword: str) -> Pattern[str]:
    """Match ``keyword`` as whole words, allowing a plural 's' or 'es'.

    ``(?<![a-z0-9])`` means "not preceded by a letter or digit", so ``mi``
    does not match inside ``mild`` or ``limit``. The trailing lookahead stops
    partial matches such as ``ssri`` inside ``ssrix``.
    """
    return re.compile(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?:e?s)?(?![a-z0-9])")


class MedicalAgentRouter:
    """Scores a query against each domain's keywords and picks the best one."""

    def __init__(self, domain_keywords: Dict[MedicalDomain, List[str]] | None = None):
        keywords = domain_keywords if domain_keywords is not None else DOMAIN_KEYWORDS
        self.domain_keywords = keywords
        self._patterns: Dict[MedicalDomain, List[Pattern[str]]] = {
            domain: [_compile_keyword(k.lower()) for k in words]
            for domain, words in keywords.items()
        }

    def score(self, query: str) -> Dict[MedicalDomain, int]:
        """Return {domain: number of keywords found} for domains with at least one hit."""
        text = query.lower()
        scores: Dict[MedicalDomain, int] = {}
        for domain, patterns in self._patterns.items():
            hits = sum(1 for pattern in patterns if pattern.search(text))
            if hits:
                scores[domain] = hits
        return scores

    def route_query(self, query: str) -> MedicalDomain:
        """Return the best-matching domain, or GENERAL when nothing matches.

        Ties go to the domain listed first in ``DOMAIN_KEYWORDS`` because
        ``max`` keeps the first maximum it sees.
        """
        scores = self.score(query)
        if not scores:
            return MedicalDomain.GENERAL
        return max(scores, key=scores.get)
