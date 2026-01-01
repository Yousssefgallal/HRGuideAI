from langchain.tools import tool

@tool("calculate_promotion_eligibility")
def calculate_promotion_eligibility(user_profile: dict) -> dict:
    """
    Calculates promotion eligibility for Lecturer → Associate Professor
    using the structured promotion calculation table.
    
    This tool uses the NEW table format:
    {
        "type": "promotion_table_data",
        "categories": [...],
        "footer": {
            "overall_total_numbers": 14,
            "overall_total_score": 18
        }
    }
    """

    from utils.promotion_table import PROMOTION_TABLE_LECTURER_TO_AP

    result = {
        "type": "promotion_eligibility",
        "eligible": False,
        "categories": [],
        "missing": [],
        "score_summary": {},
    }

    # Extract user academic data
    pubs = user_profile.get("publications_count", 0)
    single_authored = user_profile.get("single_authored_publications", 0)
    phd_supervision = user_profile.get("supervised_phd_students", 0)
    masters_supervision = user_profile.get("supervised_masters_students", 0)
    workshops = user_profile.get("workshops_organized", 0)
    research_funding = float(user_profile.get("research_funding_usd", 0))

    # Compute weighted scores using GIU rules
    publication_score = single_authored * 3 + (pubs - single_authored) * 1
    supervision_score = phd_supervision * 3 + masters_supervision * 1
    professional_score = workshops * 1   # simple scoring

    # Iterate through the table categories
    for category in PROMOTION_TABLE_LECTURER_TO_AP["categories"]:
        title = category["title"]
        rows = category["rows"]

        actual_numbers = 0
        actual_score = 0
        required_numbers = 0
        required_score = 0

        # Compute totals per category based on row definitions
        for row in rows:
            required_numbers += row["min_required_numbers"]
            required_score += row["min_required_score"]

        # Map user data → category
        if title == "Publication Records":
            actual_numbers = pubs
            actual_score = publication_score

        elif title == "Supervision Records":
            actual_numbers = phd_supervision + masters_supervision
            actual_score = supervision_score

        elif title == "Professional Activities Records":
            actual_numbers = workshops  # count of workshops
            actual_score = professional_score

        category_result = {
            "title": title,
            "actual_numbers": actual_numbers,
            "actual_score": actual_score,
            "required_numbers": required_numbers,
            "required_score": required_score,
        }

        # Check missing requirements
        if actual_numbers < required_numbers:
            category_result["missing_numbers"] = required_numbers - actual_numbers
            result["missing"].append(
                f"{title}: Missing {required_numbers - actual_numbers} numbers"
            )

        if actual_score < required_score:
            category_result["missing_score"] = required_score - actual_score
            result["missing"].append(
                f"{title}: Missing {required_score - actual_score} weighted score"
            )

        result["categories"].append(category_result)

    # OVERALL TOTALS (from table footer)
    required_total_numbers = PROMOTION_TABLE_LECTURER_TO_AP["footer"]["overall_total_numbers"]
    required_total_score = PROMOTION_TABLE_LECTURER_TO_AP["footer"]["overall_total_score"]

    total_actual_numbers = sum(c["actual_numbers"] for c in result["categories"])
    total_actual_score = sum(c["actual_score"] for c in result["categories"])

    result["score_summary"] = {
        "total_actual_numbers": total_actual_numbers,
        "total_actual_score": total_actual_score,
        "required_numbers": required_total_numbers,
        "required_score": required_total_score,
    }

    # Determine eligibility
    result["eligible"] = (
        total_actual_numbers >= required_total_numbers and
        total_actual_score >= required_total_score
    )

    return result
