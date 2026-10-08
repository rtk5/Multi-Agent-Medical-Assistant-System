"""The orchestrator: owns the agents, the router and the shared conversation.

Every user message goes through ``MedicalAssistantOrchestrator.chat``:

1. The router picks a domain (diabetes, cancer, mental health, cardiac, general).
2. The matching specialist agent answers using its own knowledge base.
3. The question and answer are appended to the shared history, so the next
   agent (if the topic changes) still sees the conversation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from medical_assistant.agents import (
    BaseMedicalAgent,
    CancerAgent,
    CardiacAgent,
    DiabeticAgent,
    MentalHealthAgent,
)
from medical_assistant.config import MEMORY
from medical_assistant.domains import MedicalDomain
from medical_assistant.routing import MedicalAgentRouter

logger = logging.getLogger(__name__)

GENERAL_RESPONSE_TEMPLATE = """I'm a specialized medical assistant with expertise in diabetes, cancer/oncology, mental health/psychiatry, and cardiovascular medicine.

Your query: "{query}"

I couldn't identify a specific medical specialty for your question. Here are some options:

🩺 **Specialized Areas I Can Help With:**
- **Diabetes**: Blood sugar management, insulin therapy, diabetic complications
- **Cancer/Oncology**: Cancer staging, chemotherapy, treatment protocols
- **Mental Health**: Depression, anxiety, psychiatric medications
- **Cardiovascular**: Heart disease, hypertension, cardiac care

💡 **Try rephrasing your question with specific medical terms**, or ask me something like:
- "What are the symptoms of diabetes?"
- "How is breast cancer staged?"
- "What medications are used for depression?"
- "What causes heart attacks?"

I'm designed to provide evidence-based medical information to support clinical decision-making and medical education."""


class MedicalAssistantOrchestrator:
    """Manages all specialist agents, routing, and shared chat history."""

    def __init__(
        self,
        agents: Optional[Mapping[MedicalDomain, BaseMedicalAgent]] = None,
        router: Optional[MedicalAgentRouter] = None,
        shared_window: int = MEMORY.shared_window,
    ):
        self.router = router if router is not None else MedicalAgentRouter()
        if agents is None:
            agents = {
                MedicalDomain.DIABETES: DiabeticAgent(),
                MedicalDomain.CANCER: CancerAgent(),
                MedicalDomain.MENTAL_HEALTH: MentalHealthAgent(),
                MedicalDomain.CARDIAC: CardiacAgent(),
            }
        self.agents: Dict[MedicalDomain, BaseMedicalAgent] = dict(agents)

        self.shared_window = shared_window
        self._history: List[BaseMessage] = []
        self.last_agent_used: Optional[MedicalDomain] = None
        self.conversation_count = 0

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    def load_knowledge_bases(self, pdf_configs: Mapping[MedicalDomain, List[str]]) -> tuple[int, int]:
        """Load each agent's PDFs and build its conversation chain.

        Returns ``(total_chunks, number_of_ready_agents)``.
        """
        total_chunks = 0
        ready_agents = 0

        for domain, pdf_paths in pdf_configs.items():
            agent = self.agents.get(domain)
            if agent is None or not pdf_paths:
                continue
            try:
                chunks, _files = agent.load_knowledge_base(list(pdf_paths))
                agent.setup_conversation_chain()
                total_chunks += chunks
                ready_agents += 1
                logger.info("%s agent ready with %d chunks", agent.display_name, chunks)
            except Exception as exc:
                logger.error("Failed to set up %s agent: %s", domain.value, exc)

        return total_chunks, ready_agents

    # ------------------------------------------------------------------ #
    # Chat
    # ------------------------------------------------------------------ #
    def chat(self, user_input: str) -> Dict[str, Any]:
        """Route one message to a specialist (or the general handler) and answer."""
        self.conversation_count += 1
        target_domain = self.router.route_query(user_input)

        if target_domain == MedicalDomain.GENERAL or target_domain not in self.agents:
            return self._handle_general_query(user_input)

        agent = self.agents[target_domain]
        if not agent.is_ready:
            return {
                "answer": (
                    f"I apologize, but the {agent.display_name} specialist is not available right now. "
                    "Please try a general medical question or contact support."
                ),
                "source_documents": [],
                "confidence": "Low",
                "domain": target_domain.value,
                "agent": agent.display_name,
                "routing_info": f"Routed to {agent.display_name} but agent not ready",
            }

        response = agent.ask_question(user_input, list(self._history))

        if self.last_agent_used is not None and self.last_agent_used != target_domain:
            response["answer"] += f"\n\n🔄 *Switched to {agent.display_name} specialist for this query*"

        self._remember(user_input, response["answer"])
        self.last_agent_used = target_domain

        response["routing_info"] = f"Routed to {agent.display_name} specialist"
        response["conversation_count"] = self.conversation_count
        return response

    def _handle_general_query(self, user_input: str) -> Dict[str, Any]:
        """Reply with a help message for questions outside the four specialties."""
        answer = GENERAL_RESPONSE_TEMPLATE.format(query=user_input)
        self._remember(user_input, answer)
        return {
            "answer": answer,
            "source_documents": [],
            "confidence": "Medium",
            "domain": MedicalDomain.GENERAL.value,
            "agent": "General Medical Assistant",
            "routing_info": "Handled as general query",
            "conversation_count": self.conversation_count,
        }

    def _remember(self, user_input: str, answer: str) -> None:
        """Append one exchange to the shared history, keeping the last N exchanges."""
        self._history.append(HumanMessage(content=user_input))
        self._history.append(AIMessage(content=answer))
        max_messages = 2 * self.shared_window
        if len(self._history) > max_messages:
            del self._history[:-max_messages]

    # ------------------------------------------------------------------ #
    # Status / housekeeping
    # ------------------------------------------------------------------ #
    def get_system_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {
            "total_agents": len(self.agents),
            "active_agents": 0,
            "agent_status": {},
            "conversation_count": self.conversation_count,
            "last_agent_used": self.last_agent_used.value if self.last_agent_used else None,
            "memory_messages": len(self._history),
        }
        for domain, agent in self.agents.items():
            if agent.is_ready:
                status["active_agents"] += 1
            status["agent_status"][domain.value] = {
                "name": agent.display_name,
                "active": agent.is_ready,
                "has_knowledge_base": agent.knowledge_base is not None,
                "has_conversation_chain": agent.conversation_chain is not None,
            }
        return status

    def clear_conversation_history(self) -> None:
        self._history.clear()
        self.last_agent_used = None
        self.conversation_count = 0
        logger.info("Conversation history cleared.")

    def get_conversation_history(self) -> List[BaseMessage]:
        return list(self._history)
