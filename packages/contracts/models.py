"""
Contracts Package

Shared data models and type definitions for the AI Engineering Project OS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProjectType(str, Enum):
    RAG = "rag"
    AGENT = "agent"
    CHATBOT = "chatbot"
    API = "api"
    FULLSTACK = "fullstack"
    OTHER = "other"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GapPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortEstimate(str, Enum):
    SMALL = "small"      # < 1 day
    MEDIUM = "medium"    # 1-3 days
    LARGE = "large"     # > 3 days


class GapRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImplementationStatusType(str, Enum):
    FULLY_IMPLEMENTED = "fully_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    DOCUMENTED_ONLY = "documented_only"
    PLANNED = "planned"
    MISSING = "missing"


# ============================================================================
# Project & Facts
# ============================================================================

@dataclass
class ProjectFacts:
    """Facts extracted from a project during audit"""
    project_name: str = ""
    project_type: ProjectType = ProjectType.OTHER
    main_language: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    database: list[str] = field(default_factory=list)
    deployment: list[str] = field(default_factory=list)
    
    # Code metrics
    total_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    test_files: int = 0
    test_lines: int = 0
    config_files: int = 0
    
    # Documentation
    has_readme: bool = False
    has_api_docs: bool = False
    has_deployment_docs: bool = False
    has_contributing: bool = False
    
    # Implementation status by category
    implementation_status: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    
    # Raw observations
    raw_observations: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_type": self.project_type.value if isinstance(self.project_type, Enum) else self.project_type,
            "main_language": self.main_language,
            "frameworks": self.frameworks,
            "database": self.database,
            "deployment": self.deployment,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "test_files": self.test_files,
            "test_lines": self.test_lines,
            "config_files": self.config_files,
            "has_readme": self.has_readme,
            "has_api_docs": self.has_api_docs,
            "has_deployment_docs": self.has_deployment_docs,
            "has_contributing": self.has_contributing,
            "implementation_status": self.implementation_status,
            "raw_observations": self.raw_observations,
        }


# ============================================================================
# Gaps
# ============================================================================

@dataclass
class Gap:
    """An identified gap in project capabilities"""
    id: str
    project_id: str
    dimension: str
    description: str
    current_state: str
    target_state: str
    priority: GapPriority = GapPriority.MEDIUM
    effort_estimate: EffortEstimate = EffortEstimate.MEDIUM
    risk: GapRisk = GapRisk.MEDIUM
    related_criteria: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "dimension": self.dimension,
            "description": self.description,
            "current_state": self.current_state,
            "target_state": self.target_state,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "effort_estimate": self.effort_estimate.value if isinstance(self.effort_estimate, Enum) else self.effort_estimate,
            "risk": self.risk.value if isinstance(self.risk, Enum) else self.risk,
            "related_criteria": self.related_criteria,
            "created_at": self.created_at,
        }


# ============================================================================
# Upgrade Tasks
# ============================================================================

@dataclass
class LearningContent:
    """Content for learning about an upgrade task"""
    problem_explanation: str = ""
    why_important: str = ""
    simple_solution: str = ""
    why_simple_not_enough: str = ""
    production_approach: str = ""
    recommended_solution: str = ""
    reasoning: str = ""
    verification_method: str = ""
    interview_questions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_explanation": self.problem_explanation,
            "why_important": self.why_important,
            "simple_solution": self.simple_solution,
            "why_simple_not_enough": self.why_simple_not_enough,
            "production_approach": self.production_approach,
            "recommended_solution": self.recommended_solution,
            "reasoning": self.reasoning,
            "verification_method": self.verification_method,
            "interview_questions": self.interview_questions,
        }


@dataclass
class CompletionCriterion:
    """A criterion for task completion"""
    criterion: str
    verification_method: str
    evidence_type: str  # "code", "test", "run_result", "benchmark", "config"


@dataclass
class UpgradeTask:
    """A task to upgrade project maturity"""
    id: str
    project_id: str
    gap_id: str
    title: str
    description: str
    learning_content: LearningContent
    completion_criteria: list[CompletionCriterion] = field(default_factory=list)
    estimated_effort: str = ""
    prerequisites: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "gap_id": self.gap_id,
            "title": self.title,
            "description": self.description,
            "learning_content": self.learning_content.to_dict() if isinstance(self.learning_content, LearningContent) else self.learning_content,
            "completion_criteria": [
                {"criterion": c.criterion, "verification_method": c.verification_method, "evidence_type": c.evidence_type}
                for c in self.completion_criteria
            ],
            "estimated_effort": self.estimated_effort,
            "prerequisites": self.prerequisites,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


# ============================================================================
# Execution Records
# ============================================================================

@dataclass
class CodeChange:
    """A code change made during execution"""
    file_path: str
    change_type: str  # "added", "modified", "deleted"
    diff: str
    purpose: str


@dataclass
class TestResult:
    """Result of a test execution"""
    test_name: str
    passed: bool
    duration_ms: float
    error: str | None = None


@dataclass
class BenchmarkResult:
    """Result of a benchmark"""
    metric: str
    before_value: float | None = None
    after_value: float | None = None
    improvement: float | None = None
    unit: str = ""


@dataclass
class ExecutionRecord:
    """Record of a task execution"""
    id: str
    task_id: str
    project_id: str
    changes: list[CodeChange] = field(default_factory=list)
    execution_log: str = ""
    test_results: list[TestResult] = field(default_factory=list)
    benchmark_results: list[BenchmarkResult] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "changes": [
                {"file_path": c.file_path, "change_type": c.change_type, "diff": c.diff, "purpose": c.purpose}
                for c in self.changes
            ],
            "execution_log": self.execution_log,
            "test_results": [
                {"test_name": t.test_name, "passed": t.passed, "duration_ms": t.duration_ms, "error": t.error}
                for t in self.test_results
            ],
            "benchmark_results": [
                {"metric": b.metric, "before_value": b.before_value, "after_value": b.after_value,
                 "improvement": b.improvement, "unit": b.unit}
                for b in self.benchmark_results
            ],
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


# ============================================================================
# Architecture Decisions
# ============================================================================

@dataclass
class ArchitectureDecision:
    """A recorded architecture decision"""
    id: str
    project_id: str
    task_id: str | None
    title: str
    context: str
    decision: str
    consequences: str
    alternatives_considered: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "title": self.title,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "alternatives_considered": self.alternatives_considered,
            "created_at": self.created_at,
        }


# ============================================================================
# Interview
# ============================================================================

@dataclass
class InterviewQuestion:
    """A question in an interview session"""
    id: str
    session_id: str
    question: str
    context: str
    user_answer: str | None = None
    follow_ups: list[str] = field(default_factory=list)
    current_follow_up: int = 0
    gap_type: str | None = None  # "knowledge", "engineering", "evidence", "experiment"
    status: str = "pending"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question": self.question,
            "context": self.context,
            "user_answer": self.user_answer,
            "follow_ups": self.follow_ups,
            "current_follow_up": self.current_follow_up,
            "gap_type": self.gap_type,
            "status": self.status,
        }


@dataclass
class InterviewSession:
    """A complete interview session"""
    id: str
    project_id: str
    task_id: str | None
    questions: list[InterviewQuestion] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: str | None = None
    status: str = "in_progress"  # "in_progress", "completed"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "questions": [q.to_dict() for q in self.questions],
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
        }


# ============================================================================
# Capability Profile
# ============================================================================

@dataclass
class InterviewPerformance:
    """Interview performance metrics"""
    total_questions: int = 0
    answered_correctly: int = 0
    gaps: list[str] = field(default_factory=list)


@dataclass
class DimensionCapability:
    """Capability in a specific dimension"""
    dimension: str
    level: str
    evidence_ids: list[str] = field(default_factory=list)
    interview_performance: InterviewPerformance = field(default_factory=InterviewPerformance)


@dataclass
class CapabilityProfile:
    """Complete capability profile for a user on a project"""
    user_id: str
    project_id: str
    capabilities: list[DimensionCapability] = field(default_factory=list)
    overall_score: float = 0.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "capabilities": [
                {
                    "dimension": c.dimension,
                    "level": c.level,
                    "evidence_ids": c.evidence_ids,
                    "interview_performance": {
                        "total_questions": c.interview_performance.total_questions,
                        "answered_correctly": c.interview_performance.answered_correctly,
                        "gaps": c.interview_performance.gaps,
                    }
                }
                for c in self.capabilities
            ],
            "overall_score": self.overall_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "updated_at": self.updated_at,
        }
