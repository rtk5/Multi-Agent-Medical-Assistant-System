"""Interactive terminal interface (the equivalent of the notebook's chat cell)."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Callable, Dict, List, Optional

from medical_assistant.config import default_pdf_configs
from medical_assistant.orchestrator import MedicalAssistantOrchestrator

EXAMPLE_QUERIES: Dict[str, List[str]] = {
    "🩺 Diabetes": [
        "What are the diagnostic criteria for Type 2 diabetes?",
        "How do we manage diabetic ketoacidosis?",
        "What are the contraindications for metformin?",
    ],
    "🎗️ Cancer/Oncology": [
        "How is breast cancer staged?",
        "What are the side effects of chemotherapy?",
        "What's the difference between NSCLC and SCLC?",
    ],
    "🧠 Mental Health": [
        "What are the DSM-5 criteria for major depression?",
        "How do we treat generalized anxiety disorder?",
        "What medications are used for bipolar disorder?",
    ],
    "❤️ Cardiovascular": [
        "What's the difference between STEMI and NSTEMI?",
        "How do we classify heart failure?",
        "What are the current hypertension guidelines?",
    ],
}

DEMO_QUERIES: List[str] = [
    "What are the diagnostic criteria for Type 2 diabetes?",
    "How is breast cancer staged and treated?",
    "What are the DSM-5 criteria for major depression?",
    "What's the difference between STEMI and NSTEMI?",
    "Can diabetes increase the risk of heart disease?",
    "Tell me about anxiety disorders",
]

HELP_TEXT = """
📝 Commands:
   • Type 'status' to see system status
   • Type 'clear' to clear conversation history
   • Type 'demo' to see example queries
   • Type 'quit' or 'exit' to end chat
"""


def build_orchestrator() -> MedicalAssistantOrchestrator:
    """Create the orchestrator and load every agent's PDFs (or demo content)."""
    print("🚀 Starting Multi-Agent Medical Assistant System...")
    assistant = MedicalAssistantOrchestrator()
    chunks, ready = assistant.load_knowledge_bases(default_pdf_configs())
    print(f"✅ {ready}/{len(assistant.agents)} agents ready ({chunks} knowledge chunks).")
    return assistant


def print_response(response: Dict) -> None:
    print(f"\n🩺 {response['agent']} ({response['confidence']} Confidence):")
    print("-" * 60)
    print(response["answer"])
    if response["source_documents"]:
        print(f"\n📚 Sources: {len(response['source_documents'])} relevant documents found")
    print(f"\n🔄 {response['routing_info']}")


def print_status(assistant: MedicalAssistantOrchestrator) -> None:
    status = assistant.get_system_status()
    print("\n📊 SYSTEM STATUS:")
    print(f"   • Active Agents: {status['active_agents']}/{status['total_agents']}")
    print(f"   • Total Conversations: {status['conversation_count']}")
    print(f"   • Last Agent Used: {status['last_agent_used']}")
    print(f"   • Memory Messages: {status['memory_messages']}")
    print("\n🤖 Agent Status:")
    for info in status["agent_status"].values():
        icon = "✅" if info["active"] else "❌"
        print(f"   {icon} {info['name']}: {'Active' if info['active'] else 'Inactive'}")


def print_examples() -> None:
    print("\n" + "=" * 60)
    print("💡 EXAMPLE MEDICAL QUERIES")
    print("=" * 60)
    for specialty, queries in EXAMPLE_QUERIES.items():
        print(f"\n{specialty}:")
        for query in queries:
            print(f"   • {query}")


def run_demo(assistant: MedicalAssistantOrchestrator) -> None:
    """Ask each scripted query and print which agent answered."""
    print("\n" + "=" * 80)
    print("🎯 MULTI-AGENT MEDICAL ASSISTANT DEMONSTRATION")
    print("=" * 80)
    for index, query in enumerate(DEMO_QUERIES, start=1):
        print(f"\n🔍 Demo Query {index}: {query}")
        print("-" * 60)
        response = assistant.chat(query)
        print(f"🤖 Agent Used: {response['agent']}")
        print(f"🎯 Domain: {response['domain']}")
        print(f"📊 Confidence: {response['confidence']}")
        preview = response["answer"]
        print("\n💬 Response Preview:")
        print(preview[:300] + "..." if len(preview) > 300 else preview)
        print("-" * 60)
    print_status(assistant)


def interactive_chat(assistant: MedicalAssistantOrchestrator,
                     input_func: Callable[[str], str] = input) -> None:
    """Read-eval-print loop. ``input_func`` can be replaced in tests."""
    print("\n" + "=" * 80)
    print("🏥 MULTI-AGENT MEDICAL ASSISTANT - CHAT INTERFACE")
    print("=" * 80)
    print("💡 I'm a specialized medical AI with expertise in:")
    print("   • 🩺 Diabetes & Endocrinology")
    print("   • 🎗️ Cancer & Oncology")
    print("   • 🧠 Mental Health & Psychiatry")
    print("   • ❤️ Cardiovascular Medicine")
    print(HELP_TEXT)
    print("🚀 Ready for your medical questions!")
    print("-" * 80)

    while True:
        try:
            user_input = input_func("\n👩‍⚕️ You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Chat interrupted. Goodbye!")
            break

        command = user_input.lower()
        if command in ("quit", "exit", "q"):
            print("\n👋 Thank you for using the Multi-Agent Medical Assistant!")
            break
        if command == "clear":
            assistant.clear_conversation_history()
            print("🧹 Conversation history cleared.")
            continue
        if command == "status":
            print_status(assistant)
            continue
        if command == "demo":
            print_examples()
            continue
        if not user_input:
            print("Please enter a medical question or command.")
            continue

        print("\n🤔 Processing your medical query...")
        try:
            print_response(assistant.chat(user_input))
        except Exception as exc:  # keep the chat alive on unexpected errors
            print(f"\n❌ Error: {exc}")
            print("Please try again with a different question.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-Agent Medical Assistant")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="run the scripted demo queries and exit")
    group.add_argument("--ask", metavar="QUESTION", help="answer one question and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="show loader/debug logs")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.ERROR,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        assistant = build_orchestrator()
    except RuntimeError as exc:  # e.g. missing watsonx credentials
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    if args.ask:
        print_response(assistant.chat(args.ask))
    elif args.demo:
        run_demo(assistant)
    else:
        interactive_chat(assistant)
    return 0


__all__ = ["main", "interactive_chat", "run_demo"]
