"""
FastAPI server exposing a LangGraph agent for querying the GIU Admin Policy PDF.

This application uses:
- FastAPI for the web server
- LangGraph for agent orchestration with tool calling
- CopilotKit for frontend integration
- OpenAI embeddings for vectorization
- In-memory vector store for document retrieval
- Tool-calling pattern where the LLM decides when to query the PDF
"""

import os
from typing import Annotated, Any
from contextlib import asynccontextmanager
import logging

from database.db_connection import engine, Base  # engine, Base are exported from db_connection.py
import config


import uuid
import traceback
from starlette.requests import Request
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict, Optional
from langchain_core.messages import SystemMessage

from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint

from config import logger, folder_path

from database.db_connection import db
from api.routes import router
from database import models_postgres as models
from agent import create_agent_graph
from utils.message_persistence import extract_message_content, save_langchain_message, message_type_to_role, save_message_to_db

import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

# Load environment variables
load_dotenv()


# Helper debug print wrapper (use logger.info but keep clear separators)
def dbg(title: str, payload: dict = None):
    logger.info("\n" + "=" * 88)
    logger.info(f"🔶 {title}")
    if payload is not None:
        try:
            logger.info(f"payload: {payload}")
        except Exception:
            logger.info("payload: <unserializable>")
    logger.info("=" * 88 + "\n")



