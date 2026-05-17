from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_profile: Mapped[dict | None] = mapped_column(JSONB)
    parsing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    parsing_error: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", back_populates="resumes")
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    projects = relationship("ResumeProject", back_populates="resume", cascade="all, delete-orphan")


class ResumeSkill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_skills"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    skill_category: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    evidence: Mapped[str | None] = mapped_column(Text)

    resume = relationship("Resume", back_populates="skills")


class ResumeProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_projects"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[dict | None] = mapped_column(JSONB)
    impact: Mapped[str | None] = mapped_column(Text)
    extracted_facts: Mapped[dict | None] = mapped_column(JSONB)

    resume = relationship("Resume", back_populates="projects")


class JobDescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_descriptions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255))
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_requirements: Mapped[dict | None] = mapped_column(JSONB)
