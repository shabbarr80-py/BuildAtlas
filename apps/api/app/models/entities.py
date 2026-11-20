import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

JSON_VALUE = JSONB().with_variant(JSON(), "sqlite")


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    projects: Mapped[list["Project"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("status IN ('created', 'archived')", name="ck_projects_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    constraints: Mapped[dict] = mapped_column(JSON_VALUE, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship(back_populates="projects")
    analyses: Mapped[list["AnalysisRun"]] = relationship(cascade="all, delete-orphan")
    milestones: Mapped[list["RoadmapMilestone"]] = relationship(cascade="all, delete-orphan")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')", name="ck_analysis_runs_status"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON_VALUE, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON_VALUE, nullable=True)
    provider: Mapped[str] = mapped_column(String(80), default="mock")
    model: Mapped[str] = mapped_column(String(120), default="deterministic")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResearchSource(Base):
    __tablename__ = "research_sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    source_type: Mapped[str] = mapped_column(String(40))
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300))
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RepositoryCandidate(Base):
    __tablename__ = "repository_candidates"
    __table_args__ = (UniqueConstraint("analysis_run_id", "html_url"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    full_name: Mapped[str] = mapped_column(String(240))
    html_url: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    stars: Mapped[int] = mapped_column(Integer)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    rationale: Mapped[str] = mapped_column(Text)
    alternatives: Mapped[list] = mapped_column(JSON_VALUE, default=list)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=True)


class RoadmapMilestone(Base):
    __tablename__ = "roadmap_milestones"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    position: Mapped[int] = mapped_column(Integer)
    tasks: Mapped[list["RoadmapTask"]] = relationship(cascade="all, delete-orphan")


class RoadmapTask(Base):
    __tablename__ = "roadmap_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('todo', 'in_progress', 'done')", name="ck_roadmap_tasks_status"
        ),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_roadmap_tasks_priority"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_milestones.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="todo")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
