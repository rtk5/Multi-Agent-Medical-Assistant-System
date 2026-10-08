"""Command-line entry point.

Examples:
    python main.py                     # interactive chat (default)
    python main.py --demo              # run the scripted demo queries
    python main.py --ask "What is HbA1c?"
"""

from medical_assistant.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
