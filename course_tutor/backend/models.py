from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    session_token = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), nullable=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserLessonProgress", back_populates="user", cascade="all, delete-orphan")
    state = relationship("UserState", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (Index("ix_courses_slug", "slug", unique=True),)

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))
    is_published = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), nullable=True)

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (Index("ix_modules_course_slug", "course_id", "slug", unique=True),)

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))

    course = relationship("Course", back_populates="modules")
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (Index("ix_topics_module_slug", "module_id", "slug", unique=True),)

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))

    module = relationship("Module", back_populates="topics")
    lessons = relationship("Lesson", back_populates="topic", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("topic_id", "slug", name="uq_lessons_topic_slug"),)

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))
    lesson_type = Column(String(50), nullable=False, default="concept", server_default=text("'concept'"))
    difficulty = Column(String(50), nullable=False, default="beginner", server_default=text("'beginner'"))
    objective = Column(Text, nullable=True)
    practice_task = Column(Text, nullable=True)
    common_confusions = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    examples = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    tags = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    raw_json = Column(JSONB, nullable=True)

    topic = relationship("Topic", back_populates="lessons")
    contents = relationship("LessonContent", back_populates="lesson", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="lesson", cascade="all, delete-orphan")
    practice_exercises = relationship("PracticeExercise", back_populates="lesson", cascade="all, delete-orphan")
    labs = relationship("Lab", back_populates="lesson", cascade="all, delete-orphan")
    progress = relationship("UserLessonProgress", back_populates="lesson", cascade="all, delete-orphan")


class LessonContent(Base):
    __tablename__ = "lesson_contents"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(50), nullable=False)
    content_type = Column(String(50), nullable=False, default="explanation", server_default=text("'explanation'"))
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))

    lesson = relationship("Lesson", back_populates="contents")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    level = Column(String, nullable=False)
    question_type = Column(String(50), nullable=False, default="mcq", server_default=text("'mcq'"))
    question = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False, default=list)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=True, default="medium", server_default=text("'medium'"))
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))

    lesson = relationship("Lesson", back_populates="questions")


class PracticeExercise(Base):
    __tablename__ = "practice_exercises"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    allowed_commands = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))
    is_required = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), nullable=True)

    lesson = relationship("Lesson", back_populates="practice_exercises")


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))
    is_required = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), nullable=True)

    lesson = relationship("Lesson", back_populates="labs")
    tasks = relationship("LabTask", back_populates="lab", cascade="all, delete-orphan")


class LabTask(Base):
    __tablename__ = "lab_tasks"

    id = Column(Integer, primary_key=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    instruction = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    allowed_commands = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    validation = Column(JSONB, nullable=True)
    sequence = Column(Integer, nullable=False, default=1, server_default=text("1"))

    lab = relationship("Lab", back_populates="tasks")


class LabSession(Base):
    __tablename__ = "lab_sessions"
    __table_args__ = (UniqueConstraint("user_id", "lab_id", name="uq_lab_sessions_user_lab"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    current_working_directory = Column(
        Text,
        nullable=False,
        default="/workspace",
        server_default=text("'/workspace'"),
    )
    command_history = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    completed_tasks = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress_user_lesson"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="locked", server_default=text("'locked'"))
    current_level = Column(String(50), nullable=False, default="standard", server_default=text("'standard'"))
    read_completed = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    quiz_unlocked = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    quiz_completed = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    last_score = Column(Integer, nullable=True)
    best_score = Column(Integer, nullable=True)
    attempts = Column(Integer, nullable=False, default=0, server_default=text("0"))
    mastery_status = Column(String(50), nullable=False, default="not_started", server_default=text("'not_started'"))
    hint_usage = Column(Integer, nullable=False, default=0, server_default=text("0"))
    confidence = Column(Integer, nullable=False, default=0, server_default=text("0"))
    question_history = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), nullable=True)

    user = relationship("User", back_populates="sessions")


class UserState(Base):
    __tablename__ = "user_state"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    current_module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    current_topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    current_lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    current_level = Column(String, nullable=False, default="standard")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    user = relationship("User", back_populates="state")
    current_lesson = relationship("Lesson", foreign_keys=[current_lesson_id])
