# backend/scripts/seed_db.py

import bcrypt
from datetime import datetime
from sqlalchemy.orm import Session

from database.db_connection import engine, Base
from database.models_postgres import (
    User,
    AcademicProfile,
    LeaveBalance,
    TrainingRecord
)

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def user_exists(session: Session, email: str, employee_id: str) -> bool:
    return session.query(User).filter(
        (User.email == email) | (User.employee_id == employee_id)
    ).first() is not None

# -------------------------------------------------
# Seed Function
# -------------------------------------------------

def seed_database():
    print("🌱 Seeding database...")

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:

        # =================================================
        # USER 1 — Academic (Lecturer)
        # =================================================
        # if not user_exists(session, "caroline.sabty@giu-uni.de", "GIU-AC-001"):
        #     user1 = User(
        #         employee_id="GIU-AC-001",
        #         full_name="Dr. Caroline Sabty",
        #         role_type="academic",
        #         faculty_or_department="Informatics and Computer Science",
        #         position_title="Lecturer",
        #         contract_type="full-time",
        #         hire_date=datetime(2018, 9, 1),
        #         date_of_birth=datetime(1985, 6, 12),
        #         service_years=6,
        #         social_insurance_years=6,
        #         probation_period=False,
        #         is_active=True,
        #         is_admin=False,
        #         email="caroline.sabty@giu-uni.de",
        #         password=hash_password("112233")
        #     )

        #     session.add(user1)
        #     session.flush()  # get user_id

        #     session.add(AcademicProfile(
        #         user_id=user1.user_id,
        #         phd_awarded_year=2017,
        #         last_promotion_year=2019,
        #         publications_count=8,
        #         single_authored_publications=2,
        #         h_index=6,
        #         supervised_phd_students=1,
        #         supervised_masters_students=3,
        #         research_funding_usd=150000,
        #         workshops_organized=2,
        #         awards_count=1,
        #         promotion_eligibility_score=17.5,
        #         eligible_for_promotion=False
        #     ))

        #     session.add(LeaveBalance(
        #         user_id=user1.user_id,
        #         annual_entitlement=21,
        #         annual_taken=10,
        #         accidental_entitlement=6,
        #         accidental_taken=1,
        #         sick_entitlement=180,
        #         sick_taken=5,
        #         marriage_leave_entitlement=10,
        #         marriage_leave_taken=0
        #     ))

        #     print("✅ Seeded academic user: Dr Caroline")

        # =================================================
        # USER 2 — Academic (Associate Professor)
        # =================================================
        if not user_exists(session, "yasmeen.hamdy@giu-uni.de", "8113"):
            user2 = User(
                employee_id="8113",
                full_name="Dr. Yassmeen",
                role_type="Administrative",
                faculty_or_department="Academic performance",
                position_title="Senior academic co-ordinator",
                contract_type="full-time",
                hire_date=datetime(2021, 1, 8),
                date_of_birth=datetime(1997, 3, 18),
                service_years=5,
                social_insurance_years=5,
                probation_period=False,
                is_active=True,
                is_admin=True,
                email="yasmeen.hamdy@giu-uni.de",
                password=hash_password("112233")
            )

            session.add(user2)
            session.flush()

            

            session.add(LeaveBalance(
                user_id=user2.user_id,
                annual_entitlement=21,
                annual_taken=21,
                accidental_entitlement=6,
                accidental_taken=6,
                sick_entitlement=180,
                sick_taken=0
            ))

            print("✅ Seeded academic admin: yasmeen.hamdy")

        # =================================================
        # USER 3 — Administrative Staff
        # =================================================
        # if not user_exists(session, "mona.ali@giu.edu.eg", "GIU-AD-001"):
        #     user3 = User(
        #         employee_id="GIU-AD-001",
        #         full_name="Mona Ali",
        #         role_type="administrative",
        #         faculty_or_department="Human Resources",
        #         position_title="HR Officer",
        #         contract_type="full-time",
        #         hire_date=datetime(2020, 7, 1),
        #         date_of_birth=datetime(1990, 9, 5),
        #         service_years=4,
        #         social_insurance_years=4,
        #         probation_period=False,
        #         is_active=True,
        #         is_admin=True,
        #         email="mona.ali@giu.edu.eg",
        #         password=hash_password("Password123!")
        #     )

        #     session.add(user3)
        #     session.flush()

        #     session.add(LeaveBalance(
        #         user_id=user3.user_id,
        #         annual_entitlement=21,
        #         annual_taken=6,
        #         accidental_entitlement=6,
        #         accidental_taken=2,
        #         sick_entitlement=180,
        #         sick_taken=1
        #     ))

            # print("✅ Seeded administrative user: Mona Ali")

        # =================================================
        session.commit()
        print("🌱 Database seeding completed successfully.")

# -------------------------------------------------
# Entry Point
# -------------------------------------------------

if __name__ == "__main__":
    seed_database()
