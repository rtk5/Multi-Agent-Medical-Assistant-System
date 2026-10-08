import pytest

from medical_assistant import cli
from medical_assistant.orchestrator import MedicalAssistantOrchestrator


def _scripted(inputs):
    """Return an input() replacement that yields the given lines in order."""
    iterator = iter(inputs)
    return lambda prompt="": next(iterator)


def test_quit_ends_chat_without_calling_agents(capsys):
    assistant = MedicalAssistantOrchestrator(agents={})
    cli.interactive_chat(assistant, input_func=_scripted(["quit"]))
    out = capsys.readouterr().out
    assert "Thank you for using" in out
    assert assistant.conversation_count == 0


def test_status_and_clear_commands_are_handled(capsys):
    assistant = MedicalAssistantOrchestrator(agents={})
    assistant._remember("hi", "hello")  # seed some history
    cli.interactive_chat(assistant, input_func=_scripted(["status", "clear", "exit"]))
    out = capsys.readouterr().out
    assert "SYSTEM STATUS" in out
    assert "Conversation history cleared" in out
    assert assistant.get_conversation_history() == []


def test_empty_input_is_rejected_politely(capsys):
    assistant = MedicalAssistantOrchestrator(agents={})
    cli.interactive_chat(assistant, input_func=_scripted(["   ", "q"]))
    assert "Please enter a medical question or command." in capsys.readouterr().out


def test_keyboard_interrupt_exits_cleanly(capsys):
    def interrupt(prompt=""):
        raise KeyboardInterrupt
    cli.interactive_chat(MedicalAssistantOrchestrator(agents={}), input_func=interrupt)
    assert "Goodbye" in capsys.readouterr().out


def test_argument_parser_rejects_demo_with_ask():
    parser = cli.build_arg_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--demo", "--ask", "x"])
