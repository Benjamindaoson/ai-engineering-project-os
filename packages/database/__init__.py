"""
Database Package

SQLite-based persistence layer.
"""

from packages.database.models import (
    Base,
    Project,
    RepositorySnapshot,
    ProjectFact,
    MaturityAssessment,
    Gap,
    EngineeringTask,
    ExecutionRun,
    VerificationResult,
    Evidence,
    ProjectVersion,
    InterviewSession,
    InterviewQuestion,
    init_db,
    get_session,
    engine,
    async_session,
    DATABASE_URL,
)

from packages.database.repositories import (
    ProjectRepository,
    SnapshotRepository,
    FactRepository,
    AssessmentRepository,
    GapRepository,
    TaskRepository,
    ExecutionRepository,
    VerificationRepository,
    EvidenceRepository,
    VersionRepository,
    InterviewRepository,
)

__all__ = [
    # Models
    "Base",
    "Project",
    "RepositorySnapshot",
    "ProjectFact",
    "MaturityAssessment",
    "Gap",
    "EngineeringTask",
    "ExecutionRun",
    "VerificationResult",
    "Evidence",
    "ProjectVersion",
    "InterviewSession",
    "InterviewQuestion",
    # Initialization
    "init_db",
    "get_session",
    "engine",
    "async_session",
    "DATABASE_URL",
    # Repositories
    "ProjectRepository",
    "SnapshotRepository",
    "FactRepository",
    "AssessmentRepository",
    "GapRepository",
    "TaskRepository",
    "ExecutionRepository",
    "VerificationRepository",
    "EvidenceRepository",
    "VersionRepository",
    "InterviewRepository",
]
