# backend/api/routes.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import bcrypt
import os

from database.db_connection import db

# System modules (Excel workflow)
from tools.Form import (FILLED_FORMS_DIR, fill_excel_form, parse_form_request_excel)

# Other backend routers
from api.load_user_data import router as user_data_router
from api.conversations import router as conversations_router
from api.messages import router as messages_router


# ======================================================
# AUTH ROUTER
# ======================================================

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


@auth_router.post("/login")
async def login_user(payload: LoginRequest):
    query = "SELECT * FROM users WHERE email = :email"
    user = await db.fetch_one(query=query, values={"email": payload.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_password = user["password"]

    try:
        if isinstance(stored_password, str):
            stored_password = stored_password.encode("utf-8")

        ok = bcrypt.checkpw(payload.password.encode("utf-8"), stored_password)

    except Exception:
        raise HTTPException(status_code=500, detail="Server error during authentication")

    if not ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_payload = {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role_type": user["role_type"],
        "position_title": user["position_title"],
        "faculty_or_department": user["faculty_or_department"],
        "is_admin": user["is_admin"],
    }

    response = JSONResponse(
        content={
            "success": True,
            "message": "Login successful",
            "user": user_payload,
        }
    )

    # Set cookie
    response.set_cookie(
        key="user_id",
        value=str(user["user_id"]),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    return response


# ======================================================
# FILE DOWNLOAD ROUTER  (Excel)
# ======================================================

files_router = APIRouter(prefix="/filled_forms", tags=["Files"])

@files_router.get("/{filename}")
def download_excel(filename: str):
    safe = os.path.basename(filename)
    path = FILLED_FORMS_DIR / safe

    if not path.exists():
        raise HTTPException(404, detail="File not found")

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=safe
    )


# ======================================================
# EXCEL FORM GENERATION ROUTER
# ======================================================

forms_router = APIRouter(prefix="/forms", tags=["HR Forms"])

class FormGenerateRequest(BaseModel):
    user_id: int
    form_type: str     # annual | accidental | marriage | excuse | maternity | mission | attendance
    content: str       # user natural language explanation


@forms_router.post("/generate")
async def generate_form(request: FormGenerateRequest):

    # STEP 1 — Parse user natural language into structured JSON
    parsed = parse_form_request_excel(
        user_text=request.content,
        form_type=request.form_type
    )

    if parsed.get("error"):
        # Return missing fields — agent will ask follow-up questions
        return {
            "success": False,
            "message": "Parsing failed — missing or invalid fields",
            "detail": parsed
        }

    structured_fields = parsed["parsed"]

    # STEP 2 — Fill Excel template
    result = await fill_excel_form(
        form_type=request.form_type,
        parsed_data=structured_fields,
        user_id=request.user_id
    )

    if result.get("error"):
        raise HTTPException(500, detail=result["detail"])

    filename = os.path.basename(result["file_path"])

    return {
        "success": True,
        "form_type": request.form_type,
        "download_url": f"/filled_forms/{filename}"
    }


# ======================================================
# MAIN AGGREGATOR ROUTER
# ======================================================

router = APIRouter()

router.include_router(auth_router)
router.include_router(user_data_router)
router.include_router(conversations_router)
router.include_router(messages_router)
router.include_router(files_router)
router.include_router(forms_router)
