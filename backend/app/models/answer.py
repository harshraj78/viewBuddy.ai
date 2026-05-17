from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Answer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "answers"

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    question = relationship("Question", back_populates="answers")
    score = relationship(
        "AnswerScore",
        back_populates="answer",
        uselist=False,
        cascade="all, delete-orphan",
    )
    feedback_items = relationship(
        "FeedbackItem",
        back_populates="answer",
        cascade="all, delete-orphan",
    )


class AnswerScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "answer_scores"

    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"),
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    correctness_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    clarity_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    depth_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    structure_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    rubric: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)

    answer = relationship("Answer", back_populates="score")


class FeedbackItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback_items"

    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"),
        index=True,
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_improvement: Mapped[str | None] = mapped_column(Text)

    answer = relationship("Answer", back_populates="feedback_items")
