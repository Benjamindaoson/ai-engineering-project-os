"""
Database Package

SQLite-based persistence layer for the AI Engineering Project OS.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import os


# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/ai_engineering.db")


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# ============================================================================
# Database Models
# ============================================================================

class Project(Base):
    """User's project being analyzed"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    github_url = Column(String(500), nullable=True)
    local_path = Column(String(1000), nullable=True)
    current_maturity = Column(String(50), default="idea")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship("RepositorySnapshot", back_populates="project", cascade="all, delete-orphan")
    facts = relationship("ProjectFact", back_populates="project", cascade="all, delete-orphan")
    assessments = relationship("MaturityAssessment", back_populates="project", cascade="all, delete-orphan")
    gaps = relationship("Gap", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("EngineeringTask", back_populates="project", cascade="all, delete-orphan")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")
    interviews = relationship("InterviewSession", back_populates="project", cascade="all, delete-orphan")


class RepositorySnapshot(Base):
    """Immutable snapshot of a repository at import time"""
    __tablename__ = "repository_snapshots"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    repo_url = Column(String(500), nullable=False)
    branch = Column(String(255), default="main")
    commit_sha = Column(String(40), nullable=False)
    workspace_path = Column(String(1000), nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="snapshots")


class ProjectFact(Base):
    """Extracted facts about a project"""
    __tablename__ = "project_facts"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    snapshot_id = Column(String(36), ForeignKey("repository_snapshots.id"), nullable=True)
    
    # Fact categories (stored as JSON)
    languages = Column(JSON, default=list)
    frameworks = Column(JSON, default=list)
    databases = Column(JSON, default=list)
    deployment = Column(JSON, default=list)
    
    # Code metrics
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    code_lines = Column(Integer, default=0)
    test_files = Column(Integer, default=0)
    config_files = Column(Integer, default=0)
    
    # Documentation
    has_readme = Column(Boolean, default=False)
    has_api_docs = Column(Boolean, default=False)
    has_deployment_docs = Column(Boolean, default=False)
    
    # Project type
    project_type = Column(String(50), default="other")
    
    # Raw observations (JSON)
    implementation_status = Column(JSON, default=dict)
    raw_observations = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="facts")
    snapshot = relationship("RepositorySnapshot")


class MaturityAssessment(Base):
    """Maturity assessment result"""
    __tablename__ = "maturity_assessments"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    snapshot_id = Column(String(36), ForeignKey("repository_snapshots.id"), nullable=True)
    
    overall_level = Column(String(50), nullable=False)
    dimension_scores = Column(JSON, default=dict)
    blockers = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="assessments")
    snapshot = relationship("RepositorySnapshot")


class Gap(Base):
    """Identified capability gap"""
    __tablename__ = "gaps"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    dimension = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    current_state = Column(Text, default="")
    target_state = Column(Text, default="")
    priority = Column(String(20), default="medium")
    effort_estimate = Column(String(20), default="medium")
    risk = Column(String(20), default="medium")
    related_criteria = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="gaps")
    tasks = relationship("EngineeringTask", back_populates="gap")


class EngineeringTask(Base):
    """Upgrade task"""
    __tablename__ = "engineering_tasks"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    gap_id = Column(String(36), ForeignKey("gaps.id"), nullable=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    
    # Learning content (JSON)
    learning_content = Column(JSON, default=dict)
    
    # Completion criteria (JSON)
    completion_criteria = Column(JSON, default=list)
    
    estimated_effort = Column(String(50), default="")
    prerequisites = Column(JSON, default=list)
    status = Column(String(20), default="pending")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    gap = relationship("Gap", back_populates="tasks")
    executions = relationship("ExecutionRun", back_populates="task", cascade="all, delete-orphan")


class ExecutionRun(Base):
    """Execution record"""
    __tablename__ = "execution_runs"
    
    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    # Changes (JSON)
    changes = Column(JSON, default=list)
    
    # Test results (JSON)
    test_results = Column(JSON, default=list)
    
    # Benchmark results (JSON)
    benchmark_results = Column(JSON, default=list)
    
    execution_log = Column(Text, default="")
    status = Column(String(20), default="pending")
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    task = relationship("EngineeringTask", back_populates="executions")
    project = relationship("Project")
    verifications = relationship("VerificationResult", back_populates="execution", cascade="all, delete-orphan")


class VerificationResult(Base):
    """Verification result"""
    __tablename__ = "verification_results"
    
    id = Column(String(36), primary_key=True)
    execution_id = Column(String(36), ForeignKey("execution_runs.id"), nullable=False)
    task_id = Column(String(36), nullable=False)
    
    verification_results = Column(JSON, default=list)
    overall_status = Column(String(20), default="unverifiable")
    missing_evidence = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    execution = relationship("ExecutionRun", back_populates="verifications")


class Evidence(Base):
    """Evidence record"""
    __tablename__ = "evidence"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    version_id = Column(String(36), ForeignKey("project_versions.id"), nullable=True)
    
    evidence_type = Column(String(50), nullable=False)
    source_path = Column(String(1000), nullable=False)
    title = Column(String(500), default="")
    description = Column(Text, default="")
    content = Column(Text, default="")
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")
    version = relationship("ProjectVersion", back_populates="evidence")


class ProjectVersion(Base):
    """Project version tracking"""
    __tablename__ = "project_versions"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    
    maturity_before = Column(String(50), nullable=True)
    maturity_after = Column(String(50), nullable=True)
    
    # Files changed (JSON)
    files_changed = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="versions")
    evidence = relationship("Evidence", back_populates="version", cascade="all, delete-orphan")


class InterviewSession(Base):
    """Interview session"""
    __tablename__ = "interview_sessions"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    task_id = Column(String(36), nullable=True)
    
    status = Column(String(20), default="in_progress")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    """Interview question"""
    __tablename__ = "interview_questions"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id"), nullable=False)
    
    question = Column(Text, nullable=False)
    context = Column(Text, default="")
    user_answer = Column(Text, nullable=True)
    follow_ups = Column(JSON, default=list)
    current_follow_up = Column(Integer, default=0)
    gap_type = Column(String(50), nullable=True)
    status = Column(String(20), default="pending")
    
    # Relationships
    session = relationship("InterviewSession", back_populates="questions")


# ============================================================================
# Database Engine Setup
# ============================================================================

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        yield session
