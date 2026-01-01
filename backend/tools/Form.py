# backend/tools/Form.py

from langchain.tools import tool
from langchain_openai import ChatOpenAI
from database.db_connection import db

from utils.form_convertor import (
    AnnualLeaveRequest,
    fill_excel_form as converter_fill_excel_form,
    FILLED_FORMS_DIR
)

from pydantic import ValidationError
from pathlib import Path
from typing import Optional
import uuid


# ======================================================
# PARSER TOOL
# ======================================================

@tool("parse_form_request_excel")
def parse_form_request_excel(user_text: str, form_type: str):
    """
    Parse natural-language text into structured fields for Excel HR forms.
    """
    # Only annual/marriage/accidental supported for now
    if form_type not in ["annual", "accidental", "marriage"]:
        return {
            "error": "unsupported_form",
            "supported": ["annual", "accidental", "marriage"]
        }

    extractor = ChatOpenAI(
        model="gpt-5-mini", temperature=0
    ).with_structured_output(AnnualLeaveRequest)

    try:
        parsed = extractor.invoke(user_text)
        return {"success": True, "parsed": parsed.dict()}
    except Exception as e:
        return {"error": "PARSE_FAILED", "detail": str(e)}



# ======================================================
# EXCEL FILLER TOOL
# ======================================================

@tool("fill_excel_form")
def fill_excel_form(form_type: str, parsed_data: dict, user_id: Optional[int] = None):
    """
    Fill an Excel HR form using utils.form_converter.fill_excel_form().
    Returns {file_path}.
    """
    try:
        validated = AnnualLeaveRequest(**parsed_data)
    except ValidationError as e:
        return {"error": "VALIDATION_FAILED", "detail": e.errors()}

    # Call your new converter function
    result = converter_fill_excel_form(
        form_type=form_type,
        parsed_data=validated.dict(),
        user_id=user_id or 0
    )

    if "error" in result:
        return result

    return {
        "success": True,
        "type": "filled_excel_form",
        "file_path": result["file_path"]
    }
