"""
Message Persistence Utilities
Handles saving messages to the database during agent execution.
"""

import json
from typing import Any, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from database.db_connection import db
from config import logger


async def save_message_to_db(
    conversation_id: int,
    role: str,
    content: Dict[str, Any]
) -> Optional[int]:
    try:
        # --------------------------------------------------
        # ✅ DEDUPLICATION BY copilot_message_id
        # --------------------------------------------------
        copilot_id = content.get("metadata", {}).get("copilot_message_id")

        if copilot_id:
            exists = await db.fetch_one(
                "SELECT 1 FROM messages WHERE copilot_message_id = :id",
                {"id": copilot_id}
            )
            if exists:
                logger.info(f"⏭️ Skipping duplicate message {copilot_id}")
                return None
        # --------------------------------------------------

        query = """
        INSERT INTO messages (conversation_id, role, content, copilot_message_id)
        VALUES (:conversation_id, :role, :content, :copilot_message_id)
        RETURNING message_id
        """

        values = {
            "conversation_id": conversation_id,
            "role": role,
            "content": json.dumps(content, ensure_ascii=False),
            "copilot_message_id": copilot_id
        }

        result = await db.fetch_one(query=query, values=values)

        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = :id",
            {"id": conversation_id}
        )

        if result:
            logger.info(
                f"✅ Saved message {result['message_id']} "
                f"(role={role}, copilot_id={copilot_id})"
            )
            return result["message_id"]

        return None

    except Exception as e:
        logger.exception(f"❌ Failed to save message to DB: {e}")
        return None



def extract_message_content(message):
    if not hasattr(message, "content"):
        return None

    text = message.content.strip() if isinstance(message.content, str) else ""

    # 🚫 Skip empty / system / lifecycle messages
    if not text:
        return None

    return {
        "text": text,
        "metadata": {
            "copilot_message_id": getattr(message, "id", None),
            "timestamp": message.additional_kwargs.get("timestamp")
        }
    }




def message_type_to_role(message) -> str:
    """
    Convert LangChain message type to database role.

    Args:
        message: LangChain message object

    Returns:
        Role string (user, assistant, system, tool)
    """
    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "assistant"
    elif isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        # Fallback based on message type attribute
        message_type = getattr(message, "type", "unknown")
        type_to_role = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "tool": "tool"
        }
        return type_to_role.get(message_type, "user")


async def save_langchain_message(
    conversation_id: int,
    message
) -> Optional[int]:
    """
    Save a LangChain message object to the database.

    Args:
        conversation_id: The conversation ID
        message: LangChain message object

    Returns:
        message_id if successful, None otherwise
    """
    role = message_type_to_role(message)
    content = extract_message_content(message)
    if content is None:
        return None  # 🚫 DO NOT SAVE

    return await save_message_to_db(conversation_id, role, content)
