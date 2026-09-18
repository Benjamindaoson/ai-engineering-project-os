"""
Contracts Package

Shared data models and type definitions for the AI Engineering Project OS.
"""

from packages.contracts.models import (
    ArchitectureDecision,
    BenchmarkResult,
    CapabilityProfile,
    CodeChange,
    CompletionCriterion,
    DimensionCapability,
    EffortEstimate,
    ExecutionRecord,
    Gap,
    GapPriority,
    GapRisk,
    ImplementationStatusType,
    InterviewPerformance,
    InterviewQuestion,
    InterviewSession,
    LearningContent,
    ProjectFacts,
    ProjectType,
    TaskStatus,
    TestResult,
    UpgradeTask,
)

# Re-export MaturityLevel from maturity_model
from packages.maturity_model import MaturityLevel

__all__ = [
    "ArchitectureDecision",
    "BenchmarkResult",
    "CapabilityProfile",
    "CodeChange",
    "CompletionCriterion",
    "DimensionCapability",
    "EffortEstimate",
    "ExecutionRecord",
    "Gap",
    "GapPriority",
    "GapRisk",
    "ImplementationStatusType",
    "InterviewPerformance",
    "InterviewQuestion",
    "InterviewSession",
    "LearningContent",
    "MaturityLevel",
    "ProjectFacts",
    "ProjectType",
    "TaskStatus",
    "TestResult",
    "UpgradeTask",
]
