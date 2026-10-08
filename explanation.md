# Multi-Agent Medical Assistant — Project Explanation

This document explains **what the project is**, **how it is architected**, **how a question flows through the system step by step**, and **how the design compares with a real Hadoop Distributed File System (HDFS) deployment**.

For a file-by-file code walkthrough and interview preparation, read [details.md](details.md). For installation and usage, read [README.md](README.md).

---

## Table of Contents

1. [What the project is](#1-what-the-project-is)
2. [Background and context](#2-background-and-context)
3. [Goals, scope and non-goals](#3-goals-scope-and-non-goals)
4. [Key concepts in plain language](#4-key-concepts-in-plain-language)
5. [Architecture](#5-architecture)
6. [The end-to-end pipeline](#6-the-end-to-end-pipeline)
7. [Design decisions and trade-offs](#7-design-decisions-and-trade-offs)
8. [What changed from the notebook](#8-what-changed-from-the-notebook)
9. [Comparison with a real HDFS deployment](#9-comparison-with-a-real-hdfs-deployment)
10. [Limitations and future work](#10-limitations-and-future-work)

---

## 1. What the project is

The **Multi-Agent Medical Assistant** is a Python application that answers medical questions in a chat. It is built from several **specialist agents**, one per medical domain:

| Agent | Domain | Knowledge source (in `textbooks/`) |
|---|---|---|
| `DiabeticAgent` | Diabetes and endocrinology | `diabetes_guidelines.pdf`, `insulin_therapy.pdf` |
| `CancerAgent` | Cancer / oncology | `chemotherapy_protocols.pdf`, `oncology_textbook.pdf` |
| `MentalHealthAgent` | Psychiatry / mental health | `psychiatry_textbook.pdf` |
| `CardiacAgent` | Cardiology / cardiovascular | `heart_failure_guidelines.pdf`, `cardiology_textbook.pdf` |

A question such as *"What are the criteria for Type 2 diabetes?"* is sent to the diabetes agent. That agent searches its own textbooks for relevant passages, gives them to a large language model (LLM), and returns an answer together with the number of source passages it used.

The original work was a Jupyter notebook (`notebooks/1_all_agents-Copy1.ipynb`, plus a near-identical copy). It has been turned into a normal multi-folder Python package (`medical_assistant/`) with tests, configuration, and a command-line interface.

---

## 2. Background and context

- The project was built during a **C3I (Centre for Computational Intelligence and Innovation) summer internship at PES University, June–July 2025**, for **Cellstrat.ai**.
- The original brief (from the slide deck in the repository) was to create a **Diabetic Agent** for Cellstrat's *CellBot* platform. When CellBot detects a diabetes conversation, it should hand the question to a specialist that knows treatment protocols, diagnosis insights, and management workflows. Other agents (cancer, cardiac, mental health) were planned as alternatives.
- The target users are **medical students and doctors**.
- The internship report describes the system as **Retrieval-Augmented Generation (RAG)** with no fine-tuning. The report also states that query routing is done by keyword matching and that the model is IBM watsonx.ai `mistralai/mistral-large`, with `ibm/slate-125m-english-rtrvr` embeddings (768 dimensions).

---

## 3. Goals, scope and non-goals

**Goals**

- Answer domain questions with answers grounded in the supplied textbooks and guidelines.
- Route each question automatically to the right specialist.
- Keep conversation context, so follow-up questions work.
- Show how many source passages supported each answer.
- Fail gracefully: missing PDFs, missing credentials, or API errors should not crash the chat.

**Non-goals**

- It is **not** a diagnostic device and gives no patient-specific treatment decisions.
- It does **not** train or fine-tune any model.
- It does **not** store patient data. Conversation memory lives only in RAM for the session.
- It is **not** a distributed system. It runs on one machine and does not use HDFS (see [section 9](#9-comparison-with-a-real-hdfs-deployment)).

---

## 4. Key concepts in plain language

| Term | Meaning in this project |
|---|---|
| **LLM** | The large language model that writes the answer. Here, Mistral Large hosted on watsonx.ai. |
| **Embedding** | A list of numbers (a vector) that represents the meaning of a piece of text. Similar texts get similar vectors. |
| **Chunk** | A piece of a textbook page, at most 1,000 characters, with a 200-character overlap with its neighbour. |
| **Vector store** | A database that stores chunk vectors and finds the nearest ones to a query vector. Here, **Chroma**. |
| **RAG** | Retrieval-Augmented Generation: fetch relevant chunks first, then ask the LLM to answer using only those chunks as context. |
| **Prompt template** | The instruction text, with placeholders for the retrieved context, chat history and question. |
| **Memory** | The recent conversation turns that are included in each new prompt. |
| **Routing** | Choosing which specialist agent handles a question. |
| **Temperature** | How random the LLM output is. Set to 0.1 here so answers are more deterministic and factual. |

---

## 5. Architecture

### 5.1 Component diagram

```text
                        ┌──────────────────────────────┐
  user question ───────▶│   CLI  (main.py / cli.py)    │
                        └──────────────┬───────────────┘
                                       │ chat(text)
                        ┌──────────────▼───────────────┐
                        │  MedicalAssistantOrchestrator │
                        │  • shared chat history        │
                        │  • agent-switch notices       │
                        │  • status / clear             │
                        └───────┬──────────────┬────────┘
                    route(text) │              │ ask_question(text, history)
                ┌───────────────▼──┐     ┌─────▼─────────────────────────────┐
                │ MedicalAgent-   │     │  Specialist agent (×4)            │
                │ Router          │     │  BaseMedicalAgent subclass        │
                │ keyword scoring │     │                                   │
                └─────────────────┘     │  ConversationalRetrievalChain     │
                                        │   ├─ Retriever (Chroma, top-k=5)  │
                                        │   ├─ Memory (window of 10 turns)  │
                                        │   ├─ Prompt (specialty template)  │
                                        │   └─ LLM (watsonx Mistral Large)  │
                                        └──────┬────────────────┬───────────┘
                                               │                │
                            ┌──────────────────▼──┐   ┌─────────▼──────────────┐
                            │ Chroma vector store │   │ watsonx.ai             │
                            │ one collection per  │   │ • LLM (generation)     │
                            │ specialty (in RAM)  │   │ • Embeddings (slate)   │
                            └──────────▲──────────┘   └────────────────────────┘
                                       │ build at start-up
                            ┌──────────┴─────────────────────────────────────┐
                            │ Ingestion: PDFs (textbooks/) → PyPDFLoader     │
                            │ → metadata → RecursiveCharacterTextSplitter    │
                            │ (fallback: built-in demo content)              │
                            └────────────────────────────────────────────────┘
```

### 5.2 Modules and responsibilities

| Layer | Module | Responsibility |
|---|---|---|
| Entry points | `main.py`, `medical_assistant/cli.py` | Parse arguments, run the chat loop, `--ask`, `--demo`. |
| Orchestration | `medical_assistant/orchestrator.py` | Owns the agents, routes each message, keeps the shared history, reports status. |
| Routing | `medical_assistant/routing/router.py` | Scores a question against keyword lists and returns a `MedicalDomain`. |
| Agents | `medical_assistant/agents/*.py` | RAG pipeline per specialty. `base.py` holds the shared logic; the four subclasses set the domain and name. |
| Ingestion | `medical_assistant/knowledge/*.py` | Load PDFs, attach metadata, chunk, and provide demo documents. |
| Prompts | `medical_assistant/prompts.py` | One template per specialty, with the same three placeholders. |
| Models | `medical_assistant/llm.py` | Creates the watsonx LLM and embedding objects from settings. |
| Configuration | `medical_assistant/config.py`, `domains.py` | Model names, LLM parameters, chunk sizes, memory windows, PDF list, domain enum. |

### 5.3 Dependency direction

Dependencies point inwards: the CLI depends on the orchestrator, the orchestrator depends on agents and the router, agents depend on knowledge, prompts and models, and everything depends on `config` and `domains`. Nothing in the lower layers imports the CLI. This keeps the core testable without a terminal or network.

### 5.4 Dependency injection

`BaseMedicalAgent` and `MedicalAssistantOrchestrator` accept their collaborators in the constructor (`llm`, `embeddings`, `agents`, `router`). In production they default to the watsonx objects. In the tests they are replaced by LangChain's fake LLM and fake embeddings, so the full RAG flow can run offline.

---

## 6. The end-to-end pipeline

The pipeline has three phases: **start-up (ingestion)**, **question answering**, and **memory update**.

### 6.1 Phase 0 — Start-up and configuration

1. `medical_assistant/__init__.py` sets `ANONYMIZED_TELEMETRY=False` before Chroma is imported, to stop a telemetry error from appearing on every query.
2. `config.py` loads `.env` with `python-dotenv` and reads `WATSONX_URL`, `WATSONX_PROJECT_ID` and `WATSONX_APIKEY`.
3. `cli.build_orchestrator()` creates the `MedicalAssistantOrchestrator`. This creates the router and the four agents. Each agent creates its watsonx LLM and embedding client (`llm.py`), which fails with a clear message if the credentials are missing.
4. `load_knowledge_bases(default_pdf_configs())` runs ingestion for each agent (phase 1).

### 6.2 Phase 1 — Ingestion (done once per start-up)

For each specialty, in `BaseMedicalAgent.load_knowledge_base`:

| Step | What happens | Code |
|---|---|---|
| 1. Read | Each configured PDF is read page by page with `PyPDFLoader`. Missing, unreadable, empty or corrupt files are logged and skipped. | `knowledge/pdf_loader.load_pdfs` |
| 2. Tag | Every page gets metadata: `domain`, `filename`, `source_path`, `source_textbook`. These are later shown as citations. | `load_pdfs` |
| 3. Chunk | Pages are split into chunks of at most **1,000 characters** with **200 characters of overlap**. The splitter prefers paragraph breaks, then line breaks, then sentences, then words. | `knowledge/pdf_loader.split_into_chunks` |
| 4. Embed and index | Each chunk is sent to the watsonx **slate-125m** embedding model and stored in a Chroma collection named `<domain>_knowledge`. | `BaseMedicalAgent.load_knowledge_base` |
| 5. Retry on failure | If the bulk embedding call fails, chunks are embedded in batches of 50. | `_create_knowledge_base_in_batches` |
| 6. Fallback | If no PDF can be read at all, the agent embeds built-in demo sections into `<domain>_demo`. | `create_demo_knowledge_base` |
| 7. Chain | `setup_conversation_chain` builds a `ConversationalRetrievalChain` that uses a Chroma retriever (`similarity`, `k=5`), a 10-turn window memory and the specialty prompt. | `setup_conversation_chain` |

After ingestion, each agent reports `is_ready = True` when it has both a knowledge base and a chain.

Sizes from the textbooks in this repository, measured with the current loader and chunker:

| Specialty | Files | Pages | Chunks |
|---|---|---|---|
| Diabetes | 2 | 270 | 709 |
| Cancer | 2 | 1,373 | 5,754 |
| Mental health | 1 | 273 | 1,119 |
| Cardiac | 2 | 166 | 1,272 |

### 6.3 Phase 2 — Answering a question

Every user message goes through `MedicalAssistantOrchestrator.chat()`:

```text
user text
   │
   ▼
[1] router.route_query(text)        keyword scores per domain
   │
   ├── GENERAL (no keyword hit) ──▶ canned help message (no LLM call)
   │
   ▼ specialist domain
[2] agent.is_ready?                 if not → "specialist not available" message
   │ yes
   ▼
[3] agent.ask_question(text, shared_history)
      a. copy shared history into the agent's memory
      b. prefix the question: "[Diabetes Query - 2025-07-30 17:20] …"
      c. ConversationalRetrievalChain:
           i.   (if history exists) LLM rewrites the question as a standalone question
           ii.  retriever returns the top 5 chunks by vector similarity
           iii. the specialty prompt is filled with {context}, {chat_history}, {question}
           iv.  LLM generates the answer (temperature 0.1, max 512 tokens)
      d. return {answer, source_documents, confidence, domain, agent}
   │
   ▼
[4] if the agent changed since last turn → append "Switched to … specialist" note
   │
   ▼
[5] remember(user text, answer) in shared history   (phase 3)
   │
   ▼
[6] return the response; the CLI prints agent, confidence, answer, source count
```

**Confidence** is a simple heuristic: `High` when at least 3 source chunks were retrieved, otherwise `Medium`. If the chain raises an error, the agent returns an apology with confidence `Low` rather than crashing the chat.

**Routing example.** For *"Can diabetes increase the risk of heart disease?"*, the diabetes keyword `diabetes` and the cardiac keyword `heart` each match once. The tie goes to the domain listed first, so the question goes to the diabetes agent. For *"What's the difference between STEMI and NSTEMI?"*, the cardiac keywords `stemi` and `nstemi` match, so it goes to the cardiac agent.

### 6.4 Phase 3 — Memory

Two memories work together:

| Memory | Owner | Size | Purpose |
|---|---|---|---|
| **Shared history** | Orchestrator (`_history` list) | last **20 exchanges** (40 messages) | Gives every agent the whole conversation, so the cardiac agent can answer "what about its treatment?" after a diabetes question. |
| **Agent window memory** | Each agent's `ConversationBufferWindowMemory` | last **10 exchanges** | Limits what a single chain puts into its prompt. It is refilled from the shared history on every call. |

Only the user's question and the final answer are written to the shared history. The internal `[Diabetes Query …]` prefix and any retrieved context are not stored.

### 6.5 Housekeeping commands

- `status` calls `get_system_status()` and prints how many agents are active, how many turns have happened, which agent answered last, and how many messages are in memory.
- `clear` calls `clear_conversation_history()`, which empties the shared history and resets the counters.

---

## 7. Design decisions and trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| **RAG instead of fine-tuning** | Textbooks can be swapped without retraining. Answers can be traced to passages. | Answer quality depends on retrieval quality and on the chunking. |
| **One vector collection per specialty** | Each agent searches only its own books, so a diabetes question is not answered from oncology text. | Four collections must be built and kept in sync. |
| **Keyword routing instead of an LLM router** | Fast, free, deterministic and easy to explain. | It misses synonyms ("sugar disease") and needs manual keyword upkeep. |
| **Whole-word keyword matching** | Stops false routes such as *mild* → cardiac via `mi`. | Plural handling is limited to `s`/`es`. |
| **Temperature 0.1, top-p 0.9, repetition penalty 1.1** | Favours factual, repeatable output for a medical setting. | Less varied wording. |
| **Chunks of 1,000 characters with 200 overlap** | Large enough for a whole paragraph of context, small enough for precise retrieval. Overlap avoids cutting a fact in half. | Overlap stores some text twice, which increases index size. |
| **Top-k = 5** | Enough evidence for an answer without filling the prompt. | Very long answers may need more context. |
| **In-memory Chroma** | Simple, no database to install. | The index is rebuilt on every start-up (see [section 10](#10-limitations-and-future-work)). |
| **Graceful fallbacks** (missing PDFs → demo content; LLM error → apology) | The app can still be demonstrated on a laptop without the full textbook set. | Demo content is tiny and must not be treated as clinical evidence. |
| **Dependency injection for models** | Tests run offline and quickly. | Slightly more constructor parameters. |

---

## 8. What changed from the notebook

The logic was kept the same wherever it was correct. These are the deliberate changes:

| Area | Notebook | Package |
|---|---|---|
| Layout | One `.ipynb` with ~1,200 lines of code | Package with 15 modules, plus tests and docs |
| Secrets | Hard-coded `project_id = "skills-network"` (a Skills Network lab project) | Read from `.env` (`WATSONX_PROJECT_ID`, `WATSONX_APIKEY`); validated with a clear error |
| PDF paths | Relative names that did not exist (`radiation_therapy.pdf`, `interventional_cardiology.pdf`, `diabetes_textbook_1.pdf`) | Points to the PDFs actually in `textbooks/`; missing files are still skipped |
| Dependencies | Installed with `!pip install` inside the notebook, including the legacy `ibm-watson-machine-learning` package | Pinned in `requirements.txt`; uses `langchain-ibm`'s `WatsonxLLM`, which removes the legacy package |
| Shared history | The agent's memory was assigned the orchestrator's list **by reference**, so the same exchange was written twice and the internal prefix leaked into history (confirmed in the notebook's saved output) | The agent receives a copy; only the orchestrator writes to the shared history |
| Routing | Keyword **substring** matching: `mi` matched *mild*, *limit* and *admission*; plurals worked by accident | Whole-word matching with plural support; `stemi`/`nstemi` added so STEMI questions still route to cardiology |
| Unused imports | `RetrievalQA`, `AgentExecutor`, `create_react_agent`, `hub`, `langchain_experimental` | Removed |
| Deprecated calls | `chain(...)` and `langchain.vectorstores.Chroma` | `chain.invoke(...)` and `langchain_community.vectorstores.Chroma` |
| Telemetry | Chroma errors printed on every query | Disabled at package import |
| Testing | None | 32 offline tests in `tests/` |
| Entry point | `start_medical_chat()` inside a cell | `python main.py`, `--ask`, `--demo` |

---

## 9. Comparison with a real HDFS deployment

### 9.1 Important clarification

**This project does not use HDFS.** There is no Hadoop, Spark, or cluster in the repository. The "data" consists of a few PDF files (about 38 MB) in a local `textbooks/` folder, and the vector index lives in the memory of one Python process.

The comparison below therefore asks: *if this knowledge pipeline were built on top of a real HDFS cluster, what would map to what, what would be gained, and what would be lost?* It is intended as an architectural and interview discussion aid.

### 9.2 What HDFS is (short reference)

The Apache Hadoop documentation describes HDFS as a master/slave design. A **NameNode** manages the file-system namespace and the mapping of blocks to DataNodes, and it is "the arbitrator and repository for all HDFS metadata". **DataNodes** store the blocks and serve reads and writes. The design explicitly states that *user data never flows through the NameNode* ([Apache Hadoop, HDFS Architecture](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html)).

Other key facts from the same design document and common references:

- Files are split into **blocks**, and the block size is configurable. The default is **128 MB** ([3 University, HDFS architecture](https://www.3university.io/learn/hadoop-hdfs-architecture/); [Alluxio, HDFS introduction](https://www.alluxio.io/learn/hdfs/introduction)).
- Each block is **replicated**. The default replication factor is **3** ([Alluxio, HDFS introduction](https://www.alluxio.io/learn/hdfs/introduction)).
- Files are **write-once** (apart from appends and truncates) with one writer at a time ([Apache Hadoop, HDFS Architecture](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html)).
- DataNodes send **heartbeats** and **block reports** to the NameNode. The NameNode uses them to detect failed nodes and restore the replication factor ([Apache Hadoop, HDFS Architecture](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html)).
- Replica placement is **rack-aware**. With replication factor 3, one replica is on the local node, one on a different rack, and one on another node of that remote rack ([Apache Hadoop, HDFS Architecture](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html)).
- HDFS is designed for **large files and high-throughput batch access**, not for low-latency random access.

### 9.3 Concept mapping

| Concept | In this project | In a real HDFS-based system |
|---|---|---|
| Source data | 7 PDF textbooks in `textbooks/` on one disk | Same PDFs stored as HDFS files, e.g. `/data/medical/raw/cancer/*.pdf` |
| Storage unit | A whole PDF, read by `PyPDFLoader` | An HDFS file split into **128 MB blocks**. The largest PDF here (~11 MB) fits in one block. |
| Replication | None. If the disk fails, the files must be restored from the original source. | Each block has **3 replicas** on different DataNodes and racks. |
| Metadata / catalogue | Python dictionaries and `PDF_CONFIGS` in `config.py`. Page metadata is attached to each Document. | The **NameNode** namespace (paths, permissions, block locations), plus a data catalogue such as a Hive metastore for the chunk table. |
| Parallel reading | Pages are read one after another in one process. | Spark or MapReduce tasks read different blocks in parallel, one task per block, running close to the data. |
| Chunking | `RecursiveCharacterTextSplitter`, 1,000 characters with 200 overlap. Done in memory. | Same logic in a distributed job (e.g. a Spark `map` over pages), writing the chunks back to HDFS as Parquet. |
| Embedding | One watsonx call per batch of chunks, done in the process. | Batch embedding job; results written to HDFS; API calls rate-limited across executors. |
| Vector index | **Chroma**, in memory, rebuilt at each start-up. | Vector index stored outside HDFS (e.g. a search engine or vector database), built from the Parquet chunks. HDFS holds the source of truth. |
| Failure handling | A bad PDF is logged and skipped. A failed embedding batch is retried in batches of 50. | Task retries and speculative execution in the framework; lost blocks are re-replicated by HDFS. |
| Scale | About 8,900 chunks in total (8,854 measured), indexed in minutes | Millions of pages from many sources; sharded indexes. |
| Access control | None (local files). | HDFS permissions and Kerberos, or Ranger policies. |
| Writes | The index is created once and not updated. | Write-once files fit well: new guideline versions are new files, and old ones are kept for audit. |

### 9.4 What HDFS would add

1. **Durability.** Three replicas across racks protect the source documents against disk and machine failure.
2. **Scale-out storage.** Adding DataNodes adds capacity without moving files.
3. **Parallel batch processing.** Chunking and embedding can run as parallel tasks, one per block.
4. **Versioning by convention.** Write-once files and dated directories (e.g. `/guidelines/2021/esc_hf.pdf`) make the source of every answer auditable.
5. **Governance.** Permissions, quotas and audit logs belong to the cluster.

### 9.5 What HDFS would not solve, and why this project does not need it

- **Low-latency questions.** HDFS is built for throughput, so reading a block for each user question would be far too slow. The correct pattern is what this project already does: process the files once (batch), build a fast index, and serve questions from the index. A real deployment would do the same, with HDFS holding the raw and processed files and a separate low-latency index serving the chat.
- **Small data.** The textbooks total about 38 MB. HDFS cluster overhead (NameNode, DataNodes, JVMs) costs much more than the data. A single local folder is the right choice here.
- **Chat state.** Conversation memory is small, per session and temporary. It does not belong in HDFS.

### 9.6 Summary comparison

| Dimension | This project | Real HDFS-based design |
|---|---|---|
| Data size | ~38 MB of PDFs | Terabytes of documents |
| Durability | Single disk, no replication | 3 replicas across racks |
| Metadata | In-process config | NameNode namespace and a data catalogue |
| Processing | Single process | Parallel tasks (Spark / MapReduce) |
| Index | In-memory Chroma, rebuilt at each start | Persistent vector store built from HDFS files |
| Failure recovery | Re-run the start-up ingestion | HDFS re-replication and task retry |
| Operational cost | Very low | Cluster to run, secure and monitor |
| Right choice when | Prototype, demo, single-clinic use, teaching | Many guideline sources, multi-team governance, very large corpora |

**Bottom line:** the current design is correct for its size and purpose. The part of the pipeline that would most benefit from HDFS is the **ingestion stage** (store raw PDFs, process them in parallel, keep versioned chunks). The **serving stage** (fast retrieval during chat) should stay in a dedicated vector index.

---

## 10. Limitations and future work

| Limitation | Effect | Possible improvement |
|---|---|---|
| The Chroma index is in memory and rebuilt each start-up | Start-up can take minutes with the large Cancer textbooks, and every rebuild re-embeds every chunk, which uses watsonx quota. | Persist the index with `persist_directory` and skip rebuilding when the PDFs have not changed (for example, by comparing file hashes). |
| Keyword routing | Misses synonyms and questions that mention two domains in an unclear way. | Add an LLM-based or embedding-based router, with keywords kept as a fast first check. |
| Confidence is based only on the number of chunks | It says nothing about whether the answer is correct. | Add a relevance score threshold and show the source page numbers. |
| The answer is not checked against sources | The LLM may still add facts that are not in the text. | Add citation checks or a faithfulness evaluation. |
| The demo content is hand-written and small | Only useful for showing the flow. | Remove or label clearly when real PDFs are available. |
| Two chains per follow-up question (rewrite + answer) | More LLM calls, more latency and quota use. | Cache rewrites or use a single prompt for simple follow-ups. |
| Chroma distance and similarity settings are left at their defaults | Retrieval quality is not tuned. | Evaluate cosine vs. L2 on a small question set. |
| No automated evaluation of answers | Quality is only checked by hand. | Build a small question–answer test set with expected sources. |
| Single user, single process | No concurrency or user accounts. | Put the orchestrator behind an API, with per-session memory. |

---

*This document describes the code as it is in the repository. It is for education and interview preparation only, not clinical use.*
