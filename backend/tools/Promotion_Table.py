from langchain.tools import tool
from utils.promotion_table import PROMOTION_TABLE_LECTURER_TO_AP


@tool("get_promotion_calculation_table")
def get_promotion_calculation_table() -> dict:
    """
    Returns the official GIU promotion calculation table for Lecturer → Associate Professor.
    Use this tool when the user asks about promotion criteria, requirements, or how promotion is evaluated.
    """
    return PROMOTION_TABLE_LECTURER_TO_AP
