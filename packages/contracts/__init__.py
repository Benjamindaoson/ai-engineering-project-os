"""
Contracts Package

Shared data models and type definitions for the AI Engineering Project OS.
"""

from packages.contracts.models import (
    ProjectType, GapPriority, TaskStatus,
    GapRisk, EffortEstimate, ImplementationStatusType,
    ProjectFacts, Gap, LearningContent, CompletionCriterion,
    UpgradeTask, CodeChange, TestResult, BenchmarkResult,
    ExecutionRecord, ArchitectureDecision, InterviewQuestion,
    InterviewSession, CapabilityProfile, InterviewPerformance,
    DimensionCapability,
)

# Re-export MaturityLevel from maturity_model
from packages.maturity_model import MaturityLevel

__all__ = [
    "ProjectType",
    "GapPriority",
    "TaskStatus",
    "MaturityLevel",
    "GapRisk",
    "EffortEstimate",
    "ImplementationStatusType",
    "ProjectFacts",
    "Gap",
    "LearningContent",
    "CompletionCriterion",
    "UpgradeTask",
    "CodeChange",
    "TestResult",
    "BenchmarkResult",
    "ExecutionRecord",
    "ArchitectureDecision",
    "InterviewQuestion",
    "InterviewSession",
    "CapabilityProfile",
    "InterviewPerformance",
    "DimensionCapability",
]
