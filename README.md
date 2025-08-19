# 🏥 Multi-Agent Medical Assistant System

Welcome to the **Multi-Agent Medical Assistant** — a modular Python system designed for accurate, evidence-based support in medical diagnosis, treatment, and education.  
This system combines **state-of-the-art LLMs (IBM Watsonx)** with domain-specialized agents and integrates **PDF knowledge bases** for practical, clinical use.

---

## ✨ Features

### Multi-Domain Coverage
- Specialized agents for:
  - Diabetes  
  - Cancer/Oncology  
  - Mental Health/Psychiatry  
  - Cardiac/Cardiovascular  

### Automated Routing
- Intelligent query router that sends questions to the correct medical domain agent based on context and keywords.

### Custom Knowledge Bases
- Load textbooks, guidelines, or literature (PDFs) for each specialty.

### Conversational Memory
- Remembers previous exchanges to support real **“case discussion”–style conversations**.

### Evidence-Based, Safe Responses
- Each agent follows strict clinical guidelines and returns references when available.

### Demo Mode
- If PDFs are not available, demo content lets you test all agents without extra setup.

---

## ⚙️ Installation

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/yourusername/medical-multi-agent.git
   cd medical-multi-agent
   ```

2. **Install Requirements**  

3. **Add Your Medical PDFs**  
   - Place your textbooks/guidelines in the project folder.  
   - Update the `PDF_CONFIGS` section in the main Python file with correct file paths.  

---

## 🚀 Usage

### Interactive Chat (Recommended)
```python

start_medical_chat()
```

### Programmatic API
```python

# Ask a medical question
response = medical_assistant.chat("What are the criteria for Type 2 Diabetes?")
print(response["answer"])
```

---

## 💡 Example Queries
You can ask questions such as:

- “What are the diagnostic criteria for Type 2 diabetes?”  
- “How is breast cancer staged?”  
- “What medications treat major depression?”  
- “What are the current hypertension guidelines?”  

---

## 🏗️ Architecture

| Module                    | Description |
|----------------------------|-------------|
| **BaseMedicalAgent**       | Abstract class for medical specialty agents |
| **DiabeticAgent/CancerAgent** | Specialty: Diabetes, Cancer/Oncology, Mental Health, Cardiac |
| **MedicalAgentRouter**     | Detects query domain and routes to correct agent |
| **MedicalAssistantOrchestrator** | Manages all agents, memory, routing, and chat history |
| **PDF Knowledge Loader**   | Reads, processes, and indexes textbook PDFs |
| **Conversational Memory**  | Cross-domain chat memory support |

---

## 🔧 Customization

- **Add More Agents**: Extend the `BaseMedicalAgent` for new specialties.  
- **Update Knowledge**: Point `PDF_CONFIGS` to new or different PDF files for up-to-date guidelines.  
- **Tune LLM Parameters**: Adjust Watsonx LLM settings for output quality or reliability.  

---

## 📊 System Status & Maintenance

- Type **`status`** in the chat interface to check active agents and memory.  
- Type **`clear`** to reset conversation history.  

---

## 📝 Attribution

Built using:  
- **IBM Watsonx LLMs**  
- **LangChain**  
- **Chroma vector stores**

⚠️ For academic, educational, and research use only.  

---

✅ **Get started today** — and bring high-quality medical answers to your research, engineering, or education workflow!
