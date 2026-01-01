# backend/api/load_user_data.py
from fastapi import APIRouter, HTTPException
from typing import Any
from utils.load_data import load_user_data as _load_user_data
from config import logger
from database.db_connection import db

router = APIRouter(prefix="/user", tags=["User"])

def dbg(title: str, payload: Any = None):
    logger.info("\n" + "-" * 72)
    logger.info(f"📦 {title}")
    if payload is not None:
        try:
            logger.info(f"payload: {payload}")
        except Exception:
            logger.info("payload: <unserializable>")
    logger.info("-" * 72 + "\n")


@router.get("/data/{user_id}")
async def get_user_data(user_id: int):
    """
    Returns aggregated user data used to inject into the agent state.
    Delegates to utils.load_user_data.load_user_data which performs DB queries.
    """
    dbg("GET_USER_DATA — START", {"user_id": user_id})
    try:
        # ensure user exists (optional quick check)
        user_check = await db.fetch_one("SELECT user_id FROM users WHERE user_id = :uid", {"uid": user_id})
        if not user_check:
            raise HTTPException(status_code=404, detail="User not found")

        data = await _load_user_data(user_id)
        dbg("GET_USER_DATA — DONE", {"keys": list(data.keys())})
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("GET_USER_DATA — Exception")
        raise HTTPException(status_code=500, detail=str(e))
