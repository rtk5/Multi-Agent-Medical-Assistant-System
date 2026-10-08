# 🏥 Multi-Agent Medical Assistant System

Welcome to the **Multi-Agent Medical Assistant** — a modular Python system designed for accurate, evidence-based support in medical diagnosis, treatment, and education.  
This system combines **state-of-the-art LLMs (IBM watsonx.ai, Mistral Large)** with domain-specialized agents and integrates **PDF knowledge bases** for practical, clinical use.

> 📚 New here? Read **[explanation.md](explanation.md)** for the architecture and end-to-end pipeline, and **[details.md](details.md)** for a file-by-file code walkthrough and interview preparation notes.

---

## ✨ Features

### Multi-Domain Coverage
- Specialized agents for:
  - Diabetes  
  - Cancer/Oncology  
  - Mental Health/Psychiatry  
  - Cardiac/Cardiovascular  

### Automated Routing
- Intelligent query router that sends questions to the correct medical domain agent based on keywords (whole-word matching, so `mi` no longer fires inside words like *mild*).

### Custom Knowledge Bases
- Load textbooks, guidelines, or literature (PDFs) for each specialty from the `textbooks/` folder.

### Conversational Memory
- Remembers previous exchanges to support real **“case discussion”–style conversations**.

### Evidence-Based, Safe Responses
- Each agent follows strict clinical guidelines and returns the source chunks it used.

### Demo Mode
- If a specialty's PDFs are missing or unreadable, built-in demo content lets you test that agent without extra setup.

---

## 📁 Project Structure

```text
Multi-Agent-Medical-Assistant-System/
├── main.py                       # Command-line entry point
├── requirements.txt              # Runtime dependencies (pinned)
├── requirements-dev.txt          # Test dependencies
├── .env.example                  # Template for watsonx.ai credentials
├── pytest.ini                    # Test configuration
├── medical_assistant/            # The Python package (all application code)
│   ├── __init__.py               # Package exports + telemetry switch
│   ├── config.py                 # Settings, PDF file list, paths
│   ├── domains.py                # MedicalDomain enum
│   ├── llm.py                    # watsonx.ai LLM and embedding factories
│   ├── prompts.py                # Specialty prompt templates
│   ├── cli.py                    # Interactive chat, --demo and --ask
│   ├── orchestrator.py           # Routes questions, shared memory, status
│   ├── agents/                   # One RAG agent per specialty
│   │   ├── base.py               #   BaseMedicalAgent (ingestion, retrieval, chain)
│   │   ├── diabetes.py           #   DiabeticAgent
│   │   ├── cancer.py             #   CancerAgent
│   │   ├── mental_health.py      #   MentalHealthAgent
│   │   └── cardiac.py            #   CardiacAgent
│   ├── knowledge/                # Knowledge-base ingestion
│   │   ├── pdf_loader.py         #   PDF loading + chunking
│   │   ├── demo_loader.py        #   Demo content -> Documents
│   │   └── demo_content.py       #   Built-in demo text
│   └── routing/
│       └── router.py             # Keyword-based query router
├── tests/                        # Offline unit tests (no watsonx calls)
├── textbooks/                    # Medical PDFs used by the agents
├── notebooks/                    # Original Jupyter notebooks (reference only)
├── explanation.md                # Architecture and pipeline
└── details.md                    # Code walkthrough and interview guide
```

---

## ⚙️ Installation

### Prerequisites

| Requirement | Why |
|---|---|
| **Python 3.10 or 3.11** | The pinned `chromadb==0.4.24` does not support Python 3.12+. |
| **IBM Cloud account with a watsonx.ai project** | Provides the Mistral Large LLM and the embedding model. |
| **Git** | To clone the repository. |

### Step-by-step

1. **Clone the repository**
   ```bash
   git clone https://github.com/rtk5/Multi-Agent-Medical-Assistant-System.git
   cd Multi-Agent-Medical-Assistant-System
   ```

2. **Create and activate a virtual environment**
   ```bash
   # macOS / Linux
   python3.11 -m venv .venv
   source .venv/bin/activate

   # Windows (PowerShell)
   py -3.11 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install the requirements**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   For running the tests as well, also install the dev requirements:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure your watsonx.ai credentials**
   ```bash
   cp .env.example .env        # Windows: copy .env.example .env
   ```
   Then edit `.env` and set:

   | Variable | Where to find it |
   |---|---|
   | `WATSONX_URL` | Your region's endpoint, e.g. `https://us-south.ml.cloud.ibm.com` |
   | `WATSONX_PROJECT_ID` | watsonx.ai project → *Manage* → *General* → Project ID |
   | `WATSONX_APIKEY` | IBM Cloud → *Manage* → *Access (IAM)* → *API keys* |

   > ⚠️ Never commit `.env`. It is already listed in `.gitignore`.

5. **Add or check your medical PDFs**
   - The PDFs the agents read are listed in `medical_assistant/config.py` under `PDF_CONFIGS`.
   - Put the files in the `textbooks/` folder. A missing file is skipped with a warning, and an agent with no readable PDFs uses demo content.
   - To use different documents, edit `PDF_CONFIGS` (paths are relative to `textbooks/`).

