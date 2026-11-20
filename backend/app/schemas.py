from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    excerpt: str


class SlideEdit(BaseModel):
    title: str = Field(min_length=1)
    key_point: str = Field(min_length=1)
    bullets: list[str] = Field(min_length=1, max_length=5)
    speaker_notes: str = ""


class Slide(SlideEdit):
    sources: list[Citation] = Field(default_factory=list)


class OutlineItem(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    focus: str = Field(min_length=1, max_length=600)


class OutlineContent(BaseModel):
    summary: str = Field(min_length=1, max_length=1200)
    slides: list[OutlineItem] = Field(min_length=2, max_length=6)


class WorkspaceOut(BaseModel):
    mode: Literal["fast", "balanced"] = "fast"
    outline: OutlineContent | None = None
    stage: str = "outline"
    approved: bool = False
    completed_slides: int = 0
    elapsed_seconds: float = 0
    last_run_seconds: float = 0
    source_warning: str | None = None


class QuizItem(BaseModel):
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = ""

    @model_validator(mode="after")
    def correct_answer_in_range(self):
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index must point at an option")
        return self


class Flashcard(BaseModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)


class LessonContent(BaseModel):
    summary: str = Field(min_length=1)
    slides: list[Slide] = Field(min_length=1, max_length=8)
    quiz: list[QuizItem] = Field(default_factory=list, max_length=6)
    flashcards: list[Flashcard] = Field(default_factory=list, max_length=8)


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    topic: str
    model: str
    slide_count: int
    status: Literal["draft", "generating", "ready", "failed"]
    source_name: str | None
    created_at: datetime
    content: LessonContent | None = None
    error: str | None = None
    workspace: WorkspaceOut | None = None


class ModelList(BaseModel):
    online: bool
    models: list[str]
    error: str | None = None


class RegenerateLesson(BaseModel):
    model: str | None = Field(default=None, min_length=1, max_length=150)
    slide_count: int | None = Field(default=None, ge=2, le=6)
    mode: Literal["fast", "balanced"] | None = None
