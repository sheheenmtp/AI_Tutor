from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    DateTime,
    Boolean,
    create_engine,
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()


# ================= PROBLEM =================
class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    starter_code = Column(Text, default="# Write your code here\n")
    hints = Column(JSON, nullable=True)

    input_format = Column(Text, nullable=False)
    output_format = Column(Text, nullable=False)

    # ✅ REQUIRED RELATIONSHIPS
    test_cases = relationship(
        "TestCase",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

    submissions = relationship(
        "Submission",
        back_populates="problem",
        cascade="all, delete-orphan"
    )


# ================= TEST CASE =================
class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)

    input_data = Column(Text, default="")
    expected_output = Column(Text, nullable=False)

    is_sample = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    points = Column(Integer, default=10)

    problem = relationship(
        "Problem",
        back_populates="test_cases"
    )


# ================= USER =================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)

    current_level = Column(String(20), default="beginner")
    total_score = Column(Integer, default=0)
    problems_solved = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship(
        "Submission",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ================= SUBMISSION =================
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)

    code = Column(Text, nullable=False)
    status = Column(String(20))

    passed_tests = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    score = Column(Integer, default=0)

    submitted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")


# ================= DB SETUP =================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

