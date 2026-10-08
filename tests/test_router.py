import pytest

from medical_assistant.domains import MedicalDomain
from medical_assistant.routing import MedicalAgentRouter


@pytest.fixture
def router():
    return MedicalAgentRouter()


@pytest.mark.parametrize("query, expected", [
    ("What are the symptoms of diabetes?", MedicalDomain.DIABETES),
    ("How does metformin lower blood sugar?", MedicalDomain.DIABETES),
    ("How is breast cancer staged?", MedicalDomain.CANCER),
    ("Which tumors are malignant?", MedicalDomain.CANCER),          # plural form
    ("What are the DSM-5 criteria for major depression?", MedicalDomain.MENTAL_HEALTH),
    ("Tell me about anxiety disorders", MedicalDomain.MENTAL_HEALTH),
    ("What's the difference between STEMI and NSTEMI?", MedicalDomain.CARDIAC),
    ("What are the current hypertension guidelines?", MedicalDomain.CARDIAC),
    ("hello", MedicalDomain.GENERAL),
    ("what is your name", MedicalDomain.GENERAL),
])
def test_routes_queries_to_expected_domain(router, query, expected):
    assert router.route_query(query) == expected


def test_short_keyword_does_not_match_inside_other_words(router):
    # The notebook matched 'mi' inside 'mild'/'limit'; whole-word matching must not.
    assert router.route_query("What is a mild fever?") == MedicalDomain.GENERAL
    assert router.route_query("What is the daily sodium limit?") == MedicalDomain.GENERAL


def test_most_keyword_hits_wins(router):
    # 'diabetes' (1 hit) ties with 'heart' (1 hit); ties go to the first domain listed.
    assert router.route_query("Can diabetes increase the risk of heart disease?") == MedicalDomain.DIABETES
    # Two cardiac hits beat one diabetes hit.
    assert router.route_query("heart failure and chest pain with diabetes") == MedicalDomain.CARDIAC


def test_score_reports_hits_per_domain(router):
    scores = router.score("insulin and metformin for diabetes")
    assert scores[MedicalDomain.DIABETES] == 3
    assert MedicalDomain.CANCER not in scores
