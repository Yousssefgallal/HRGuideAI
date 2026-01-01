# api/messages.py — DEBUG / VERBOSE
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.db_connection import db
import json
import traceback
from config import logger

router = APIRouter(prefix="/messages", tags=["Messages"])

def dbg(title: str, payload=None):
    logger.info("\n" + "-" * 72)
    logger.info(f"🟩 {title}")
    if payload is not None:
        try:
            logger.info(f"payload: {payload}")
        except Exception:
            logger.info("payload: <unserializable>")
    logger.info("-" * 72 + "\n")


class MessageCreate(BaseModel):
    conversation_id: int
    role: str = Field(..., description="Message role: user, assistant, system, or tool")
    content: Dict[str, Any] = Field(..., description="Message content as JSON object")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": 1,
                "role": "user",
                "content": {
                    "text": "What is the leave policy?",
                    "metadata": {
                        "timestamp": "2025-01-15T10:30:00Z",
                        "user_agent": "Mozilla/5.0"
                    }
                }
            }
        }


class MessageResponse(BaseModel):
    message_id: int
    conversation_id: int
    role: str
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_message(payload: MessageCreate):
    dbg("CREATE_MESSAGE — START", {"payload": payload.dict()})
    # Validate conversation
    try:
        conv_check = await db.fetch_one(
            "SELECT conversation_id FROM conversations WHERE conversation_id = :id",
            {"id": payload.conversation_id}
        )
        dbg("CREATE_MESSAGE — conv_check", {"exists": bool(conv_check), "conv_check": dict(conv_check) if conv_check else None})
        if not conv_check:
            raise HTTPException(status_code=404, detail=f"Conversation {payload.conversation_id} not found")

        valid_roles = ["user", "assistant", "system", "tool"]
        if payload.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        query = """
        INSERT INTO messages (conversation_id, role, content)
        VALUES (:conversation_id, :role, :content)
        RETURNING message_id, conversation_id, role, content, created_at
        """
        values = {
            "conversation_id": payload.conversation_id,
            "role": payload.role,
            "content": json.dumps(payload.content, ensure_ascii=False)
        }
        dbg("CREATE_MESSAGE — Executing INSERT", {"query": query, "values": values})
        message = await db.fetch_one(query=query, values=values)
        dbg("CREATE_MESSAGE — INSERT RESULT", {"message": dict(message) if message else None})

        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = :id",
            {"id": payload.conversation_id}
        )
        logger.debug("Conversation updated_at set")

        result = dict(message)
        if isinstance(result["content"], str):
            result["content"] = json.loads(result["content"])
        dbg("CREATE_MESSAGE — FINAL RETURN", {"result": result})
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CREATE_MESSAGE — Exception")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")


@router.get("/{conversation_id}", response_model=List[MessageResponse])
async def get_messages(conversation_id: int, limit: int = 100, offset: int = 0):
    dbg("GET_MESSAGES — START", {"conversation_id": conversation_id, "limit": limit, "offset": offset})
    try:
        conv_check = await db.fetch_one(
            "SELECT conversation_id FROM conversations WHERE conversation_id = :id",
            {"id": conversation_id}
        )
        dbg("GET_MESSAGES — conv_check", {"exists": bool(conv_check)})
        if not conv_check:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        query = """
        SELECT message_id, conversation_id, role, content, created_at
        FROM messages
        WHERE conversation_id = :conversation_id
        ORDER BY created_at ASC
        LIMIT :limit OFFSET :offset
        """
        dbg("GET_MESSAGES — Executing SQL", {"query": query, "values": {"conversation_id": conversation_id, "limit": limit, "offset": offset}})
        messages = await db.fetch_all(query=query, values={"conversation_id": conversation_id, "limit": limit, "offset": offset})
        dbg("GET_MESSAGES — DB ROWS", {"count": len(messages)})
        result = []
        for msg in messages:
            msg_dict = dict(msg)
            if isinstance(msg_dict.get("content"), str):
                try:
                    msg_dict["content"] = json.loads(msg_dict["content"])
                except Exception:
                    logger.exception("Failed to json-decode message content")
            result.append(msg_dict)
        dbg("GET_MESSAGES — FINAL", {"result_count": len(result)})
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("GET_MESSAGES — Exception")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/single/{message_id}", response_model=MessageResponse)
async def get_message(message_id: int):
    dbg("GET_MESSAGE — START", {"message_id": message_id})
    try:
        query = """
        SELECT message_id, conversation_id, role, content, created_at
        FROM messages
        WHERE message_id = :id
        """
        message = await db.fetch_one(query=query, values={"id": message_id})
        dbg("GET_MESSAGE — DB RESULT", {"message": dict(message) if message else None})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        result = dict(message)
        if isinstance(result["content"], str):
            result["content"] = json.loads(result["content"])
        dbg("GET_MESSAGE — FINAL", {"result": result})
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("GET_MESSAGE — Exception")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{message_id}")
async def delete_message(message_id: int, hard_delete: bool = False):
    dbg("DELETE_MESSAGE — START", {"message_id": message_id, "hard_delete": hard_delete})
    try:
        message = await db.fetch_one(
            "SELECT message_id, conversation_id FROM messages WHERE message_id = :id",
            {"id": message_id}
        )
        dbg("DELETE_MESSAGE — EXIST CHECK", {"message": dict(message) if message else None})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        conversation_id = message["conversation_id"]
        query = "DELETE FROM messages WHERE message_id = :id"
        dbg("DELETE_MESSAGE — Executing", {"query": query, "values": {"id": message_id}})
        await db.execute(query=query, values={"id": message_id})
        await db.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = :id", {"id": conversation_id})
        dbg("DELETE_MESSAGE — DONE", {"message_id": message_id})
        return {"success": True, "message": "Message deleted permanently", "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("DELETE_MESSAGE — Exception")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count/{conversation_id}")
async def get_message_count(conversation_id: int):
    dbg("GET_MESSAGE_COUNT — START", {"conversation_id": conversation_id})
    try:
        query = "SELECT COUNT(*) as count FROM messages WHERE conversation_id = :conversation_id"
        result = await db.fetch_one(query=query, values={"conversation_id": conversation_id})
        dbg("GET_MESSAGE_COUNT — RESULT", {"count": result["count"] if result else None})
        return {"conversation_id": conversation_id, "message_count": result["count"] if result else 0}
    except Exception:
        logger.exception("GET_MESSAGE_COUNT — Exception")
        raise HTTPException(status_code=500, detail="Failed to get message count")


@router.delete("/conversation/{conversation_id}/all")
async def delete_all_messages(conversation_id: int):
    dbg("DELETE_ALL_MESSAGES — START", {"conversation_id": conversation_id})
    try:
        conv_check = await db.fetch_one("SELECT conversation_id FROM conversations WHERE conversation_id = :id", {"id": conversation_id})
        dbg("DELETE_ALL_MESSAGES — conv_check", {"exists": bool(conv_check)})
        if not conv_check:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        query = "DELETE FROM messages WHERE conversation_id = :id"
        dbg("DELETE_ALL_MESSAGES — Executing", {"query": query, "values": {"id": conversation_id}})
        await db.execute(query=query, values={"id": conversation_id})
        await db.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = :id", {"id": conversation_id})
        dbg("DELETE_ALL_MESSAGES — DONE", {"conversation_id": conversation_id})
        return {"success": True, "message": "All messages deleted", "conversation_id": conversation_id}
    except HTTPException:
        raise
    except Exception:
        logger.exception("DELETE_ALL_MESSAGES — Exception")
        raise HTTPException(status_code=500, detail="Failed to delete messages")
