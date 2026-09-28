"""Read-only Project Lab assessment service.

This integration is intentionally assessment-only. It never edits learner code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from packages.contracts.models import (
    CompletionCriterion,
    ExecutionRecord,
    LearningContent,
    TaskStatus,
    UpgradeTask,
)
from services.verification_engine import VerificationEngine


@dataclass(frozen=True)
class ProjectLabCriterion:
    criterion: str
    evidence_type: str
    verification_method: str = ""


class ProjectLabAssessmentService:
    """Run Project OS verification against a learner repository without mutating it."""

    def __init__(self, verifier: VerificationEngine | None = None):
        self.verifier = verifier or VerificationEngine()

    def assess(
        self,
        *,
        project_id: str,
        project_path: str,
        skill_ids: list[str] | None = None,
        criteria: list[ProjectLabCriterion] | None = None,
    ) -> dict[str, Any]:
        root = Path(project_path)
        if not root.exists() or not root.is_dir():
            raise ValueError("Project workspace not found")

        requested = criteria or [
            ProjectLabCriterion(
                criterion="Project tests are discoverable and pass collection",
                evidence_type="test",
                verification_method="project_test_discovery",
            )
        ]

        completion_criteria = [
            CompletionCriterion(
                criterion=item.criterion,
                verification_method=item.verification_method,
                evidence_type=item.evidence_type,
            )
            for item in requested
        ]

        assessment_id = f"project-lab-{uuid4()}"
        task = UpgradeTask(
            id=f"{assessment_id}-task",
            project_id=project_id,
            gap_id="project-lab-readonly",
            title="Read-only Project Lab assessment",
            description="Assess the submitted repository without modifying learner code.",
            learning_content=LearningContent(),
            completion_criteria=completion_criteria,
        )

        execution = ExecutionRecord(
            id=f"{assessment_id}-execution",
            task_id=task.id,
            project_id=project_id,
            changes=[],
            execution_log="Project Lab read-only assessment; no code changes were executed.",
            test_results=[],
            status=TaskStatus.COMPLETED,
            harness_metadata={
                "mode": "project-lab-readonly",
                "read_only": True,
                "skill_ids": list(skill_ids or []),
            },
        )

        verification = self.verifier.verify(task, execution, str(root))
        statuses = [item.status for item in verification.verification_results]

        passed = sum(1 for status in statuses if status == "passed")
        partial = sum(1 for status in statuses if status == "partial")
        failed = sum(1 for status in statuses if status in {"failed", "unverifiable"})
        total = len(statuses)

        return {
            "assessment_id": assessment_id,
            "project_id": project_id,
            "skill_ids": list(skill_ids or []),
            "read_only": True,
            "repository_mutated": False,
            "verification": verification.to_dict(),
            "summary": {
                "total": total,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "pass_rate": (passed / total) if total else 0.0,
            },
        }
