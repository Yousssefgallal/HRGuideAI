# utils/load_user_data.py — DEBUG
from database.db_connection import db
from config import logger
import traceback

def dbg(title: str, payload=None):
    logger.info("\n" + "-" * 72)
    logger.info(f"📦 {title}")
    if payload is not None:
        try:
            logger.info(f"payload: {payload}")
        except Exception:
            logger.info("payload: <unserializable>")
    logger.info("-" * 72 + "\n")


async def load_user_data(user_id: int):
    dbg("LOAD_USER_DATA — START", {"user_id": user_id})
    try:
        # 1) user
        dbg("QUERY: users", {"sql": "SELECT * FROM users WHERE user_id = :uid", "uid": user_id})
        user = await db.fetch_one("SELECT * FROM users WHERE user_id = :uid", {"uid": user_id})
        dbg("USER RESULT", {"user": dict(user) if user else None})
        if not user:
            logger.warning("User not found in load_user_data")
            return {
                "error": "User not found",
                "user": None,
                "academic": None,
                "leaves": None,
                "training": None,
                "chat_history": None
            }

        # 2) academic profile
        dbg("QUERY: academic_profile", {"sql": "SELECT * FROM academic_profile WHERE user_id = :uid", "uid": user_id})
        academic = await db.fetch_one("SELECT * FROM academic_profile WHERE user_id = :uid", {"uid": user_id})
        dbg("ACADEMIC RESULT", {"academic": dict(academic) if academic else None})

        # 3) leaves
        dbg("QUERY: leave_balances", {"sql": "SELECT * FROM leave_balances WHERE user_id = :uid", "uid": user_id})
        leaves = await db.fetch_one("SELECT * FROM leave_balances WHERE user_id = :uid", {"uid": user_id})
        dbg("LEAVES RESULT", {"leaves": dict(leaves) if leaves else None})

        # 4) training records (multiple)
        dbg("QUERY: training_records", {"sql": "SELECT * FROM training_records WHERE user_id = :uid", "uid": user_id})
        training_rows = await db.fetch_all("SELECT * FROM training_records WHERE user_id = :uid", {"uid": user_id})
        training = [dict(row) for row in training_rows] if training_rows else []
        dbg("TRAINING RESULT", {"count": len(training)})

        # 5) chat history
        dbg("QUERY: conversations", {"sql": "SELECT * FROM conversations WHERE user_id = :uid ORDER BY created_at DESC", "uid": user_id})
        chat_rows = await db.fetch_all("SELECT * FROM conversations WHERE user_id = :uid ORDER BY created_at DESC", {"uid": user_id})
        chat_history = [dict(row) for row in chat_rows] if chat_rows else []
        dbg("CHAT HISTORY RESULT", {"count": len(chat_history)})

        result = {
            "user": dict(user),
            "academic": dict(academic) if academic else None,
            "leaves": dict(leaves) if leaves else None,
            "training": training,
            "chat_history": chat_history
        }
        dbg("LOAD_USER_DATA — FINAL", {"keys": list(result.keys())})
        return result
    except Exception:
        logger.error("Exception in load_user_data")
        logger.error(traceback.format_exc())
        raise
