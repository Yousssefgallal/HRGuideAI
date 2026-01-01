# GIU Admin Policy Conversational Agent

A LangGraph-based conversational AI agent that can answer questions about the GIU Admin Policy document using retrieval-augmented generation (RAG) with tool calling.

## Architecture

This application leverages:

- **LangGraph**: Orchestrates the agent's workflow with stateful conversation management
- **Tool Calling**: The LLM decides when to query the PDF based on user questions
- **OpenAI Embeddings**: Converts text into vector representations for semantic search
- **In-Memory Vector Store**: Fast document retrieval using DocArray
- **Conversational Memory**: Maintains context across multiple exchanges

## Features

- 📄 **PDF Question Answering**: Ask questions about GIU administrative policies
- 🧠 **Smart Retrieval**: Agent automatically decides when to search the document
- 💬 **Conversational**: Maintains conversation history for context-aware responses
- 🔍 **Semantic Search**: Uses vector embeddings for accurate information retrieval
- ⚡ **Fast**: In-memory vector store for quick responses

## Setup

### Prerequisites

- Python 3.11+
- Poetry (installed in the root directory)
- OpenAI API key

### Installation

1. **Install dependencies** (from root directory):
   ```bash
   poetry install
   ```

2. **Set up environment variables**:
   ```bash
   cd backend
   cp .env.example .env
   ```

3. **Add your OpenAI API key** to the `.env` file:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

   Get your API key from: https://platform.openai.com/api-keys

## Usage

### Running the Agent

From the `backend` directory:

```bash
poetry run python main.py
```

### Example Conversation

```
============================================================
GIU Admin Policy Conversational Agent
============================================================

Loading PDF from: ../docs/GIU policy_ Admin.pdf
Loaded 50 pages from PDF
Split into 150 chunks
Vector store created successfully

Agent ready! Type your questions (or 'quit' to exit)
------------------------------------------------------------

You: What are the admission requirements?