# AI News Station: Multi-Agent Orchestration

A production-grade **Multi-Agent System (MAS)** built with **LangGraph** and **FastAPI**. This system automates the lifecycle of digital content creation—from live web research to editorial synthesis and quality assurance—incorporating human oversight and real-time cost tracking[cite: 1].

## 🚀 Key Features

*   **Stateful Multi-Agent Orchestration:** Utilizes a Directed Acyclic Graph (DAG) with cycles to allow agents to collaborate and self-correct[cite: 1].
*   **Human-in-the-Loop (HITL):** Implements state-level interrupts, allowing human operators to review and approve drafts before finalization[cite: 1].
*   **Persistent Checkpointing:** Uses session-based persistence (`thread_id`) to ensure the system can recover state across server restarts or long pauses[cite: 1].
*   **Real-time Observability:** Built-in token tracking (input/output) for every agent interaction to monitor operational costs[cite: 1].
*   **Agentic Search:** Integrated with **Tavily AI** for optimized, LLM-friendly web retrieval[cite: 1].

---

## 🏗️ Architecture

The system is governed by a shared **AgentState**, which acts as a "shared notebook" for three specialized agents[cite: 1]:

1.  **The Researcher:** Executes tool-calls to gather live data from the web based on a user-provided topic[cite: 1].
2.  **The Editor:** Synthesizes raw research data into a formatted, high-quality LinkedIn post[cite: 1].
3.  **The Critic:** Acts as a quality gate. It evaluates the editor's output and either triggers a **Self-Correction loop** or marks the task as complete[cite: 1].



---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Orchestration** | LangGraph |
| **LLM Provider** | OpenAI (GPT-4o) |
| **API Framework** | FastAPI |
| **Search Engine** | Tavily AI |
| **Persistence** | MemorySaver (LangGraph Checkpointer) |
| **Observability** | LangSmith |

---

## 🚦 Getting Started

### 1. Environment Setup
Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
LANGSMITH_API_KEY=your_langsmith_key # Optional for tracing
LANGSMITH_TRACING=true
```

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python main.py
```

---

## 📡 API Endpoints

### `POST /start`
Initializes the graph and runs the **Researcher** and **Editor**. The process will automatically interrupt (pause) after the draft is created for human review[cite: 1].

**Request:**
```json
{
  "topic": "The impact of Blackwell GPUs on AI training"
}
```

### `POST /approve/{thread_id}`
Resumes the graph from the frozen state, running the **Critic** to finalize the post[cite: 1].



