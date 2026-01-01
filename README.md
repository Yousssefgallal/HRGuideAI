# GIU Policy QA Application

A full-stack conversational AI application that allows users to ask questions about the GIU Administrative Policy document. The application uses LangGraph for agent orchestration, CopilotKit for seamless frontend-backend integration, and OpenAI for embeddings and language model capabilities.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Frontend      │         │   API Proxy      │         │    Backend      │
│   (Next.js)     │────────▶│   (Next.js API)  │────────▶│   (FastAPI)     │
│                 │         │                  │         │                 │
│  CopilotSidebar │         │  /api/copilotkit │         │  LangGraph Agent│
│                 │         │                  │         │  + Vector Store │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### Components

- **Frontend** (Next.js + shadcn/ui + CopilotKit)
  - Clean, modern UI with CopilotKit sidebar
  - Real-time chat interface
  - Responsive design with dark mode support

- **Backend** (FastAPI + LangGraph + CopilotKit)
  - LangGraph agent with tool calling
  - PDF document processing and indexing
  - OpenAI embeddings for semantic search
  - In-memory vector store for fast retrieval

- **Connection Layer** (CopilotKit)
  - Seamless frontend-backend communication
  - Agent state management
  - Tool calling infrastructure

## Prerequisites

- Python 3.12.x (required for backend dependencies)
- Node.js 18+ and npm
- Poetry (Python dependency management)
- OpenAI API key

## Project Structure

```
bachelor_project/
├── frontend/                 # Next.js frontend
│   ├── app/
│   │   ├── api/
│   │   │   └── copilotkit/  # API proxy route
│   │   ├── page.tsx         # Main chat page
│   │   └── layout.tsx       # Root layout with CopilotKit provider
│   ├── components/
│   │   └── providers.tsx    # CopilotKit configuration
│   └── .env.local           # Frontend environment variables
│
├── backend/                  # FastAPI backend
│   ├── main.py              # FastAPI server + LangGraph agent
│   ├── .env                 # Backend environment variables
│   └── README.md
│
├── docs/                     # Documents
│   └── GIU policy_ Admin.pdf # The policy document
│
└── pyproject.toml           # Python dependencies
```

## Setup

### 1. Clone and Install Dependencies

#### Backend Setup

```bash
# Install Python dependencies with Poetry (from project root)
poetry install

# Verify installation
poetry show
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Return to project root
cd ..
```

### 2. Configure Environment Variables

#### Backend (.env)

The backend `.env` file is already created at `backend/.env` with your OpenAI API key.

If you need to update it:

```bash
# Edit backend/.env
OPENAI_API_KEY=your-actual-api-key-here
PORT=8000  # Optional, defaults to 8000
```

#### Frontend (.env.local)

The frontend environment file is already created at `frontend/.env.local`:

```bash
BACKEND_URL=http://localhost:8000
```

## Running the Application

You need to run both the backend and frontend servers simultaneously.

### Terminal 1: Start the Backend

```bash
# From project root
cd backend
poetry run python main.py
```

The backend will:
- Load and index the PDF document
- Start the FastAPI server on `http://localhost:8000`
- Expose the agent at `/copilotkit`

You should see:
```
============================================================
Starting GIU Admin Policy QA Agent API
============================================================

Loading PDF from: ../docs/GIU policy_ Admin.pdf
Loaded X pages from PDF
Split into Y chunks
Vector store created successfully

✅ Agent initialized and ready at /copilotkit
🏥 Health check available at /health
```

### Terminal 2: Start the Frontend

```bash
# From project root (in a new terminal)
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

### Access the Application

1. Open your browser and navigate to `http://localhost:3000`
2. Click the chat button in the bottom-right corner
3. Start asking questions about the GIU Administrative Policies!

## Usage Examples

Once the application is running, you can ask questions like:

- "What are the admission requirements?"
- "Tell me about the grading policy"
- "What is the attendance policy?"
- "How do I apply for financial aid?"
- "What are the graduation requirements?"

The agent will:
1. Understand your question
2. Search the policy document using semantic search
3. Retrieve relevant sections
4. Generate an accurate answer based on the document

## Features

- **🤖 AI-Powered Search**: Uses OpenAI embeddings for intelligent document retrieval
- **💬 Conversational Interface**: Natural chat-based interaction
- **🎯 Context-Aware**: Maintains conversation history for follow-up questions
- **⚡ Fast Responses**: In-memory vector store for quick retrieval
- **🎨 Modern UI**: Clean interface built with shadcn/ui components
- **🌓 Dark Mode**: Automatic dark/light mode support
- **📱 Responsive**: Works on desktop and mobile devices

## Development

### Backend Development

```bash
poetry run python backend/main.py
```

The server will auto-reload on code changes.

### Frontend Development

```bash
cd frontend
npm run dev
```

Next.js will hot-reload on code changes.

### Debugging

- **Backend logs**: Check the terminal running the FastAPI server
- **Frontend logs**: Check the browser console and the terminal running Next.js
- **API proxy**: Monitor requests in the browser Network tab

## Troubleshooting

### Backend Issues

**Problem**: `OPENAI_API_KEY not found`
```bash
# Solution: Check backend/.env file
cat backend/.env
# Make sure OPENAI_API_KEY is set
```

**Problem**: `ModuleNotFoundError`
```bash
# Solution: Reinstall dependencies
poetry install
```

**Problem**: PDF not found
```bash
# Solution: Verify the PDF exists
ls docs/GIU\ policy_\ Admin.pdf
```

### Frontend Issues

**Problem**: Can't connect to backend
```bash
# Solution 1: Verify backend is running
curl http://localhost:8000/health

# Solution 2: Check frontend/.env.local
cat frontend/.env.local
```

**Problem**: CopilotKit errors
```bash
# Solution: Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### General Issues

**Problem**: Port already in use
```bash
# Solution: Change the port
# Backend: Set PORT in backend/.env
# Frontend: Run on different port
npm run dev -- -p 3001
```

## Technology Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **UI Library**: shadcn/ui with Radix UI
- **Styling**: TailwindCSS
- **AI Integration**: CopilotKit
- **Icons**: Lucide React

### Backend
- **Web Framework**: FastAPI
- **Agent Framework**: LangGraph
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-ada-002
- **Vector Store**: DocArray (in-memory)
- **PDF Processing**: PyPDF
- **AI Integration**: CopilotKit Python SDK

### Infrastructure
- **Package Management**: Poetry (Python), npm (JavaScript)
- **Language**: Python 3.12, TypeScript
- **API Protocol**: CopilotKit AG UI Protocol

## License

This project is for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend and frontend logs
3. Verify all environment variables are set correctly
