import pytest

from medical_assistant.agents import CancerAgent, CardiacAgent, DiabeticAgent, MentalHealthAgent
from medical_assistant.domains import MedicalDomain
from medical_assistant.orchestrator import MedicalAssistantOrchestrator


@pytest.fixture
def assistant(fake_llm, fake_embeddings):
    """Orchestrator with four real agents backed by demo content and fake models."""
    agents = {
        MedicalDomain.DIABETES: DiabeticAgent(llm=fake_llm, embeddings=fake_embeddings),
        MedicalDomain.CANCER: CancerAgent(llm=fake_llm, embeddings=fake_embeddings),
        MedicalDomain.MENTAL_HEALTH: MentalHealthAgent(llm=fake_llm, embeddings=fake_embeddings),
        MedicalDomain.CARDIAC: CardiacAgent(llm=fake_llm, embeddings=fake_embeddings),
    }
    orchestrator = MedicalAssistantOrchestrator(agents=agents)
    # No PDF paths -> every agent falls back to demo content.
    orchestrator.load_knowledge_bases({domain: ["missing.pdf"] for domain in agents})
    return orchestrator


def test_all_agents_ready_after_demo_fallback(assistant):
    status = assistant.get_system_status()
    assert status["total_agents"] == 4
    assert status["active_agents"] == 4


def test_chat_routes_to_specialist_and_answers(assistant):
    response = assistant.chat("What are the symptoms of diabetes?")
    assert response["domain"] == "diabetes"
    assert response["agent"] == "Diabetes"
    assert "Stubbed clinical answer" in response["answer"]
    assert response["conversation_count"] == 1


def test_general_query_gets_help_message(assistant):
    response = assistant.chat("what is your name")
    assert response["domain"] == "general"
    assert "couldn't identify a specific medical specialty" in response["answer"]


def test_shared_history_has_no_duplicates(assistant):
    assistant.chat("What are the symptoms of diabetes?")
    history = assistant.get_conversation_history()
    # One exchange = exactly one human + one AI message (the notebook stored extra copies).
    assert [m.type for m in history] == ["human", "ai"]
    assert history[0].content == "What are the symptoms of diabetes?"


def test_agent_switch_is_announced(assistant):
    assistant.chat("What are the symptoms of diabetes?")
    response = assistant.chat("How is breast cancer staged?")
    assert "Switched to Cancer/Oncology specialist" in response["answer"]


def test_history_is_capped_to_shared_window(fake_llm, fake_embeddings):
    orchestrator = MedicalAssistantOrchestrator(agents={}, shared_window=2)
    for i in range(10):
        orchestrator._remember(f"q{i}", f"a{i}")
    assert len(orchestrator.get_conversation_history()) == 4  # 2 exchanges * 2 messages


def test_clear_resets_state(assistant):
    assistant.chat("What is diabetes?")
    assistant.clear_conversation_history()
    status = assistant.get_system_status()
    assert status["memory_messages"] == 0
    assert status["conversation_count"] == 0
    assert status["last_agent_used"] is None


def test_unready_agent_returns_unavailable_message(fake_llm, fake_embeddings):
    agent = CardiacAgent(llm=fake_llm, embeddings=fake_embeddings)  # never loaded
    orchestrator = MedicalAssistantOrchestrator(agents={MedicalDomain.CARDIAC: agent})
    response = orchestrator.chat("What is a STEMI?")
    assert "not available right now" in response["answer"]
    assert orchestrator.get_conversation_history() == []
