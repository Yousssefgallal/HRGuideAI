# backend/utils/form_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from datetime import date, time
from dateutil import parser as date_parser


# ----------------------
# Leave (annual / accidental / marriage)
# ----------------------
class AnnualAccidentalMarriageLeaveForm(BaseModel):
    form_type: Literal["annual", "accidental", "marriage"] = Field(...)

    name: str
    id: str
    faculty_or_department: str
    academic_or_non_academic: Literal["academic", "non_academic"]
    fulltime_or_parttime: Literal["full_time", "part_time"]
    start_date: date
    end_date: date
    number_of_days: int

    # Accept flexible input for dates (strings)
    @validator("start_date", "end_date", pre=True)
    def _parse_date(cls, v):
        if isinstance(v, date):
            return v
        if v is None or v == "":
            raise ValueError("date required")
        return date_parser.parse(v).date()


# ----------------------
# Excuse form
# ----------------------
class ExcuseForm(BaseModel):
    form_type: Literal["excuse"] = Field("excuse")
    name: str
    id: str
    department: str
    academic_or_non_academic: Literal["academic", "non_academic"]
    fulltime_or_parttime: Literal["full_time", "part_time"]
    excuse_date: date
    from_time: time
    to_time: time

    @validator("excuse_date", pre=True)
    def _parse_excuse_date(cls, v):
        if isinstance(v, date):
            return v
        return date_parser.parse(v).date()

    @validator("from_time", "to_time", pre=True)
    def _parse_time(cls, v):
        if isinstance(v, time):
            return v
        # dateutil can parse times as datetimes; extract time
        return date_parser.parse(v).time()


# ----------------------
# Maternity form
# ----------------------
class MaternityLeaveForm(BaseModel):
    form_type: Literal["maternity"] = Field("maternity")
    name: str
    id: str
    department: str
    academic_or_non_academic: Literal["academic", "non_academic"]
    fulltime_or_parttime: Literal["full_time", "part_time"]
    start_date: date
    end_date: date
    total_leave_days: int
    medical_report: Literal["attached", "not_attached"]
    birth_certificate: Literal["attached", "not_attached"]

    @validator("start_date", "end_date", pre=True)
    def _parse_date(cls, v):
        if isinstance(v, date):
            return v
        return date_parser.parse(v).date()


# ----------------------
# Mission form
# ----------------------
class MissionForm(BaseModel):
    form_type: Literal["mission"] = Field("mission")
    name: str
    department: str
    academic_or_non_academic: Literal["academic", "non_academic"]
    fulltime_or_parttime: Literal["full_time", "part_time"]
    start_date: date
    end_date: date
    from_time: time
    to_time: time
    mission_destination: Optional[str] = None

    @validator("start_date", "end_date", pre=True)
    def _parse_date(cls, v):
        if isinstance(v, date):
            return v
        return date_parser.parse(v).date()

    @validator("from_time", "to_time", pre=True)
    def _parse_time(cls, v):
        if isinstance(v, time):
            return v
        return date_parser.parse(v).time()


# ----------------------
# Incomplete attendance form
# ----------------------
class IncompleteAttendanceForm(BaseModel):
    form_type: Literal["attendance"] = Field("attendance")
    name: str
    id: str
    faculty: str
    department: str
    missing_date: date
    missing_from_time: Optional[time] = None
    missing_to_time: Optional[time] = None

    @validator("missing_date", pre=True)
    def _parse_missing_date(cls, v):
        if isinstance(v, date):
            return v
        return date_parser.parse(v).date()

    @validator("missing_from_time", "missing_to_time", pre=True)
    def _parse_time_optional(cls, v):
        if v is None or v == "":
            return None
        return date_parser.parse(v).time()


# ----------------------
# registry for lookup
# ----------------------
SCHEMA_REGISTRY = {
    "annual": AnnualAccidentalMarriageLeaveForm,
    "accidental": AnnualAccidentalMarriageLeaveForm,
    "marriage": AnnualAccidentalMarriageLeaveForm,
    "excuse": ExcuseForm,
    "maternity": MaternityLeaveForm,
    "mission": MissionForm,
    "attendance": IncompleteAttendanceForm,
}
