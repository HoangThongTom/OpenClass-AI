from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(150), nullable=False)
    slide_count: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class LessonWorkspace(Base):
    __tablename__ = "lesson_workspaces"

    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)


class LessonDocument(Base):
    __tablename__ = "lesson_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    pages: Mapped[list] = mapped_column(JSON, nullable=False)
