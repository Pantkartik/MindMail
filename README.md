#  Mindmail — Agentic Personal Productivity Assistant

> An enterprise-grade, multi-agent AI assistant that connects your Gmail, Google Calendar, and persistent user memory to answer complex cross-source inquiries and prepare human-approved actions.

[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-blue.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)

---

##  Why Mindmail?

Most AI email assistants are simple chatbots or LLM wrappers that only read your unread inbox. **Mindmail** is built from the ground up as a **hierarchical multi-agent system**:

- **Task Planner:** Decomposes multi-faceted questions into atomic sub-tasks.
- **Cross-Source Reasoning:** Seamlessly cross-references emails with calendar events (e.g., matching interview confirmation emails with calendar slots and preparation instructions).
- **Hybrid Semantic RAG:** Ingests and indexes emails using `pgvector` for fast vector + lexical retrieval.
- **Dual-Tier Memory:** Retains short-term thread context and extracts long-term behavioral habits (e.g., email tone, concise formatting, preferred meeting slots).
- **Human-in-the-Loop (HITL) Safety:** Critical actions (sending emails, modifying calendar events) trigger a state pause and require user review/approval.
- **Observable Agent Traces:** Visualizes real-time execution steps, tool latencies, and source citations.

---

## 🏗️ Architecture

```
User Query ──► [FastAPI Gateway] ──► [LangGraph Planner]
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
               [Gmail Agent]          [Calendar Agent]         [RAG / pgvector]
                      │                       │                       │
                      └───────────────────────┼───────────────────────┘
                                              ▼
                                    [Synthesizer Node]
                                              │
                                              ▼
                                 [Evidence & Citation Check]
                                              │
                                              ▼
                                   [HITL Approval Gate]
                                    /                 \
                          (Approved)                   (Rejected)
                              ▼                            ▼
                     [Execute Email / Cal]              [End / Redo]
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Google Cloud Console Project (with Gmail API and Google Calendar API enabled)

### 2. Infrastructure Setup (PostgreSQL + pgvector & Redis)
```bash
# Start PostgreSQL (with pgvector) and Redis
docker-compose up -d
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment variables
cp ../.env.example .env
# Edit .env with your Google & LLM API keys

# Start FastAPI server
uvicorn backend.api.main:app --reload --port 8000
```

### 4. Interactive Testing
Visit the API docs at `http://localhost:8000/docs`.

---

## 📁 Repository Structure

```
Mindmail/
├── PRD.md                 # Complete Product Requirements Document
├── ARCHITECTURE.md        # Technical architecture & LangGraph state design
├── docker-compose.yml     # PostgreSQL + pgvector & Redis services
├── .env.example           # Environment variables template
├── backend/
│   ├── requirements.txt   # Python dependencies
│   ├── agents/
│   │   ├── state.py       # Mindmail TypedDict State definition
│   │   ├── planner.py     # AI Task Decomposition Planner
│   │   └── orchestrator.py# LangGraph compilation & HITL interrupts
│   ├── tools/
│   │   ├── gmail.py       # Gmail API v1 tool suite
│   │   └── calendar.py    # Google Calendar API v3 tool suite
│   ├── memory/
│   │   └── store.py       # Dual-tier persistent memory manager
│   ├── rag/
│   │   └── pipeline.py    # Email chunking, embeddings & pgvector search
│   └── api/
│       └── main.py        # FastAPI server & SSE streaming
└── frontend/              # Next.js 14 Web Application
```
