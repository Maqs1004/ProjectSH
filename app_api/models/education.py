import enum
import datetime

from sqlalchemy.dialects.postgresql import JSONB

from ..db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, String, JSON, Float, Enum, Text


class QuestionType(enum.Enum):
    open = "open"
    multiple_choice = "multiple_choice"


class CurrentStage(enum.Enum):
    not_generated = "not_generated"
    generating = "generating"
    generated = "generated"
    education = "education"
    question = "question"
    ask_question = "ask_question"
    waiting_response = "waiting_user_response"
    completed = "completed"


class ContentType(enum.Enum):
    text = "text"
    image = "image"


class UserCourseTracker(Base):
    __tablename__ = "user_course_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255))
    current_module_id = Column(Integer, default=None)
    current_sub_module_id = Column(Integer, default=None)
    current_stage = Column(Enum(CurrentStage))
    current_order_number = Column(Integer, default=1)
    plan = Column(JSONB, default=None)
    active = Column(Boolean, default=True)
    archived = Column(Boolean, default=False)
    finished = Column(Boolean, default=False)
    input_token = Column(Integer, default=0)
    output_token = Column(Integer, default=0)
    spent_amount = Column(Float, default=0)
    usage_count = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    user = relationship("Users", back_populates="user_course")
    course = relationship("Courses", back_populates="user_course")


class Courses(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    description = Column(String(255), default=None)
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    summary = Column(Text, default=None)
    stat_modul_id = Column(Integer, nullable=True)
    stat_sub_modul_id = Column(Integer, nullable=True)
    default_plan = Column(JSONB, default=None)
    is_personalized = Column(Boolean, default=False)
    is_generated = Column(Boolean, default=False)
    user_course = relationship("UserCourseTracker", back_populates="course")
    module = relationship("Modules", back_populates="course", cascade="all, delete-orphan")


class Modules(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255))
    description = Column(String(255), default=None)
    order_number = Column(Integer, default=None)
    course = relationship("Courses", back_populates="module")
    sub_module = relationship("SubModules", back_populates="module", cascade="all, delete-orphan")


class SubModules(Base):
    __tablename__ = "sub_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String(255))
    description = Column(String(255), default=None)
    order_number = Column(Integer, default=None)
    module = relationship("Modules", back_populates="sub_module")
    question = relationship("Questions", back_populates="sub_module", cascade="all, delete-orphan")
    module_content = relationship("ModuleContents", back_populates="sub_module", cascade="all, delete-orphan")


class ModuleContents(Base):
    __tablename__ = "module_contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_module_id = Column(Integer, ForeignKey("sub_modules.id"), nullable=False)
    title = Column(String(255))
    content_type = Column(Enum(ContentType), default=None)
    content_data = Column(JSON, default=None)
    order_number = Column(Integer, default=None)
    sub_module = relationship("SubModules", back_populates="module_content")


class Questions(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_module_id = Column(Integer, ForeignKey("sub_modules.id"), nullable=False)
    content = Column(Text, default=None)
    question_type = Column(Enum(QuestionType))
    options = Column(JSON, default=None)
    order_number = Column(Integer, default=None)
    sub_module = relationship("SubModules", back_populates="question")
    answer = relationship("UserAnswers", back_populates="question")


class UserAnswers(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), default=None)
    answer = Column(Text)
    score = Column(Integer, default=None)
    feedback = Column(Text, default=None)
    question = relationship("Questions", back_populates="answer")
    user = relationship("Users", back_populates="answer")
