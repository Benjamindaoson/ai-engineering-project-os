"""
Project Auditor Service

Responsible for reading and understanding user projects, building fact lists,
assessing maturity, and identifying gaps.
Now with real evidence-based assessment.
"""

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.contracts.models import (
    EffortEstimate,
    Gap,
    GapPriority,
    GapRisk,
    ImplementationStatusType,
)
from packages.evidence_model import EvidenceBuilder, EvidenceType
from packages.maturity_model import MaturityEvaluator, MaturityLevel
from packages.project_intelligence import (
    Evidence,
    analyze_directory,
    build_project_facts,
)


@dataclass
class RawObservation:
    """Raw observation during project analysis"""
    category: str
    finding: str
    evidence_path: str | None = None
    evidence_lines: tuple | None = None
    severity: str = "info"


class ProjectAuditor:
    """
    Audits user projects and produces:
    - ProjectFacts: Extracted facts about the project
    - MaturityAssessment: Current maturity level
    - Gaps: Identified capability gaps
    """
    
    def __init__(self):
        self.evaluator = MaturityEvaluator()
    
    def audit(
        self,
        project_path: str,
        project_id: str,
        github_url: str | None = None,
        user_goals: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Perform a complete project audit with evidence.
        
        Args:
            project_path: Path to project on disk
            project_id: Unique identifier for this project
            github_url: Optional GitHub URL
            user_goals: Optional user-specified goals
        
        Returns:
            Dictionary with:
            - project_facts: Extracted facts with evidence
            - maturity_assessment: Assessment result
            - gaps: List of identified gaps
            - raw_observations: All observations made during audit
        """
        # Step 1: Extract project facts with evidence
        project_name = Path(project_path).name
        facts = build_project_facts(project_path, project_name)
        
        # Step 2: Assess maturity based on real facts
        maturity = self.evaluator.evaluate(facts)
        
        # Step 3: Generate observations
        observations = facts.get("raw_observations", [])
        
        # Step 4: Identify gaps based on real analysis
        gaps = self._identify_gaps(facts, maturity, project_id)
        
        return {
            "project_facts": facts,
            "maturity_assessment": maturity.to_dict(),
            "gaps": [g.to_dict() for g in gaps],
            "raw_observations": observations,
        }
    
    def _identify_gaps(
        self,
        facts: dict[str, Any],
        maturity: Any,
        project_id: str
    ) -> list[Gap]:
        """Identify gaps based on maturity assessment and real facts"""
        gaps = []
        
        # Check each maturity blocker
        for blocker in maturity.blockers:
            gap = Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension=blocker.get("category", "unknown"),
                description=f"Missing: {blocker.get('criterion_name', 'Unknown criterion')}",
                current_state="Not implemented",
                target_state=blocker.get("criterion_name", "Required"),
                priority=self._determine_priority(blocker),
                effort_estimate=self._estimate_effort(blocker),
                risk=self._determine_risk(blocker),
                related_criteria=[blocker.get("criterion_id", "")],
            )
            gaps.append(gap)
        
        # Add specific gaps based on real analysis
        # Testing gaps
        if not facts.get("has_pytest"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="testing",
                description="Missing: pytest or test framework",
                current_state="No test framework detected",
                target_state="pytest configured and tests written",
                priority=GapPriority.HIGH,
                effort_estimate=EffortEstimate.LARGE,
                risk=GapRisk.MEDIUM,
                related_criteria=["mvp_tests"],
            ))
        
        if facts.get("test_files", 0) == 0 or facts.get("test_lines", 0) < facts.get("code_lines", 1) * 0.1:
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="testing",
                description="Low test coverage",
                current_state="Test coverage appears low",
                target_state="At least 20% test coverage",
                priority=GapPriority.MEDIUM,
                effort_estimate=EffortEstimate.MEDIUM,
                risk=GapRisk.LOW,
                related_criteria=["preprod_regression"],
            ))
        
        # Deployment gaps
        if not facts.get("has_dockerfile"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="deployment",
                description="Missing: Dockerfile",
                current_state="No containerization",
                target_state="Dockerfile exists and builds",
                priority=GapPriority.MEDIUM,
                effort_estimate=EffortEstimate.SMALL,
                risk=GapRisk.MEDIUM,
                related_criteria=["preprod_auto_tests"],
            ))
        
        if not facts.get("has_ci"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="deployment",
                description="Missing: CI/CD pipeline",
                current_state="No CI/CD detected",
                target_state="GitHub Actions or similar CI configured",
                priority=GapPriority.HIGH,
                effort_estimate=EffortEstimate.MEDIUM,
                risk=GapRisk.MEDIUM,
                related_criteria=["preprod_auto_tests"],
            ))
        
        # Auth gaps
        if not facts.get("has_auth"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="auth",
                description="Missing: Authentication",
                current_state="No auth code detected",
                target_state="Authentication implemented",
                priority=GapPriority.CRITICAL,
                effort_estimate=EffortEstimate.LARGE,
                risk=GapRisk.HIGH,
                related_criteria=["preprod_permissions"],
            ))
        
        # Error handling gaps
        if not facts.get("has_error_handling"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="error_handling",
                description="Missing: Error handling",
                current_state="No error handling detected",
                target_state="Exception handling with logging",
                priority=GapPriority.HIGH,
                effort_estimate=EffortEstimate.MEDIUM,
                risk=GapRisk.MEDIUM,
                related_criteria=["mvp_error_handling"],
            ))
        
        # Retry gaps
        if not facts.get("has_retry"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="error_handling",
                description="Missing: Retry mechanism",
                current_state="No retry logic",
                target_state="Retry with backoff for transient failures",
                priority=GapPriority.MEDIUM,
                effort_estimate=EffortEstimate.MEDIUM,
                risk=GapRisk.MEDIUM,
                related_criteria=["preprod_retry"],
            ))
        
        # Observability gaps
        obs_stats = facts.get("observability", {})
        if not obs_stats.get("logging"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="monitoring",
                description="Missing: Logging",
                current_state="No logging detected",
                target_state="Structured logging implemented",
                priority=GapPriority.HIGH,
                effort_estimate=EffortEstimate.SMALL,
                risk=GapRisk.LOW,
                related_criteria=["preprod_logging"],
            ))
        
        if not obs_stats.get("metrics"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="monitoring",
                description="Missing: Metrics",
                current_state="No metrics collection",
                target_state="Key metrics exposed",
                priority=GapPriority.MEDIUM,
                effort_estimate=EffortEstimate.MEDIUM,
                risk=GapRisk.LOW,
                related_criteria=["preprod_monitoring"],
            ))
        
        # Documentation gaps
        if not facts.get("has_readme"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="documentation",
                description="Missing: README",
                current_state="No README.md",
                target_state="README with setup instructions",
                priority=GapPriority.MEDIUM,
                effort_estimate=EffortEstimate.SMALL,
                risk=GapRisk.LOW,
                related_criteria=["mvp_deploy"],
            ))
        
        # Configuration gaps
        if not facts.get("has_env_example"):
            gaps.append(Gap(
                id=str(uuid.uuid4()),
                project_id=project_id,
                dimension="deployment",
                description="Missing: Environment example",
                current_state="No .env.example",
                target_state=".env.example with required variables",
                priority=GapPriority.MEDIUM,
                effort_estimate=EffortEstimate.SMALL,
                risk=GapRisk.LOW,
                related_criteria=["preprod_auto_tests"],
            ))
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda x: priority_order.get(x.priority.value if hasattr(x.priority, 'value') else str(x.priority), 3))
        
        return gaps[:20]
    
    def _determine_priority(self, blocker: dict[str, Any]) -> GapPriority:
        """Determine gap priority based on blocker"""
        category = blocker.get("category", "")
        level = blocker.get("level_required", "")
        
        if category in ["core_features", "auth", "data"]:
            return GapPriority.CRITICAL
        
        if level == "production":
            return GapPriority.CRITICAL
        
        if level == "pre_production":
            return GapPriority.HIGH
        
        return GapPriority.MEDIUM
    
    def _estimate_effort(self, blocker: dict[str, Any]) -> EffortEstimate:
        """Estimate effort to fix a gap"""
        feature = blocker.get("criterion_name", "").lower()
        
        if any(word in feature for word in ["logging", "comment", "docs", "env"]):
            return EffortEstimate.SMALL
        
        if any(word in feature for word in ["test", "error handling", "validation", "ci"]):
            return EffortEstimate.MEDIUM
        
        if any(word in feature for word in ["monitoring", "deployment", "ci/cd", "authentication", "security"]):
            return EffortEstimate.LARGE
        
        return EffortEstimate.MEDIUM
    
    def _determine_risk(self, blocker: dict[str, Any]) -> GapRisk:
        """Determine risk of the gap"""
        category = blocker.get("category", "")
        
        if category in ["security", "error_handling", "reliability", "auth"]:
            return GapRisk.HIGH
        if category in ["monitoring", "deployment"]:
            return GapRisk.MEDIUM
        
        return GapRisk.LOW
