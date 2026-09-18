"""
Project Auditor Service

Responsible for reading and understanding user projects, building fact lists,
assessing maturity, and identifying gaps.
"""

import os
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from packages.contracts.models import (
    ProjectFacts, Gap, GapPriority, GapRisk, EffortEstimate,
    ImplementationStatusType
)
from packages.maturity-model import MaturityEvaluator, MaturityLevel
from packages.evidence-model import EvidenceBuilder, EvidenceType
from packages.project-intelligence import build_project_facts, analyze_directory


@dataclass
class RawObservation:
    """Raw observation during project analysis"""
    category: str
    finding: str
    evidence_path: Optional[str] = None
    evidence_lines: Optional[tuple] = None
    severity: str = "info"  # "info", "warning", "critical"


class ProjectAuditor:
    """
    Audits user projects and produces:
    - ProjectFacts: Extracted facts about the project
    - MaturityAssessment: Current maturity level
    - Gaps: Identified capability gaps
    """
    
    def __init__(self):
        self.evaluator = MaturityEvaluator()
        self.observations: List[RawObservation] = []
    
    def audit(
        self,
        project_path: str,
        project_id: str,
        github_url: Optional[str] = None,
        user_goals: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a complete project audit.
        
        Args:
            project_path: Path to project on disk
            project_id: Unique identifier for this project
            github_url: Optional GitHub URL
            user_goals: Optional user-specified goals
        
        Returns:
            Dictionary with:
            - project_facts: ProjectFacts object
            - maturity_assessment: Assessment result
            - gaps: List of identified gaps
            - raw_observations: All observations made during audit
        """
        self.observations = []
        
        # Step 1: Extract project facts
        project_name = Path(project_path).name
        facts = build_project_facts(project_path, project_name)
        
        # Step 2: Analyze implementation status
        facts = self._analyze_implementation_status(project_path, facts)
        
        # Step 3: Add observations
        self._generate_observations(facts, project_path)
        
        # Step 4: Assess maturity
        maturity = self.evaluator.evaluate(facts.to_dict())
        
        # Step 5: Identify gaps
        gaps = self._identify_gaps(facts, maturity, project_id)
        
        return {
            "project_facts": facts.to_dict(),
            "maturity_assessment": maturity.to_dict(),
            "gaps": [g.to_dict() for g in gaps],
            "raw_observations": [
                {
                    "category": o.category,
                    "finding": o.finding,
                    "evidence_path": o.evidence_path,
                    "evidence_lines": o.evidence_lines,
                    "severity": o.severity,
                }
                for o in self.observations
            ],
        }
    
    def _analyze_implementation_status(
        self,
        project_path: str,
        facts: ProjectFacts
    ) -> ProjectFacts:
        """Analyze implementation status of various project components"""
        analysis = analyze_directory(project_path)
        
        # Check for key files and patterns
        has_api = any("api" in f.lower() or "route" in f.lower() 
                      for f in analysis.config_files)
        has_auth = any("auth" in f.lower() or "login" in f.lower() 
                       for f in analysis.files)
        has_tests = len(analysis.test_files) > 0
        has_docker = analysis.deployment_stats.get("docker", False)
        has_ci = any("github" in d.lower() for d in analysis.deployment)
        
        # Analyze main code content
        code_content = ""
        for f in analysis.files[:20]:  # Sample first 20 files
            try:
                with open(os.path.join(project_path, f.relative_path), "r", encoding="utf-8", errors="ignore") as file:
                    code_content += file.read()[:1000]
            except:
                pass
        
        # Core features status
        facts.implementation_status["core_features"] = [
            {
                "feature": "Core functionality",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if facts.code_lines > 100 else ImplementationStatusType.PARTIALLY_IMPLEMENTED.value,
                "evidence": [],
            }
        ]
        
        # Data layer status
        facts.implementation_status["data"] = [
            {
                "feature": "Data persistence",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if facts.database else ImplementationStatusType.MISSING.value,
                "evidence": facts.database,
            },
            {
                "feature": "Data validation",
                "status": ImplementationStatusType.PARTIALLY_IMPLEMENTED.value if any(p in code_content for p in ["validate", "schema", "pydantic"]) else ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        # API layer status
        facts.implementation_status["api"] = [
            {
                "feature": "API endpoints",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if has_api else ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
            {
                "feature": "Error handling",
                "status": ImplementationStatusType.PARTIALLY_IMPLEMENTED.value if "except" in code_content or "try" in code_content else ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        # Auth status
        facts.implementation_status["auth"] = [
            {
                "feature": "Authentication",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if has_auth else ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
            {
                "feature": "Authorization",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        # Error handling
        facts.implementation_status["error_handling"] = [
            {
                "feature": "Exception handling",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if "except" in code_content else ImplementationStatusType.PARTIALLY_IMPLEMENTED.value,
                "evidence": [],
            },
            {
                "feature": "Retry mechanism",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
            {
                "feature": "Fallback",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        # Testing
        facts.implementation_status["testing"] = [
            {
                "feature": "Unit tests",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if facts.test_files > 0 else ImplementationStatusType.MISSING.value,
                "evidence": analysis.test_files,
            },
            {
                "feature": "Integration tests",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        # Deployment
        facts.implementation_status["deployment"] = [
            {
                "feature": "Containerization",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if has_docker else ImplementationStatusType.MISSING.value,
                "evidence": ["Dockerfile", "docker-compose.yml"] if has_docker else [],
            },
            {
                "feature": "CI/CD",
                "status": ImplementationStatusType.FULLY_IMPLEMENTED.value if has_ci else ImplementationStatusType.MISSING.value,
                "evidence": [".github/workflows"] if has_ci else [],
            },
        ]
        
        # Monitoring (assumed missing for most projects)
        facts.implementation_status["monitoring"] = [
            {
                "feature": "Logging",
                "status": ImplementationStatusType.PARTIALLY_IMPLEMENTED.value if "log" in code_content.lower() else ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
            {
                "feature": "Metrics",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
            {
                "feature": "Tracing",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        # Evaluation (assumed missing unless explicitly found)
        facts.implementation_status["evaluation"] = [
            {
                "feature": "Benchmarks",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
            {
                "feature": "A/B testing",
                "status": ImplementationStatusType.MISSING.value,
                "evidence": [],
            },
        ]
        
        return facts
    
    def _generate_observations(self, facts: ProjectFacts, project_path: str):
        """Generate observations from project facts"""
        # Code quality observations
        if facts.total_files == 0:
            self.observations.append(RawObservation(
                category="structure",
                finding="No source files found",
                severity="critical",
            ))
        elif facts.total_files < 5:
            self.observations.append(RawObservation(
                category="structure",
                finding="Very few source files, may be a stub project",
                severity="warning",
            ))
        
        # Testing observations
        if facts.test_files == 0:
            self.observations.append(RawObservation(
                category="testing",
                finding="No test files found",
                severity="warning",
            ))
        elif facts.test_files < facts.total_files * 0.1:
            self.observations.append(RawObservation(
                category="testing",
                finding=f"Low test coverage ({facts.test_files} tests for {facts.total_files} files)",
                severity="warning",
            ))
        
        # Documentation observations
        if not facts.has_readme:
            self.observations.append(RawObservation(
                category="documentation",
                finding="No README.md found",
                severity="warning",
            ))
        
        # Tech stack observations
        if not facts.frameworks:
            self.observations.append(RawObservation(
                category="tech_stack",
                finding="No frameworks detected",
                severity="info",
            ))
        
        # Deployment observations
        if not facts.deployment:
            self.observations.append(RawObservation(
                category="deployment",
                finding="No deployment configuration found",
                severity="warning",
            ))
        
        # Database observations
        if not facts.database:
            self.observations.append(RawObservation(
                category="data",
                finding="No database detected",
                severity="info",
            ))
    
    def _identify_gaps(
        self,
        facts: ProjectFacts,
        maturity: Any,
        project_id: str
    ) -> List[Gap]:
        """Identify gaps based on maturity assessment"""
        gaps = []
        
        # Check each blocker and create gaps
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
        
        # Add specific gaps based on implementation status
        for category, items in facts.implementation_status.items():
            for item in items:
                status = item.get("status", "")
                if status in [ImplementationStatusType.MISSING.value, 
                              ImplementationStatusType.PARTIALLY_IMPLEMENTED.value]:
                    # Check if we already have this gap
                    existing = any(
                        g.description == f"Missing: {item['feature']}" 
                        for g in gaps
                    )
                    if not existing:
                        gap = Gap(
                            id=str(uuid.uuid4()),
                            project_id=project_id,
                            dimension=category,
                            description=f"Missing: {item['feature']}",
                            current_state="Not implemented" if status == ImplementationStatusType.MISSING.value else "Partially implemented",
                            target_state=item["feature"],
                            priority=self._prioritize_feature(category, item["feature"]),
                        )
                        gaps.append(gap)
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda x: priority_order.get(x.priority.value if hasattr(x.priority, 'value') else str(x.priority), 3))
        
        return gaps[:20]  # Return top 20 gaps
    
    def _determine_priority(self, blocker: Dict[str, Any]) -> GapPriority:
        """Determine gap priority based on blocker"""
        category = blocker.get("category", "")
        level = blocker.get("level_required", "")
        
        # Core features are always high priority
        if category in ["core_features"]:
            return GapPriority.HIGH
        
        # Production requirements are critical
        if level == "production":
            return GapPriority.CRITICAL
        
        # Pre-production requirements are high
        if level == "pre_production":
            return GapPriority.HIGH
        
        return GapPriority.MEDIUM
    
    def _estimate_effort(self, blocker: Dict[str, Any]) -> EffortEstimate:
        """Estimate effort to fix a gap"""
        feature = blocker.get("criterion_name", "").lower()
        
        # Simple features
        if any(word in feature for word in ["logging", "comment", "docs"]):
            return EffortEstimate.SMALL
        
        # Medium complexity
        if any(word in feature for word in ["test", "error handling", "validation"]):
            return EffortEstimate.MEDIUM
        
        # Complex features
        if any(word in feature for word in ["monitoring", "deployment", "ci/cd", "authentication"]):
            return EffortEstimate.LARGE
        
        return EffortEstimate.MEDIUM
    
    def _determine_risk(self, blocker: Dict[str, Any]) -> GapRisk:
        """Determine risk of the gap"""
        category = blocker.get("category", "")
        
        if category in ["security", "error_handling", "reliability"]:
            return GapRisk.HIGH
        if category in ["monitoring", "deployment"]:
            return GapRisk.MEDIUM
        
        return GapRisk.LOW
    
    def _prioritize_feature(self, category: str, feature: str) -> GapPriority:
        """Prioritize a feature based on category and type"""
        feature_lower = feature.lower()
        
        # Critical features
        if any(word in feature_lower for word in ["error handling", "exception", "validation"]):
            return GapPriority.HIGH
        if any(word in feature_lower for word in ["auth", "security", "test"]):
            return GapPriority.HIGH
        
        # Medium priority
        if any(word in feature_lower for word in ["monitoring", "logging", "metrics"]):
            return GapPriority.MEDIUM
        
        # Lower priority
        if any(word in feature_lower for word in ["docs", "comment"]):
            return GapPriority.LOW
        
        return GapPriority.MEDIUM
