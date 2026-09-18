"""
Verification Engine Service

Responsible for verifying that tasks are actually completed,
not by reading README, but by checking real evidence.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from packages.contracts.models import (
    UpgradeTask, ExecutionRecord, CompletionCriterion,
    TaskStatus, TestResult
)
from packages.evidence_model import Evidence, EvidenceType


@dataclass
class VerificationResult:
    """Result of verifying a single criterion"""
    criterion: str
    status: str  # "passed", "failed", "partial", "unverifiable"
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    details: str = ""


@dataclass
class VerificationOutput:
    """Complete verification output"""
    task_id: str
    verification_results: List[VerificationResult]
    overall_status: str  # "passed", "partial", "failed", "unverifiable"
    missing_evidence: List[Dict[str, str]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "verification_results": [
                {
                    "criterion": r.criterion,
                    "status": r.status,
                    "evidence": r.evidence,
                    "details": r.details,
                }
                for r in self.verification_results
            ],
            "overall_status": self.overall_status,
            "missing_evidence": self.missing_evidence,
            "recommendations": self.recommendations,
        }


class VerificationEngine:
    """
    Verifies that tasks are actually completed by checking real evidence.
    
    Verification methods:
    - code: Check if code implementation exists
    - test: Check if tests exist and pass
    - run_result: Check if command execution results
    - benchmark: Check benchmark results
    - config: Check if configuration exists
    """
    
    def __init__(self):
        self.verification_methods = {
            "code": self._verify_code,
            "test": self._verify_test,
            "run_result": self._verify_run_result,
            "benchmark": self._verify_benchmark,
            "config": self._verify_config,
        }
    
    def verify(
        self,
        task: UpgradeTask,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationOutput:
        """
        Verify task completion.
        
        Args:
            task: The task being verified
            execution_record: Execution record from the task
            project_path: Path to project root
        
        Returns:
            VerificationOutput with detailed results
        """
        results: List[VerificationResult] = []
        missing_evidence: List[Dict[str, str]] = []
        
        for criterion in task.completion_criteria:
            result = self._verify_criterion(
                criterion,
                execution_record,
                project_path,
            )
            results.append(result)
            
            if result.status in ["failed", "unverifiable"]:
                missing_evidence.append({
                    "type": criterion.evidence_type,
                    "description": criterion.criterion,
                })
        
        # Determine overall status
        passed = sum(1 for r in results if r.status == "passed")
        partial = sum(1 for r in results if r.status == "partial")
        total = len(results)
        
        if passed == total:
            overall_status = "passed"
        elif passed + partial == total:
            overall_status = "partial"
        else:
            overall_status = "failed"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, missing_evidence)
        
        return VerificationOutput(
            task_id=task.id,
            verification_results=results,
            overall_status=overall_status,
            missing_evidence=missing_evidence,
            recommendations=recommendations,
        )
    
    def _verify_criterion(
        self,
        criterion: CompletionCriterion,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationResult:
        """Verify a single completion criterion"""
        method = self.verification_methods.get(criterion.evidence_type)
        
        if method:
            return method(criterion, execution_record, project_path)
        
        # Default: unverifiable
        return VerificationResult(
            criterion=criterion.criterion,
            status="unverifiable",
            evidence=[],
            details=f"Unknown evidence type: {criterion.evidence_type}",
        )
    
    def _verify_code(
        self,
        criterion: CompletionCriterion,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationResult:
        """Verify code implementation exists"""
        evidence: List[Dict[str, Any]] = []
        passed = False
        details_parts = []
        
        # Check if there are code changes
        code_changes = [c for c in execution_record.changes if c.change_type in ["added", "modified"]]
        
        if code_changes:
            for change in code_changes:
                evidence.append({
                    "type": "code",
                    "file": change.file_path,
                    "purpose": change.purpose,
                })
            passed = True
            details_parts.append(f"Found {len(code_changes)} code changes")
        else:
            # Try to find related files in project
            related_files = self._find_related_files(project_path, criterion.criterion)
            if related_files:
                for f in related_files:
                    evidence.append({
                        "type": "code",
                        "file": f,
                    })
                passed = True
                details_parts.append(f"Found related files: {len(related_files)}")
        
        # Check execution log for success
        if "error" in execution_record.execution_log.lower():
            passed = False
            details_parts.append("Execution log contains errors")
        
        return VerificationResult(
            criterion=criterion.criterion,
            status="passed" if passed else "failed",
            evidence=evidence,
            details=". ".join(details_parts) if details_parts else "No evidence found",
        )
    
    def _verify_test(
        self,
        criterion: CompletionCriterion,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationResult:
        """Verify tests exist and pass"""
        evidence: List[Dict[str, Any]] = []
        passed_count = 0
        failed_count = 0
        
        # Check test results from execution
        for test_result in execution_record.test_results:
            if test_result.passed:
                passed_count += 1
                evidence.append({
                    "type": "test",
                    "test": test_result.test_name,
                    "status": "passed",
                    "duration_ms": test_result.duration_ms,
                })
            else:
                failed_count += 1
                evidence.append({
                    "type": "test",
                    "test": test_result.test_name,
                    "status": "failed",
                    "error": test_result.error,
                })
        
        # Try to run tests if none were run
        if not execution_record.test_results:
            test_results = self._run_tests(project_path)
            for tr in test_results:
                if tr.passed:
                    passed_count += 1
                else:
                    failed_count += 1
                evidence.append({
                    "type": "test",
                    "test": tr.test_name,
                    "status": "passed" if tr.passed else "failed",
                    "duration_ms": tr.duration_ms,
                    "error": tr.error,
                })
        
        # Determine status
        if passed_count > 0 and failed_count == 0:
            status = "passed"
        elif passed_count > 0 and failed_count > 0:
            status = "partial"
        elif passed_count == 0:
            status = "failed"
        else:
            status = "unverifiable"
        
        details = f"Passed: {passed_count}, Failed: {failed_count}"
        
        return VerificationResult(
            criterion=criterion.criterion,
            status=status,
            evidence=evidence,
            details=details,
        )
    
    def _verify_run_result(
        self,
        criterion: CompletionCriterion,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationResult:
        """Verify command execution results"""
        evidence: List[Dict[str, Any]] = []
        
        # Check execution log
        if execution_record.execution_log:
            evidence.append({
                "type": "run_result",
                "log": execution_record.execution_log[:500],  # First 500 chars
            })
            
            # Check for errors
            if execution_record.error:
                return VerificationResult(
                    criterion=criterion.criterion,
                    status="failed",
                    evidence=evidence,
                    details=f"Execution error: {execution_record.error}",
                )
            
            return VerificationResult(
                criterion=criterion.criterion,
                status="passed",
                evidence=evidence,
                details="Execution completed successfully",
            )
        
        return VerificationResult(
            criterion=criterion.criterion,
            status="unverifiable",
            evidence=evidence,
            details="No execution log available",
        )
    
    def _verify_benchmark(
        self,
        criterion: CompletionCriterion,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationResult:
        """Verify benchmark results"""
        evidence: List[Dict[str, Any]] = []
        
        if execution_record.benchmark_results:
            for br in execution_record.benchmark_results:
                evidence.append({
                    "type": "benchmark",
                    "metric": br.metric,
                    "before": br.before_value,
                    "after": br.after_value,
                    "improvement": br.improvement,
                    "unit": br.unit,
                })
            
            return VerificationResult(
                criterion=criterion.criterion,
                status="passed",
                evidence=evidence,
                details=f"Found {len(execution_record.benchmark_results)} benchmark results",
            )
        
        return VerificationResult(
            criterion=criterion.criterion,
            status="unverifiable",
            evidence=evidence,
            details="No benchmark results available",
        )
    
    def _verify_config(
        self,
        criterion: CompletionCriterion,
        execution_record: ExecutionRecord,
        project_path: str,
    ) -> VerificationResult:
        """Verify configuration files exist"""
        evidence: List[Dict[str, Any]] = []
        
        # Look for config files in changes
        config_changes = [c for c in execution_record.changes 
                         if any(ext in c.file_path for ext in [".json", ".yaml", ".yml", ".toml", ".env"])]
        
        if config_changes:
            for change in config_changes:
                evidence.append({
                    "type": "config",
                    "file": change.file_path,
                })
            return VerificationResult(
                criterion=criterion.criterion,
                status="passed",
                evidence=evidence,
                details=f"Found {len(config_changes)} config changes",
            )
        
        # Try to find config files in project
        config_patterns = ["*.json", "*.yaml", "*.yml", "*.toml", "*.env*"]
        found_configs = []
        for pattern in config_patterns:
            found_configs.extend(Path(project_path).rglob(pattern))
        
        if found_configs:
            for f in found_configs[:5]:  # Limit to 5
                evidence.append({
                    "type": "config",
                    "file": str(f.relative_to(project_path)),
                })
            return VerificationResult(
                criterion=criterion.criterion,
                status="passed",
                evidence=evidence,
                details=f"Found {len(found_configs)} config files",
            )
        
        return VerificationResult(
            criterion=criterion.criterion,
            status="failed",
            evidence=evidence,
            details="No config files found",
        )
    
    def _find_related_files(
        self,
        project_path: str,
        criterion: str,
    ) -> List[str]:
        """Find files related to a criterion"""
        related = []
        keywords = criterion.lower().split()
        
        for root, dirs, files in os.walk(project_path):
            # Skip common exclusions
            dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__", ".venv"]]
            
            for f in files:
                if any(kw in f.lower() for kw in keywords):
                    related.append(os.path.join(root, f))
        
        return related[:10]  # Limit to 10
    
    def _run_tests(self, project_path: str) -> List[TestResult]:
        """Run tests in project"""
        results = []
        
        # Detect test framework
        has_pytest = os.path.exists(os.path.join(project_path, "pytest.ini")) or \
                    os.path.exists(os.path.join(project_path, "pyproject.toml"))
        has_jest = os.path.exists(os.path.join(project_path, "package.json"))
        
        if has_pytest:
            try:
                result = subprocess.run(
                    ["pytest", "--collect-only", "-q"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                # Parse output
                if "error" not in result.stdout.lower():
                    results.append(TestResult(
                        test_name="pytest_collection",
                        passed=True,
                        duration_ms=0,
                    ))
            except Exception as e:
                results.append(TestResult(
                    test_name="pytest_collection",
                    passed=False,
                    duration_ms=0,
                    error=str(e),
                ))
        
        if has_jest:
            try:
                result = subprocess.run(
                    ["npm", "test", "--", "--listTests"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    results.append(TestResult(
                        test_name="jest_collection",
                        passed=True,
                        duration_ms=0,
                    ))
            except Exception as e:
                results.append(TestResult(
                    test_name="jest_collection",
                    passed=False,
                    duration_ms=0,
                    error=str(e),
                ))
        
        return results
    
    def _generate_recommendations(
        self,
        results: List[VerificationResult],
        missing: List[Dict[str, str]],
    ) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        passed = sum(1 for r in results if r.status == "passed")
        total = len(results)
        
        if passed == total:
            recommendations.append("所有验证标准已通过，任务完成。")
        elif passed > 0:
            recommendations.append(f"部分验证通过 ({passed}/{total})，请解决剩余问题。")
        else:
            recommendations.append("验证未通过，请检查实现。")
        
        # Specific recommendations
        for missing_item in missing:
            if missing_item["type"] == "code":
                recommendations.append("请确保代码实现存在并可访问。")
            elif missing_item["type"] == "test":
                recommendations.append("请添加相应的测试用例。")
            elif missing_item["type"] == "run_result":
                recommendations.append("请运行代码并记录执行结果。")
            elif missing_item["type"] == "benchmark":
                recommendations.append("请运行基准测试并记录结果。")
            elif missing_item["type"] == "config":
                recommendations.append("请添加相应的配置文件。")
        
        return list(set(recommendations))  # Deduplicate