6. **Check the installation (optional, offline)**
   ```bash
   python -m pytest
   ```
   The tests use fake models, so they run without credentials or internet access.

---

## 🚀 Usage

### Interactive chat (recommended)
```bash
python main.py
```

Inside the chat:

| Input | Action |
|---|---|
| any medical question | routed to the right specialist and answered |
| `status` | active agents, memory size, last agent used |
| `demo` | list example questions |
| `clear` | reset the conversation history |
| `quit`, `exit`, `q` | leave the chat |

### One-shot question
```bash
python main.py --ask "What are the criteria for Type 2 diabetes?"
```

### Scripted demo
```bash
python main.py --demo
```

Add `-v` to any command to see PDF loading and debug logs.

### Programmatic API
```python
from medical_assistant.cli import build_orchestrator

assistant = build_orchestrator()          # loads all PDFs (or demo content)
response = assistant.chat("What are the criteria for Type 2 diabetes?")

print(response["agent"])                  # e.g. "Diabetes"
print(response["answer"])
print(len(response["source_documents"]))  # number of textbook chunks used
```

---

## 💡 Example Queries

You can ask questions such as:

- “What are the diagnostic criteria for Type 2 diabetes?”  
- “How is breast cancer staged?”  
- “What medications treat major depression?”  
- “What are the current hypertension guidelines?”  
- “What's the difference between STEMI and NSTEMI?”

---

## 🏗️ Architecture

| Module | Description |
|---|---|
| **BaseMedicalAgent** (`agents/base.py`) | Shared RAG pipeline: load PDFs, build the vector store, retrieve, answer |
| **DiabeticAgent / CancerAgent / MentalHealthAgent / CardiacAgent** | Specialty agents: set the domain, name and prompt |
| **MedicalAgentRouter** (`routing/router.py`) | Scores each question against domain keywords and picks the best domain |
| **MedicalAssistantOrchestrator** (`orchestrator.py`) | Owns the agents, routes each message, keeps shared memory and status |
| **PDF Knowledge Loader** (`knowledge/`) | Reads PDFs, adds metadata, splits into 1,000-character chunks |
| **LLM & embeddings** (`llm.py`) | watsonx.ai Mistral Large and `slate-125m-english-rtrvr` |
| **CLI** (`cli.py`, `main.py`) | Terminal chat, `--ask` and `--demo` modes |

For the full picture, see [explanation.md](explanation.md).

---

## 🔧 Customization

- **Add more agents**: subclass `BaseMedicalAgent` (see `agents/cardiac.py` for a minimal example), add a `MedicalDomain` value, a prompt in `prompts.py`, keywords in `routing/router.py`, and register the agent in `MedicalAssistantOrchestrator`.
- **Update knowledge**: change `PDF_CONFIGS` in `medical_assistant/config.py`.
- **Tune the LLM**: change `WatsonxSettings` in `medical_assistant/config.py` (`temperature`, `max_new_tokens`, `top_p`, `repetition_penalty`).
- **Tune retrieval and memory**: `ChunkingSettings`, `RetrievalSettings` and `MemorySettings` in the same file.

---

## 🧪 Running the Tests

```bash
python -m pytest
```

The suite covers routing, PDF loading and chunking, prompt templates, the orchestrator's memory and status logic, and the CLI loop. It uses fake LLM and embedding models, so it never calls watsonx.ai.

---

## 🛠️ Troubleshooting

| Symptom | Fix |
|---|---|
| `Missing watsonx.ai settings: WATSONX_PROJECT_ID, WATSONX_APIKEY` | Create `.env` from `.env.example` and fill in the values. |
| `429 ... usage quota` | The watsonx.ai free quota for the day is used up. Wait for it to reset or use a paid plan. |
| `File not found, skipping: ...textbooks/...pdf` | Put the PDF in `textbooks/` or fix the name in `PDF_CONFIGS`. |
| Dependency install fails (chromadb, onnxruntime, ibm packages) | Check `python --version`. Use Python 3.10 or 3.11; the pinned `chromadb==0.4.24` does not support Python 3.12+. |
| `ibm-watsonx-ai==1.0.4` shows as yanked | This pin matches the notebook. The exact pin still installs. |
| Slow first start | Every PDF page is embedded on each start, because the vector store lives in memory. The Cancer textbooks take the longest. |

---

## 📓 Original Notebooks

The original single-file versions are kept in `notebooks/` for reference. The package in `medical_assistant/` is the maintained version. It fixes a few issues in the notebook, described in [details.md](details.md#known-issues-in-the-original-notebook-and-how-the-package-fixes-them).

---

## 📝 Attribution

Built using:  
- **IBM watsonx.ai** (Mistral Large, Slate embeddings)  
- **LangChain**  
- **Chroma vector stores**  
- **pypdf** for PDF parsing  

Developed during a C3I summer internship at PES University for Cellstrat.ai (June–July 2025). See `RITHVIK_RAJESH_MATTA_C3I_FINAL_REPORT.pdf`.

⚠️ For academic, educational, and research use only. This system is **not** a medical device and does not replace a qualified clinician.

---

✅ **Get started today** — and bring high-quality medical answers to your research, engineering, or education workflow!