# ============================================================
# USER-AWARE WRAPPER — injects user_id + frontend state (DEBUG)
# ============================================================
class UserAwareLangGraphAgent(LangGraphAgent):
    async def invoke(self, data, request: Request = None):
        dbg("UserAwareLangGraphAgent.invoke() — START", {"has_request": bool(request)})
        try:
            # Extract user ID (header > cookie)
            user_id = None
            if request:
                header_user = request.headers.get("x-copilotkit-user-id")
                if header_user:
                    user_id = header_user
                    logger.debug(f"Header user id found: {header_user}")

            cookie_user = request.cookies.get("user_id") if request else None
            if not user_id and cookie_user:
                user_id = cookie_user
                logger.debug(f"Cookie user id found: {cookie_user}")

            # Thread id (header)
            thread_id = None
            if request:
                thread_id = request.headers.get("x-copilotkit-thread-id")
                logger.debug(f"Thread id from header: {thread_id}")

            if not thread_id:
                thread_id = f"thread_{uuid.uuid4().hex[:16]}"
                logger.warning(f"No thread_id provided — generated new: {thread_id}")

            conversation_id = None
            try:
                conv_query = "SELECT conversation_id FROM conversations WHERE thread_id = :thread_id"
                dbg("Looking up conversation by thread_id", {"thread_id": thread_id, "sql": conv_query})
                conv_result = await db.fetch_one(query=conv_query, values={"thread_id": thread_id})
                logger.debug(f"DB result for conversation lookup: {conv_result}")
                if conv_result:
                    conversation_id = conv_result["conversation_id"]
                    logger.info(f"Found conversation_id={conversation_id} for thread_id={thread_id}")
                else:
                    logger.warning(f"No conversation found for thread_id={thread_id} — will attempt auto-create if user provided")
                    if user_id:
                        try:
                            logger.info(f"Auto-creating conversation for user_id={user_id}, thread_id={thread_id}")
                            recheck_query = "SELECT conversation_id FROM conversations WHERE thread_id = :thread_id"
                            recheck_result = await db.fetch_one(query=recheck_query, values={"thread_id": thread_id})
                            logger.debug(f"Recheck result: {recheck_result}")
                            if recheck_result:
                                conversation_id = recheck_result["conversation_id"]
                                logger.info(f"Conversation already created by race condition: {conversation_id}")
                            else:
                                insert_query = """
                                INSERT INTO conversations (user_id, title, thread_id)
                                VALUES (:user_id, :title, :thread_id)
                                ON CONFLICT (thread_id) DO UPDATE SET thread_id = conversations.thread_id
                                RETURNING conversation_id
                                """
                                dbg("Inserting new conversation", {"user_id": int(user_id), "thread_id": thread_id})
                                result = await db.fetch_one(
                                    query=insert_query,
                                    values={
                                        "user_id": int(user_id),
                                        "title": "New Conversation",
                                        "thread_id": thread_id
                                    }
                                )
                                logger.debug(f"Insert result: {result}")
                                if result:
                                    conversation_id = result["conversation_id"]
                                    logger.info(f"Auto-created conversation_id={conversation_id}")
                                else:
                                    logger.error("Insert returned no result")
                        except Exception as create_err:
                            logger.exception(f"Failed auto-create: {create_err}")
                    else:
                        logger.warning("Cannot auto-create conversation — no user_id provided")
            except Exception as e:
                logger.exception(f"Error while looking up / creating conversation: {e}")

            logger.info(f"Resolved: user_id={user_id}, thread_id={thread_id}, conversation_id={conversation_id}")

            # Ensure state
            if "state" not in data:
                data["state"] = {}
                logger.debug("Injected missing data['state']")

            if user_id:
                try:
                    data["state"]["user_id"] = int(user_id)
                except Exception:
                    data["state"]["user_id"] = user_id
                logger.debug(f"Injected user_id into state: {data['state']['user_id']}")

            if conversation_id:
                data["state"]["conversation_id"] = conversation_id
                logger.debug(f"Injected conversation_id into state: {conversation_id}")

            if "user_data" in data.get("state", {}):
                logger.info("Frontend user_data present in state — preserving")

            # ============================================================
            # SAVE USER MESSAGE TO DATABASE (before agent execution)
            # ============================================================
            if conversation_id:
                try:
                    # Extract new messages from the request
                    # CopilotKit sends messages in data["messages"]
                    new_messages = data.get("messages", [])

                    if new_messages:
                        logger.info(f"Found {len(new_messages)} new message(s) to persist")

                        # Save each new user message
                        for msg in new_messages:
                            # Only save user messages here (assistant messages come after agent response)
                            msg_type = message_type_to_role(msg)
                            if msg_type == "user":
                                extracted = extract_message_content(msg)

                                # Safety check — avoid saving empty message
                                if not extracted.get("text"):
                                    logger.warning(
                                        "User message has no text after extraction — skipping save",
                                        extra={"raw_message": str(msg)}
                                    )
                                else:
                                    logger.info(
                                        f"Saving user message to conversation {conversation_id}",
                                        extra={"content": extracted}
                                    )
                                    await save_message_to_db(
                                        conversation_id=conversation_id,
                                        role="user",
                                        content=extracted
                                    )
                    else:
                        logger.debug("No new messages in data['messages']")

                except Exception as persist_err:
                    logger.exception(f"Error saving user message: {persist_err}")
                    # Don't fail the request if persistence fails
            else:
                logger.warning("No conversation_id — skipping message persistence")

            dbg("UserAwareLangGraphAgent.invoke() — CALLING super().invoke()", {"state_snapshot": data.get("state")})
            result = await super().invoke(data, request)

            # ============================================================
            # SAVE ASSISTANT RESPONSE TO DATABASE (after agent execution)
            # ============================================================
            if conversation_id:
                try:
                    # Extract assistant messages from the result
                    # LangGraph returns messages in result["messages"] or result might have state with messages
                    result_messages = []

                    # Check different possible locations for messages in response
                    if isinstance(result, dict):
                        if "messages" in result:
                            result_messages = result["messages"]
                        elif "state" in result and "messages" in result["state"]:
                            result_messages = result["state"]["messages"]

                    if result_messages:
                        logger.info(f"Found {len(result_messages)} message(s) in agent response")

                        # Save assistant and tool messages (skip user messages as they're already saved)
                        for msg in result_messages:
                            msg_type = message_type_to_role(msg)
                            if msg_type in ["assistant", "tool"]:
                                extracted = extract_message_content(msg)

                                if extracted.get("text") or extracted.get("tool_calls"):
                                    await save_message_to_db(
                                        conversation_id=conversation_id,
                                        role=msg_type,
                                        content=extracted
                                    )

                                logger.info(f"Saving {msg_type} message to conversation {conversation_id}")
                                await save_langchain_message(conversation_id, msg)
                    else:
                        logger.debug("No messages found in agent result to persist")

                except Exception as persist_err:
                    logger.exception(f"Error saving assistant message: {persist_err}")
                    # Don't fail the request if persistence fails

            return result
        except Exception as e:
            logger.error("Unhandled exception in UserAwareLangGraphAgent.invoke()")
            logger.error(traceback.format_exc())
            # Return a structured error to the caller so frontend sees a 500 instead of crashing silently
            raise

