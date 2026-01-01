import os
from typing import Annotated, Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from langchain.tools.retriever import create_retriever_tool

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from database.db_connection import db
from api.routes import router
from database import models_postgres as models
from utils.promt import system_promptt
from tools.Promotion_Calculator import calculate_promotion_eligibility
from tools.Promotion_Table import get_promotion_calculation_table
from tools.Form import parse_form_request_excel, fill_excel_form



class State(TypedDict):
    """State schema for the conversational agent."""
    messages: Annotated[list, add_messages]
    retrieved_chunks: list[dict[str, Any]]  # Store retrieved document chunks
    user_id: Optional[int]                    # Persist user_id across graph steps
    user_data: Optional[dict]                 # Complete user data (academic, leaves, training)
    conversation_id: Optional[int]            # Conversation ID for message persistence


def create_agent_graph(retriever):
    """
    Create a LangGraph agent with tool-calling capability.

    Args:
        retriever: The retriever for querying the PDF

    Returns:
        Compiled LangGraph agent graph
    """
    # Create retrieval tool
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_policy_info",
        "Search and retrieve information from the GIU Admin Policy document. "
        "Use this tool to answer questions about GIU administrative policies, "
        "procedures, regulations, and guidelines."
    )

    promotion_tool = calculate_promotion_eligibility
    promotion_table_tool = get_promotion_calculation_table
    parse_request = parse_form_request_excel
    fill_form = fill_excel_form

    tools = [retriever_tool, promotion_tool, promotion_table_tool, parse_request, fill_form]

    # Initialize LLM with tool binding
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    def build_llm_messages(state: State, system_prompt: str):
        """
        Build the final ordered list of messages for LLM invocation.
        Includes:
        - system prompt
        - user_data injection
        - conversation messages from state (HumanMessage, AIMessage, ToolMessage)
        """
        messages = []
        
        # 1) System prompt ALWAYS first
        messages.append(SystemMessage(content=system_prompt))
        
        # 2) Add user_data if exists
        if state.get("user_data"):
            messages.append(
                SystemMessage(
                    content=f"USER DATA for personalization:\n{state['user_data']}"
                )
            )
        
        # 3) Add real conversation messages
        # LangGraph ensures these are always BaseMessage objects
        for msg in state["messages"]:
            messages.append(msg)
        
        return messages

    # Define the chatbot node
    def chatbot(state: State):
        """
        Main agent node that decides whether to use tools or respond directly.
        """
        system_prompt = system_promptt

        llm_messages = build_llm_messages(state, system_prompt)

        # LLM invocation (supports tools)
        response = llm_with_tools.invoke(llm_messages)

        # LangGraph requires returning new messages
        return {"messages": [response]}

    # Define a custom tool node that captures retrieved chunks
    def retrieve_and_store(state: State):
        """
        Custom tool node that executes retrieval and stores chunks in state.
        """
        # Get the last message (which should have tool calls)
        last_message = state["messages"][-1]

        # Execute the tool calls
        tool_node = ToolNode(tools=tools)
        result = tool_node.invoke(state)

        # Extract retrieved chunks if the retrieval tool was called
        retrieved_chunks = []
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                if tool_call.get("name") == "retrieve_policy_info":
                    # Get the query that was used
                    query = tool_call.get("args", {}).get("query", "")

                    # Retrieve documents to get chunk details
                    docs = retriever.invoke(query)

                    # Format chunks for frontend display
                    for i, doc in enumerate(docs):
                        chunk_info = {
                            "content": doc.page_content,
                            "page": doc.metadata.get("page", "Unknown"),
                            "source": doc.metadata.get("source", "GIU Policy"),
                            "index": i + 1,
                        }
                        retrieved_chunks.append(chunk_info)

        return {
            "messages": result.get("messages", []),
            "retrieved_chunks": retrieved_chunks
        }

    # Build the graph
    graph_builder = StateGraph(State)

    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", retrieve_and_store)

    # Add edges
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,  # If LLM makes a tool call, go to tools; otherwise END
    )
    graph_builder.add_edge("tools", "chatbot")  # After tools, return to chatbot

    # Compile with memory for conversation persistence
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    
    return graph
