# backend/models.py
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Numeric, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from database.db_connection import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    role_type = Column(String(20), nullable=False)  # 'academic' or 'administrative'
    faculty_or_department = Column(String(100))
    position_title = Column(String(100))
    contract_type = Column(String(50))  # 'full-time', 'part-time', 'temporary'
    hire_date = Column(DateTime, nullable=False)
    date_of_birth = Column(DateTime)
    service_years = Column(Integer, default=0)
    social_insurance_years = Column(Integer, default=0)
    probation_period = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)


    # Relationships
    academic_profile = relationship("AcademicProfile", back_populates="user", uselist=False)
    leave_balance = relationship("LeaveBalance", back_populates="user", uselist=False)
    trainings = relationship("TrainingRecord", back_populates="user")


class AcademicProfile(Base):
    __tablename__ = "academic_profile"

    academic_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    phd_awarded_year = Column(Integer)
    last_promotion_year = Column(Integer)
    publications_count = Column(Integer, default=0)
    single_authored_publications = Column(Integer, default=0)
    h_index = Column(Integer, default=0)
    supervised_phd_students = Column(Integer, default=0)
    supervised_masters_students = Column(Integer, default=0)
    research_funding_usd = Column(Numeric(12, 2), default=0)
    workshops_organized = Column(Integer, default=0)
    awards_count = Column(Integer, default=0)
    promotion_eligibility_score = Column(Numeric(5, 2))
    eligible_for_promotion = Column(Boolean, default=False)

    user = relationship("User", back_populates="academic_profile")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    leave_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    annual_entitlement = Column(Integer, default=21)
    annual_taken = Column(Integer, default=0)
    accidental_entitlement = Column(Integer, default=6)
    accidental_taken = Column(Integer, default=0)
    sick_entitlement = Column(Integer, default=180)
    sick_taken = Column(Integer, default=0)
    compensation_balance = Column(Integer, default=0)
    unpaid_balance = Column(Integer, default=0)
    maternity_entitlement = Column(Integer, default=90)
    maternity_taken = Column(Integer, default=0)
    marriage_leave_entitlement = Column(Integer, default=10)
    marriage_leave_taken = Column(Integer, default=0)
    last_leave_date = Column(DateTime)

    user = relationship("User", back_populates="leave_balance")


class TrainingRecord(Base):
    __tablename__ = "training_records"

    training_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    training_title = Column(String(200), nullable=False)
    provider = Column(String(150))
    completion_date = Column(DateTime)
    certificate_url = Column(String(255))

    user = relationship("User", back_populates="trainings")


# ================================
# Conversations + Messages Tables
# ================================

class Conversation(Base):
    __tablename__ = "conversations"
    conversation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    title = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    thread_id = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship to user
    user = relationship("User", backref="conversations")

    # Relationship to messages
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"
    message_id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.conversation_id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)
    content = Column(JSONB, nullable=False)  # store as JSONB
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to conversation
    conversation = relationship("Conversation", back_populates="messages")