def load_and_index_all_pdfs(folder_path: str):
    """
    Load ALL PDFs in a folder, split them into chunks, 
    embed them, and create ONE combined vector store.

    Returns:
        retriever: unified retriever that searches across all PDFs
    """

    print("=== START: load_and_index_all_pdfs ===")
    print(f"[1] Scanning folder for PDFs: {folder_path}")

    # 1. Collect all PDF filenames
    pdf_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".pdf")
    ]

    print(f"[2] Found {len(pdf_files)} PDF files:")
    for f in pdf_files:
        print(f"     - {f}")

    all_documents = []

    # 2. Process each PDF file
    for idx, pdf_name in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(folder_path, pdf_name)
        print(f"\n=== Processing PDF {idx}/{len(pdf_files)} ===")
        print(f"[3] Loading PDF: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        print(f"[4] Loaded {len(docs)} pages from: {pdf_name}")

        # Split into chunks
        print("[5] Splitting PDF into chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = splitter.split_documents(docs)
        print(f"[6] Created {len(chunks)} chunks from: {pdf_name}")

        # Add metadata to identify origin file (optional but recommended)
        for c in chunks:
            c.metadata["source_pdf"] = pdf_name

        all_documents.extend(chunks)

    print(f"\n[7] TOTAL chunks from ALL PDFs: {len(all_documents)}")

    # 3. Build embeddings + vector store
    print("[8] Initializing OpenAI embeddings...")
    embeddings = OpenAIEmbeddings()

    print("[9] Creating combined vector store...")
    vectorstore = DocArrayInMemorySearch.from_documents(
        documents=all_documents,
        embedding=embeddings
    )
    print("[10] Combined vector store created successfully.")

    # 4. Make retriever
    print("[11] Creating unified retriever (k=3)...")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    print("[12] Unified retriever ready.")
    print("=== END: load_and_index_all_pdfs ===\n")

    return retriever

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.
    Initializes the agent on startup.
    """
    
    # Startup
    # Validate OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in a .env file or export it."
        )
    
    try:
        await db.connect()
        logger.info("✅ Connected to PostgreSQL")
    except Exception:
        logger.exception("❌ Failed to connect to Postgres")
        raise

    logger.info("\n" + "=" * 60)
    logger.info("Starting GIU Admin Policy QA Agent API")
    logger.info("=" * 60 + "\n")

    # Load and index the PDF
    retriever = load_and_index_all_pdfs(folder_path)

    # Create the agent graph
    graph = create_agent_graph(retriever)

    # Create CopilotKit Remote Endpoint with our LangGraph agent
    sdk = CopilotKitRemoteEndpoint(
        agents=[
            UserAwareLangGraphAgent(
                name="policy_qa_agent",
                description="An agent that answers questions about the GIU Admin Policy document",
                graph=graph,
            )
        ],
    )

    # Add the CopilotKit endpoint to our FastAPI app
    add_fastapi_endpoint(app, sdk, "/copilotkit")

    logger.info("\n✅ Agent initialized and ready at /copilotkit")
    logger.info("🏥 Health check available at /health\n")

    yield

    try:
        await db.disconnect()
        logger.info("🛑 Disconnected Postgres")
    except Exception:
        logger.exception("❌ Error disconnecting Postgres")

    logger.info("🛑 HRGuideAI Backend stopped")

    # Shutdown (cleanup if needed)
    logger.info("Shutting down...")


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="GIU Policy QA Agent API",
    description="API for querying the GIU Admin Policy document using a conversational agent",
    version="1.0.0",
    lifespan=lifespan
)

# Mount API routers (this was missing)
app.include_router(router)

# Optional: create tables (dev convenience)
try:
    logger.info("Ensuring database tables exist (Base.metadata.create_all)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables checked/created.")
except Exception:
    logger.exception("Failed to create/check DB tables with Base.metadata.create_all")


# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default
        "http://localhost:3001",  # Alternative port
        "https://localhost:3000",
        "https://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "policy_qa_agent"}


def main():
    """Run the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
