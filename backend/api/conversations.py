# api/conversations.py — DEBUG / VERBOSE
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.db_connection import db
from datetime import datetime
import uuid
import json
import traceback
from config import logger

router = APIRouter(prefix="/conversations", tags=["Conversations"])

def dbg(title: str, payload=None):
    logger.info("\n" + "-" * 72)
    logger.info(f"🟦 {title}")
    if payload is not None:
        try:
            logger.info(f"payload: {payload}")
        except Exception:
            logger.info("payload: <unserializable>")
    logger.info("-" * 72 + "\n")

# Pydantic models
class CreateConversationRequest(BaseModel):
    user_id: int
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    conversation_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    thread_id: str
    is_active: bool


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class MessageResponse(BaseModel):
    message_id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


@router.post("/", response_model=ConversationResponse)
async def create_conversation(payload: CreateConversationRequest):
    dbg("CREATE_CONVERSATION — RECEIVED", {"payload": payload.dict()})
    thread_id = f"thread_{uuid.uuid4().hex[:16]}"
    query = """
    INSERT INTO conversations (user_id, title, thread_id)
    VALUES (:user_id, :title, :thread_id)
    RETURNING *
    """
    try:
        dbg("Executing SQL INSERT", {"query": query, "values": {"user_id": payload.user_id, "title": payload.title, "thread_id": thread_id}})
        conversation = await db.fetch_one(query=query, values={
            "user_id": payload.user_id,
            "title": payload.title,
            "thread_id": thread_id
        })
        dbg("CREATE_CONVERSATION — DB RESULT", {"conversation": dict(conversation) if conversation else None})
        return dict(conversation)
    except Exception as e:
        logger.error("Failed to create conversation")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(user_id: int, include_inactive: bool = False):
    dbg("GET_USER_CONVERSATIONS — START", {"user_id": user_id, "include_inactive": include_inactive})
    base_query = """
    SELECT * FROM conversations
    WHERE user_id = :user_id
    """
    if not include_inactive:
        base_query += " AND is_active = TRUE"
    base_query += " ORDER BY updated_at DESC"
    try:
        dbg("Executing SQL SELECT", {"query": base_query, "values": {"user_id": user_id}})
        conversations = await db.fetch_all(query=base_query, values={"user_id": user_id})
        dbg("GET_USER_CONVERSATIONS — RESULT", {"count": len(conversations)})
        return [dict(conv) for conv in conversations]
    except Exception as e:
        logger.exception("Error fetching user conversations")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    dbg("GET_CONVERSATION — START", {"conversation_id": conversation_id})
    try:
        query = "SELECT * FROM conversations WHERE conversation_id = :id"
        conv = await db.fetch_one(query=query, values={"id": conversation_id})
        dbg("GET_CONVERSATION — DB RESULT", {"conversation": dict(conv) if conv else None})
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return dict(conv)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving conversation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thread/{thread_id}", response_model=ConversationResponse)
async def get_conversation_by_thread(thread_id: str):
    dbg("GET_CONVERSATION_BY_THREAD — START", {"thread_id": thread_id})
    try:
        query = "SELECT * FROM conversations WHERE thread_id = :thread_id"
        conv = await db.fetch_one(query=query, values={"thread_id": thread_id})
        dbg("GET_CONVERSATION_BY_THREAD — DB RESULT", {"conversation": dict(conv) if conv else None})
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return dict(conv)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving conversation by thread")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, payload: UpdateConversationRequest):
    dbg("UPDATE_CONVERSATION — START", {"conversation_id": conversation_id, "payload": payload.dict()})
    updates = []
    values = {"id": conversation_id}
    if payload.title is not None:
        updates.append("title = :title")
        values["title"] = payload.title
    if payload.is_active is not None:
        updates.append("is_active = :is_active")
        values["is_active"] = payload.is_active
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    query = f"""
    UPDATE conversations
    SET {', '.join(updates)}
    WHERE conversation_id = :id
    RETURNING *
    """
    try:
        dbg("Executing SQL UPDATE", {"query": query, "values": values})
        conversation = await db.fetch_one(query=query, values=values)
        dbg("UPDATE_CONVERSATION — DB RESULT", {"conversation": dict(conversation) if conversation else None})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return dict(conversation)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating conversation")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, soft_delete: bool = True):
    dbg("DELETE_CONVERSATION — START", {"conversation_id": conversation_id, "soft_delete": soft_delete})
    try:
        if soft_delete:
            query = """
            UPDATE conversations
            SET is_active = FALSE
            WHERE conversation_id = :id
            RETURNING conversation_id
            """
        else:
            query = "DELETE FROM conversations WHERE conversation_id = :id RETURNING conversation_id"
        dbg("Executing SQL DELETE/UPDATE", {"query": query, "values": {"id": conversation_id}})
        result = await db.fetch_one(query=query, values={"id": conversation_id})
        dbg("DELETE_CONVERSATION — DB RESULT", {"result": dict(result) if result else None})
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"success": True, "message": "Conversation deleted", "conversation_id": result["conversation_id"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting conversation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(conversation_id: int, limit: int = 100):
    dbg("GET_CONVERSATION_MESSAGES — START", {"conversation_id": conversation_id, "limit": limit})
    try:
        query = """
        SELECT * FROM messages
        WHERE conversation_id = :id
        ORDER BY created_at ASC
        LIMIT :limit
        """
        dbg("Executing SQL SELECT messages", {"query": query, "values": {"id": conversation_id, "limit": limit}})
        messages = await db.fetch_all(query=query, values={"id": conversation_id, "limit": limit})
        dbg("GET_CONVERSATION_MESSAGES — DB ROWS", {"rows": len(messages)})
        return [dict(msg) for msg in messages]
    except Exception as e:
        logger.exception("Error retrieving conversation messages")
        raise HTTPException(status_code=500, detail=str(e))
