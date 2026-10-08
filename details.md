# Code Details and Interview Guide

This document explains **every file in the project**, what each important function does, and **what you should be able to explain in an interview**. Read [explanation.md](explanation.md) first for the big picture.

---

## Table of Contents

1. [How to read this document](#1-how-to-read-this-document)
2. [Repository map](#2-repository-map)
3. [File-by-file walkthrough](#3-file-by-file-walkthrough)
4. [Following one question through the code](#4-following-one-question-through-the-code)
5. [Known issues in the original notebook and how the package fixes them](#5-known-issues-in-the-original-notebook-and-how-the-package-fixes-them)
6. [Testing](#6-testing)
7. [Interview preparation](#7-interview-preparation)
8. [Concepts you must be able to explain](#8-concepts-you-must-be-able-to-explain)
9. [Likely interview questions with answers](#9-likely-interview-questions-with-answers)
10. [A 5-minute demo script](#10-a-5-minute-demo-script)

---

## 1. How to read this document

- Section 3 is the reference: one entry per file.
- Section 4 traces one question from the keyboard to the answer.
- Sections 7–10 are for preparing for questions about the project.

Key Python terms used below:

- **`dataclass`**: a class that mostly holds data. Python writes `__init__` for you.
- **`Enum`**: a fixed set of named values (here, the medical domains).
- **`from __future__ import annotations`**: lets type hints refer to classes defined later and allows modern syntax such as `dict[str, int]` on older Python versions.
- **Type hints** (e.g. `pdf_paths: List[str]`) document the expected types. Python does not enforce them at run time.

---

## 2. Repository map

```text
main.py                          entry point: calls cli.main()
requirements.txt                 pinned runtime dependencies
requirements-dev.txt             adds pytest
pytest.ini                       test discovery settings
.env.example                     template for watsonx credentials (copy to .env)
.gitignore                       ignores .env, venvs, caches, Chroma data
medical_assistant/
    __init__.py                  package exports, telemetry switch
    config.py                    all settings and the PDF list
    domains.py                   MedicalDomain enum
    llm.py                       creates watsonx LLM and embedding objects
    prompts.py                   specialty prompt templates
    cli.py                       terminal chat, --ask, --demo
    orchestrator.py              routing + shared memory + status
    agents/
        __init__.py              re-exports the agent classes
        base.py                  BaseMedicalAgent: the RAG pipeline
        diabetes.py              DiabeticAgent
        cancer.py                CancerAgent
        mental_health.py         MentalHealthAgent
        cardiac.py               CardiacAgent
    knowledge/
        __init__.py              re-exports ingestion helpers
        pdf_loader.py            read PDFs, tag pages, split into chunks
        demo_loader.py           demo sections -> Documents
        demo_content.py          built-in demo text (data only)
    routing/
        __init__.py              re-exports the router
        router.py                keyword scoring -> domain
tests/
    conftest.py                  fake LLM and embedding fixtures
    test_router.py               routing rules
    test_knowledge.py            loader, chunker, demo data, prompts, config drift
    test_orchestrator.py         end-to-end offline chat flow
    test_cli.py                  command loop
notebooks/                       original notebooks (reference only)
textbooks/                       PDFs read by the agents
```

---

## 3. File-by-file walkthrough

### 3.1 `main.py`

```python
from medical_assistant.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
```

- The `if __name__ == "__main__"` guard means the code only runs when the file is executed directly, not when it is imported.
- `main()` returns an exit code (0 success, 1 configuration error). `SystemExit` passes that code to the shell.

### 3.2 `medical_assistant/__init__.py`

- Sets `os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")` **before** the imports below. Chroma reads this variable when it is imported, so the order matters. The `# noqa: E402` comments tell linters that the late imports are intentional.
- Exports `MedicalDomain`, `MedicalAssistantOrchestrator` and `__version__`.

### 3.3 `medical_assistant/config.py`

This is the single place to change behaviour.

| Name | What it is |
|---|---|
| `PROJECT_ROOT`, `TEXTBOOKS_DIR` | Absolute paths computed from the file's own location, so the program works from any current folder. |
| `load_dotenv()` | Reads `.env` into `os.environ`. Real environment variables still win. |
| `WatsonxSettings` (frozen dataclass) | URL, project id, API key from the environment; model id; `max_new_tokens=512`, `temperature=0.1`, `top_p=0.9`, `repetition_penalty=1.1`; embedding model `ibm/slate-125m-english-rtrvr`. `validate()` raises `RuntimeError` listing the missing variables. |
| `ChunkingSettings` | `chunk_size=1000`, `chunk_overlap=200`, separators in priority order. |
| `RetrievalSettings` | `top_k=5`. |
| `MemorySettings` | `agent_window=10` (per agent), `shared_window=20` (orchestrator). |
| `PDF_CONFIGS` | Dictionary from domain to a list of PDF file names inside `textbooks/`. |
| `resolve_pdf_paths()` | Joins the names with `TEXTBOOKS_DIR`. |
| `default_pdf_configs()` | `PDF_CONFIGS` with full paths. |
| `WATSONX`, `CHUNKING`, `RETRIEVAL`, `MEMORY` | Module-level instances used as defaults elsewhere. |

`frozen=True` makes the settings immutable, so a value cannot change by accident during a run.

### 3.4 `medical_assistant/domains.py`

`MedicalDomain(Enum)` with values `diabetes`, `cancer`, `mental_health`, `cardiac`, `general`. The value strings are used in metadata, Chroma collection names and log messages. `GENERAL` is not an agent. It means "no specialty matched".

### 3.5 `medical_assistant/llm.py`

- `create_llm(settings)` builds `langchain_ibm.WatsonxLLM` with `model_id`, `url`, `apikey`, `project_id` and a `params` dictionary. The keys come from `GenTextParamsMetaNames` (for example `MAX_NEW_TOKENS`). Using the enum constants avoids typos in parameter names.
- `create_embeddings(settings)` builds `WatsonxEmbeddings` with `EmbedTextParamsMetaNames`. `TRUNCATE_INPUT_TOKENS` is set to 3 as in the notebook. This is a very small limit and may cut long chunks. It is kept for fidelity, and is worth mentioning as a question to investigate.
- Both call `settings.validate()` first, so the error is clear.

### 3.6 `medical_assistant/prompts.py`

- Four string templates, one per specialty. Each gives the model a persona (DiabetesGPT, OncologyGPT, PsychiatryGPT, CardiologyGPT), numbered guidelines, and the three placeholders.
- `INPUT_VARIABLES = ["context", "chat_history", "question"]` must match what the chain supplies.
- `build_prompt(domain)` returns a LangChain `PromptTemplate`. It raises `ValueError` for an unknown domain, so a missing template fails early.

Prompt engineering is part of the design: the "Base responses on provided … literature" rule is the main way the answer is kept close to the sources.

### 3.7 `medical_assistant/knowledge/pdf_loader.py`

- `LoadResult` (dataclass): `pages`, `files_loaded`, `files_skipped`.
- `load_pdfs(pdf_paths, domain)`:
  1. checks that each file exists and is readable (`os.path.exists`, `os.access`);
  2. reads it with `PyPDFLoader(path).load()`, which returns one `Document` per page;
  3. updates each page's metadata with `domain`, `filename`, `source_path`, and `source_textbook` (for example `cardiac_textbook_2`);
  4. records skipped files instead of raising an exception.
- `split_into_chunks(pages, settings)`: builds a `RecursiveCharacterTextSplitter`. It tries to split on `\n\n`, then `\n`, `. `, space, and finally single characters, so chunks end at natural boundaries where possible. `length_function=len` counts characters, not tokens.

### 3.8 `medical_assistant/knowledge/demo_content.py`

A dictionary `DEMO_DOCUMENTS` from domain name to a list of `(topic, text)` tuples. It was generated from the notebook's demo strings, so the content is the same. It only contains text, with no logic.

### 3.9 `medical_assistant/knowledge/demo_loader.py`

`build_demo_documents(domain)` turns the tuples into `Document` objects. `textwrap.dedent` removes the leading indentation that came from the notebook's triple-quoted strings.

### 3.10 `medical_assistant/knowledge/__init__.py`

Re-exports `load_pdfs`, `split_into_chunks`, `LoadResult` and `build_demo_documents`, so other modules can write `from medical_assistant.knowledge import ...`.

### 3.11 `medical_assistant/routing/router.py`

- `DOMAIN_KEYWORDS`: keyword lists per domain. Multi-word phrases such as `"blood sugar"` work because matching is done on the whole text.
- `_compile_keyword(keyword)` returns a compiled regular expression:
  - `(?<![a-z0-9])` means "the keyword must not follow a letter or digit", so `mi` will not match inside *mild* or *limit*;
  - `(?:e?s)?` allows a plural such as *tumors* or *boxes*;
  - `(?![a-z0-9])` means "not followed by a letter or digit".
- `MedicalAgentRouter.score(query)`: lower-cases the text and counts how many keywords match for each domain. Only domains with at least one hit are returned.
- `route_query(query)`: returns the domain with the highest score. `max(scores, key=scores.get)` returns the **first** maximum in insertion order, so ties go to the domain that appears first in `DOMAIN_KEYWORDS` (diabetes, then cancer, then mental health, then cardiac). If there are no hits, it returns `GENERAL`.

Note that the score counts distinct keywords, not occurrences. "heart failure" scores two cardiac hits because both `heart` and `heart failure` are keywords.

### 3.12 `medical_assistant/routing/__init__.py`

Re-exports `DOMAIN_KEYWORDS` and `MedicalAgentRouter`.

### 3.13 `medical_assistant/agents/base.py` — the core RAG class

`BaseMedicalAgent` has class attributes `domain` and `display_name` that subclasses override.

| Method | What it does |
|---|---|
| `__init__(llm, embeddings, memory_window, top_k)` | Uses the injected models, or creates the watsonx ones. Sets `knowledge_base=None` and `conversation_chain=None`. |
| `load_knowledge_base(pdf_paths)` | `load_pdfs` → if no pages, call `create_demo_knowledge_base`. Otherwise `split_into_chunks` → `Chroma.from_documents(chunks, embeddings, collection_name="<domain>_knowledge")`. If that raises, it calls the batch fallback. Returns `(chunk_count, files_loaded)`. |
| `_create_knowledge_base_in_batches(chunks, batch_size=50)` | Creates the Chroma collection from the first batch and calls `add_documents` for the rest. Failed batches are logged and skipped. Returns how many chunks were stored. |
| `create_demo_knowledge_base()` | Embeds the demo documents into `<domain>_demo`. Returns `(count, 1)`. |
| `create_medical_prompt()` | Returns `build_prompt(self.domain)`. |
| `setup_conversation_chain()` | Creates the retriever (`as_retriever(search_type="similarity", search_kwargs={"k": top_k})`), the window memory (`ConversationBufferWindowMemory`, `memory_key="chat_history"`, `output_key="answer"`), and `ConversationalRetrievalChain.from_llm(...)` with `return_source_documents=True`. |
| `is_ready` (property) | True when both the knowledge base and the chain exist. |
| `ask_question(question, chat_history)` | Copies the shared history into the chain's memory, adds a `[<name> Query - time]` prefix, invokes the chain, and returns a dictionary. Any exception becomes an apology dictionary with `confidence="Low"`. |

**Points to explain:**

- `ConversationalRetrievalChain` does two things. If there is chat history, the LLM first rewrites the follow-up as a standalone question. The retriever then searches with that question, and the answer prompt is filled with the chunks.
- `output_key="answer"` tells the memory which output to store, because the chain returns several keys (`answer`, `source_documents`).
- The `chat_history` list is copied (`list(chat_history or [])`). The notebook assigned the same list object, which caused duplicates (section 5).
- `confidence` is "High" when at least 3 sources are returned. This is a heuristic, not a measure of correctness.

### 3.14 `medical_assistant/agents/diabetes.py`, `cancer.py`, `mental_health.py`, `cardiac.py`

Each file defines one subclass with two class attributes:

```python
class DiabeticAgent(BaseMedicalAgent):
    domain = MedicalDomain.DIABETES
    display_name = "Diabetes"
```

Everything else is inherited. To add a specialty, create a new file in the same pattern (see the README's Customization section).

### 3.15 `medical_assistant/agents/__init__.py`

Re-exports the base class and the four agents.

### 3.16 `medical_assistant/orchestrator.py`

`MedicalAssistantOrchestrator` is the main object used by the CLI and by any other code.

| Member | What it does |
|---|---|
| `__init__(agents, router, shared_window)` | If `agents` is not given, creates the four default agents. Creates an empty shared history list. |
| `load_knowledge_bases(pdf_configs)` | For each domain: `agent.load_knowledge_base(paths)` then `agent.setup_conversation_chain()`. Exceptions are logged per agent, so one failure does not stop the others. Returns `(total_chunks, ready_agents)`. |
| `chat(user_input)` | Routes, checks readiness, calls `ask_question`, adds the agent-switch note, saves the exchange, and returns the response dictionary. |
| `_handle_general_query(user_input)` | Formats the help message from `GENERAL_RESPONSE_TEMPLATE`, saves the exchange, and returns it. No LLM call is made. |
| `_remember(user_input, answer)` | Appends a `HumanMessage` and an `AIMessage`, then drops the oldest messages so that at most `2 * shared_window` remain. |
| `get_system_status()` | Counts active agents and reports per-agent flags. |
| `clear_conversation_history()` | Empties the history and resets the counters. |
| `get_conversation_history()` | Returns a copy of the history list. |

The `GENERAL_RESPONSE_TEMPLATE` string is the same text as the notebook's general reply.

### 3.17 `medical_assistant/cli.py`

- `EXAMPLE_QUERIES` and `DEMO_QUERIES`: data used by `demo` and `--demo`.
- `build_orchestrator()`: creates the orchestrator and loads `default_pdf_configs()`.
- `print_response`, `print_status`, `print_examples`: presentation helpers.
- `run_demo(assistant)`: asks each demo query and prints the agent used.
- `interactive_chat(assistant, input_func=input)`: the read–eval–print loop. It takes `input_func` as a parameter, so tests can feed scripted lines instead of a real keyboard. It handles `quit`/`exit`/`q`, `clear`, `status`, `demo`, empty input, Ctrl-C and end-of-file.
- `build_arg_parser()`: `--demo` and `--ask` are mutually exclusive (`add_mutually_exclusive_group`), and `-v` turns on logs.
- `main(argv)`: configures logging to stderr, builds the orchestrator, and catches `RuntimeError` from missing credentials to print a message and return exit code 1.

### 3.18 `tests/` and configuration files

- `pytest.ini`: looks in `tests/` and adds the project root to `sys.path`, so `import medical_assistant` works.
- `tests/conftest.py`: `fake_embeddings` (`FakeEmbeddings`, which returns random vectors with no real meaning) and `fake_llm` (`FakeListLLM`, which returns a fixed string). The tests check plumbing and routing, not answer quality.
- See section 6 for what each test file covers.

---

## 4. Following one question through the code

Question: `"What are the symptoms of diabetes?"` (second turn of a session, after a cardiac question).

1. `cli.interactive_chat` reads the line with `input_func`, strips it, and sees it is not a command.
2. `cli.print_response(assistant.chat(user_input))` calls the orchestrator.
3. `orchestrator.chat`:
   - increments `conversation_count`;
   - `router.route_query` → `score` finds `diabetes` (1 hit) and nothing else → `MedicalDomain.DIABETES`;
   - the diabetes agent `is_ready`, so the code continues;
   - calls `agent.ask_question(text, list(self._history))` where `_history` holds the earlier cardiac exchange.
4. `BaseMedicalAgent.ask_question`:
   - the chain memory is set to a copy of the two earlier messages;
   - the question becomes `"[Diabetes Query - 2026-10-08 10:30] What are the symptoms of diabetes?"`;
   - `chain.invoke(...)`:
     - the LLM condenses the question using the earlier messages;
     - `retriever.invoke(standalone_question)` runs a similarity search in Chroma and returns 5 Documents;
     - the prompt is filled with the text of those 5 chunks, the history, and the question;
     - the LLM generates the answer;
   - the dictionary is returned, with `confidence` set from the number of sources.
5. Back in the orchestrator: the last agent was cardiac, so the switch note is appended to the answer. `_remember` stores the question and the final answer. `last_agent_used` becomes DIABETES. The routing info is added.
6. `print_response` prints the agent name, confidence, answer, number of sources, and routing info.

---

## 5. Known issues in the original notebook and how the package fixes them

These were found while reading the code. Items 1 and 2 were confirmed in the notebook's own saved output.

| # | Issue in the notebook | Effect | Fix in the package |
|---|---|---|---|
| 1 | `self.conversation_chain.memory.chat_memory.messages = chat_history` stores the **same list object**. Adding messages to the agent's memory also changes the orchestrator's history. | Each exchange was stored twice. The saved `get_conversation_history()` output shows repeated AI replies and internal `[Diabetes Query …]` prefixes. | `ask_question` assigns `list(chat_history)`, a copy. Only the orchestrator writes to the shared history. Test: `test_shared_history_has_no_duplicates`. |
| 2 | Keyword routing used substring matching (`keyword in query`). | `mi` matched *mild*, *limit*, *admission*. A question about a mild fever would be routed to cardiology. | Whole-word regex with plural support (`router._compile_keyword`). Test: `test_short_keyword_does_not_match_inside_other_words`. |
| 3 | Notebook used `"skills-network"` as the watsonx project id. | Works only inside the Skills Network lab, which the user does not control. | `WATSONX_PROJECT_ID` and `WATSONX_APIKEY` from `.env`, with a clear error if they are missing. |
| 4 | PDF names in the notebook did not exist (`radiation_therapy.pdf`, `interventional_cardiology.pdf`, `diabetes_textbook_1.pdf`). | Those files were silently skipped. | Config lists the real files in `textbooks/`. A test checks that every configured file exists. |
| 5 | `SHARED memory k=20` was documented as a window but was never applied to the stored list. | The shared list grew without limit. | `_remember` keeps only the last `2 * shared_window` messages. Test: `test_history_is_capped_to_shared_window`. |
| 6 | Notebook called the chain with `chain({...})` and imported the deprecated `langchain.vectorstores.Chroma`. | Deprecation warnings; may break on a later LangChain version. | `chain.invoke(...)` and `langchain_community.vectorstores.Chroma`. |
| 7 | Chroma telemetry error printed on every query. | Noise in the output. | `ANONYMIZED_TELEMETRY=False` set before import. |
| 8 | `ibm-watson-machine-learning` and `langchainhub`, `langchain_experimental` installed but unused (or only partly used). | Heavier install, more conflicts. | Only the packages that are used are pinned. `langchain-ibm` replaces the legacy WML wrapper. |
| 9 | The automatic demo check (`if total_chunks == 0`) runs only when no chunks at all were counted. Demo chunks are counted in `total_chunks`, so the check almost never fires. | The notebook's "auto-start demo" is effectively dead code. | The demo is an explicit command (`--demo`), not an automatic fallback. |

**Still open (not fixed, worth mentioning in an interview):**

- `TRUNCATE_INPUT_TOKENS: 3` is kept from the notebook. It is unusually low and should be checked against the watsonx documentation.
- The Chroma index is in memory and rebuilt on every start, which uses the embedding quota every time.
- Keyword lists are hand-maintained.
- `confidence` is based on the number of chunks, not on answer quality.

---

## 6. Testing

Run all tests from the project root:

```bash
python -m pytest
```

| File | What it proves |
|---|---|
| `test_router.py` | Ten queries route to the expected domain, including plural forms and a general query. Also checks that short keywords do not match inside other words, that the domain with the most hits wins, and that ties go to the first domain. |
| `test_knowledge.py` | Each specialty has three demo documents with the right metadata. General has none. A missing PDF is skipped, not raised. Chunks respect the size limit. Prompt templates expose the three variables. Every configured textbook exists (catches config drift). |
| `test_orchestrator.py` | Full chat flow with real agents using fake models: routing, answering, the general reply, no duplicate history, agent-switch notice, history cap, clear, and an unready agent. |
| `test_cli.py` | The command loop: `quit`, `status` and `clear`, empty input, Ctrl-C, and argument validation. |

**What the tests do not cover:** the real watsonx calls and the answer quality. Those need credentials and a manual check. The package was also run once against all seven real textbooks with the fake embedding model. That run loaded every file and produced 8,854 chunks without errors.

---

## 7. Interview preparation

### 7.1 Your 60-second summary

> "I turned a research notebook into a Python package. It answers medical questions with four specialist RAG agents: diabetes, oncology, psychiatry and cardiology. A keyword router picks the agent. Each agent loads its own textbook PDFs, splits them into 1,000-character chunks with overlap, embeds them with IBM's Slate model into a Chroma vector store, and retrieves the top five chunks for each question. Those chunks, the conversation history, and a specialty prompt go to Mistral Large on watsonx.ai with a low temperature. Shared memory lets the conversation move between specialists. I also fixed bugs in the notebook, such as duplicated chat history and substring routing, and added tests that run offline."

### 7.2 What you should be able to do

- Draw the architecture from memory (explanation.md, section 5).
- Explain each stage of the RAG pipeline and why each parameter has its value.
- Walk through the code path for one question (section 4).
- Explain the bugs you found and how you fixed them (section 5).
- Explain why HDFS is or is not used, and what would change at scale (explanation.md, section 9).
- Run the project: install, configure `.env`, run `python main.py --ask ...` and `python -m pytest`.
- Say what you would do next (section 10 of explanation.md).

---

## 8. Concepts you must be able to explain

| Concept | One-line explanation | Where it is in the code |
|---|---|---|
| **RAG** | Retrieve relevant text first, then generate with it as context, which reduces hallucination and makes answers traceable. | `agents/base.py` |
| **Embedding** | A fixed-length vector for a piece of text; similar meaning → nearby vectors. | `llm.create_embeddings`, Chroma |
| **Vector similarity search** | Find the stored vectors closest to the query vector (Chroma's default metric is L2 distance unless set otherwise). | `as_retriever(search_type="similarity")` |
| **Chunking with overlap** | Split long text into pieces; overlap keeps facts that cross a boundary. | `knowledge/pdf_loader.split_into_chunks` |
| **Recursive text splitting** | Try paragraph, line, sentence, then word separators, so chunks break at natural points. | `RecursiveCharacterTextSplitter` |
| **Prompt template** | A string with placeholders filled at run time. | `prompts.py` |
| **Temperature / top-p** | Control randomness. Low temperature = more deterministic output. | `config.WatsonxSettings` |
| **Conversational memory** | Stores recent turns and adds them to the next prompt. A window limits how many. | `ConversationBufferWindowMemory` |
| **Condense-question step** | Follow-up questions are rewritten into standalone questions before retrieval. | `ConversationalRetrievalChain` |
| **Keyword routing** | Score each domain by keyword matches and pick the best. | `routing/router.py` |
| **Dependency injection** | Pass collaborators in, instead of creating them inside the class, to make testing possible. | `BaseMedicalAgent.__init__` |
| **Fake objects in tests** | `FakeListLLM` and `FakeEmbeddings` stand in for the real services. | `tests/conftest.py` |
| **Graceful degradation** | Missing PDFs, bad credentials and API errors are handled without crashing. | `pdf_loader`, `cli.main`, `ask_question` |
| **Regular expressions with lookarounds** | `(?<![a-z0-9])` and `(?![a-z0-9])` enforce whole-word matching. | `router._compile_keyword` |
| **Enum** | A closed set of named constants (`MedicalDomain`). | `domains.py` |
| **Frozen dataclass** | Immutable settings objects. | `config.py` |
| **Environment variables and `.env`** | Keep secrets out of code. | `config.py`, `.env.example` |
| **Virtual environments and pinning** | Reproducible installs. | `requirements.txt` |
| **Unit vs. integration tests** | Unit tests check one piece (router); the orchestrator test checks several pieces together with fakes. | `tests/` |

---

## 9. Likely interview questions with answers

**Architecture and design**

1. **Why RAG and not fine-tuning?** The knowledge changes (new guidelines), and RAG lets you swap PDFs without retraining. Answers can cite the passages used. Fine-tuning would need labelled data and compute, and would still not provide sources.
2. **Why one vector collection per specialty?** It keeps retrieval focused. A diabetes question cannot be answered with oncology passages, and each collection can be rebuilt on its own.
3. **Why keyword routing instead of an LLM router?** It is fast, deterministic, free, and easy to test. The cost is poorer handling of synonyms. The next step would be to combine keywords with an embedding-based classifier.
4. **How does the orchestrator differ from the agents?** The orchestrator decides *who* answers and manages shared state. The agents decide *how* to answer, using their own knowledge.
5. **Why does `BaseMedicalAgent` exist?** The four specialties share the same pipeline. The base class holds it once, and each subclass only sets the domain, name and (through `prompts.py`) the prompt.
6. **How would you add a fifth specialty?** Add a `MedicalDomain` value, a prompt template, keywords, a PDF list, a subclass, and register it in the orchestrator. Add router and loader tests.

**RAG and retrieval**

7. **Why 1,000 characters with 200 overlap?** It keeps each chunk to about a paragraph, which is precise enough for retrieval and short enough to fit several chunks in the prompt. The overlap keeps a sentence that crosses a boundary whole in at least one chunk.
8. **Why k = 5?** Five chunks give enough evidence without making the prompt too long for the 512-token answer budget. I would tune it with a set of test questions.
9. **What is `TRUNCATE_INPUT_TOKENS: 3` and is it correct?** It is the setting from the notebook that controls truncation of embedding input. A value of 3 is unusually low, so I would check it against the watsonx embedding documentation before relying on it.
10. **How do you know the answers are correct?** Honestly, the project does not yet measure this. It shows source counts, and the prompt tells the model to rely on the literature. A proper evaluation would use a labelled question set and check whether the answer matches the cited passage.
11. **What happens if no chunks are relevant?** The retriever still returns the closest five, so the model may answer from weak context. A score threshold would be the fix.

**Memory and conversation**

12. **Why two memories?** The shared history gives all agents the conversation. The per-agent window limits the prompt size for each chain.
13. **What bug did you find in the memory?** The agent's memory and the shared history referred to the same list, so each exchange was stored twice and internal prefixes leaked into history. The notebook's saved output shows it. The fix is to copy the list.
14. **What is the condense-question step?** For a follow-up such as "and in children?", the LLM first rewrites it into a full question using the history. Retrieval then works on the full question.

**Engineering and quality**

15. **How is configuration handled?** All settings are in `config.py`, secrets come from `.env` and environment variables, and the file `.env` is ignored by Git.
16. **How do you test without calling watsonx?** Dependency injection. The tests pass `FakeListLLM` and `FakeEmbeddings`, so the whole RAG pipeline runs locally.
17. **What happens if a PDF is corrupt or missing?** The loader logs it and skips it. An agent with no readable file uses demo content, and the rest of the system keeps working.
18. **What are the limits of the current design?** In-memory index rebuilt on each start, keyword-only routing, no answer evaluation, one process and no concurrency.
19. **How would you deploy it?** Persist the index, move the orchestrator behind an HTTP API (for example FastAPI), keep sessions in a store such as Redis, containerise it, and keep the secrets in a secret manager.
20. **How would it scale?** Embedding is the slow part. Batch and cache embeddings, persist the vector store, and store the raw and chunked documents in object storage or HDFS (see explanation.md, section 9).

**HDFS and big data**

21. **Is HDFS used in this project?** No. The data is about 38 MB of PDFs on a local disk, so a cluster would add cost without benefit. Section 9 of explanation.md maps the concepts and says where HDFS would help.
22. **What is the role of the NameNode and the DataNodes?** The NameNode holds the namespace and block locations and is the arbitrator for metadata. DataNodes store the blocks and serve reads and writes. User data does not pass through the NameNode.
23. **What do the default HDFS settings mean?** 128 MB blocks and three replicas. The replicas are spread across racks for reliability.
24. **Why is HDFS not suitable for low-latency chat?** It is designed for high-throughput batch reading of large files. A chat needs an index that answers in milliseconds. HDFS is good for storing and processing the source documents, not for serving individual queries.

**Python and code**

25. **Why `from __future__ import annotations`?** It delays evaluation of type hints, so forward references and modern syntax work on older Python versions.
26. **What is `frozen=True` on a dataclass?** The object cannot be changed after creation, which prevents accidental changes to settings.
27. **Why `setdefault` for the telemetry variable?** It sets the value only if the user has not already set it, so a user can turn telemetry on explicitly.
28. **Why is `max(scores, key=scores.get)` used?** It returns the key with the highest value. When there is a tie, it returns the first one encountered.
29. **Why do the tests use `pythonpath = .` in `pytest.ini`?** The package sits in the project root. That setting makes `import medical_assistant` work without installing the package.

---

## 10. A 5-minute demo script

1. **Show the structure** (30 s): `tree -L 2` or the README's project structure. Mention that the notebook is kept under `notebooks/`.
2. **Show the configuration** (30 s): `config.py` → `PDF_CONFIGS` and `WatsonxSettings`. Show `.env.example`. Do not show a real key.
3. **Run the tests** (30 s): `python -m pytest`. Point out that they pass without any credentials.
4. **Routing** (60 s): in Python, call `MedicalAgentRouter().route_query(...)` on "What is a mild fever?" (general) and "What's the difference between STEMI and NSTEMI?" (cardiac). Explain why `mi` does not match "mild".
5. **Live question** (90 s, with credentials): `python main.py --ask "What are the criteria for Type 2 diabetes?"`. Point out the agent name, the confidence and the number of source chunks.
6. **Follow-up** (60 s): in `python main.py`, ask a diabetes question, then "and how is it treated?", then a cardiac question, then `status`. Show the agent-switch message.
7. **Architecture and bug story** (60 s): open `explanation.md` section 5 and `details.md` section 5. Explain the duplicate-history bug and how you found it in the notebook output.

If credentials are not available, run steps 1–4 and 7, and say that the live calls need a watsonx.ai project.

---

## Known issues in the original notebook and how the package fixes them

This heading is linked from the README. The full table is in [section 5](#5-known-issues-in-the-original-notebook-and-how-the-package-fixes-them).

---

*This document describes the code in the repository. It is for learning and interview preparation.*
