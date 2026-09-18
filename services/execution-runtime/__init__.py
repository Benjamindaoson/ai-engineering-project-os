"""
Execution Runtime Service

Responsible for safely executing code modifications and running tests.
"""

import os
import json
import uuid
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from packages.contracts.models import (
    UpgradeTask, ExecutionRecord, CodeChange, TestResult,
    BenchmarkResult, TaskStatus, LearningContent
)


@dataclass
class ExecutionConfig:
    """Configuration for execution"""
    save_baseline: bool = True
    run_tests: bool = True
    timeout_seconds: int = 300
    max_retries: int = 1


class ExecutionRuntime:
    """
    Executes upgrade tasks safely with:
    - Baseline saving before modifications
    - All changes tracked
    - Test execution and result recording
    - Benchmark comparison
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.baseline_path = ".upgrade_baseline"
    
    def execute(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> ExecutionRecord:
        """
        Execute an upgrade task.
        
        Args:
            task: The task to execute
            project_path: Path to project root
        
        Returns:
            ExecutionRecord with all execution details
        """
        record = ExecutionRecord(
            id=str(uuid.uuid4()),
            task_id=task.id,
            project_id=task.project_id,
            status=TaskStatus.IN_PROGRESS,
        )
        
        try:
            # Step 1: Save baseline
            if self.config.save_baseline:
                self._save_baseline(project_path, record)
            
            # Step 2: Prepare workspace
            workspace = self._prepare_workspace(project_path)
            
            # Step 3: Execute based on task type
            # For Phase 1, we'll simulate execution since we don't have actual LLM integration
            result = self._simulate_execution(task, project_path, workspace)
            
            # Step 4: Record changes
            record.changes = result.get("changes", [])
            
            # Step 5: Run tests if configured
            if self.config.run_tests:
                record.test_results = self._run_project_tests(project_path)
            
            # Step 6: Generate benchmarks
            record.benchmark_results = self._generate_benchmarks(project_path, record.changes)
            
            # Step 7: Finalize
            record.status = TaskStatus.COMPLETED
            record.execution_log = result.get("log", "")
            record.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            record.status = TaskStatus.FAILED
            record.error = str(e)
            record.execution_log = f"Execution failed: {e}"
            record.completed_at = datetime.now().isoformat()
        
        return record
    
    def _save_baseline(
        self,
        project_path: str,
        record: ExecutionRecord,
    ) -> str:
        """Save project baseline before modifications"""
        baseline_id = f"baseline_{record.id}"
        baseline_dir = Path(project_path) / self.baseline_path / baseline_id
        
        try:
            # Create baseline directory
            baseline_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy key files (not all to save space)
            key_patterns = ["*.py", "*.ts", "*.js", "*.json", "*.yaml", "*.yml"]
            
            for pattern in key_patterns:
                for src in Path(project_path).rglob(pattern):
                    # Skip virtual environments and caches
                    if any(skip in str(src) for skip in ["venv", ".venv", "node_modules", "__pycache__"]):
                        continue
                    
                    rel_path = src.relative_to(project_path)
                    dst = baseline_dir / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            
            record.execution_log += f"Baseline saved to {baseline_dir}\n"
            return str(baseline_dir)
            
        except Exception as e:
            record.execution_log += f"Warning: Failed to save baseline: {e}\n"
            return ""
    
    def _prepare_workspace(self, project_path: str) -> str:
        """Prepare workspace for execution"""
        workspace = Path(project_path) / ".upgrade_workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        return str(workspace)
    
    def _simulate_execution(
        self,
        task: UpgradeTask,
        project_path: str,
        workspace: str,
    ) -> Dict[str, Any]:
        """
        Simulate task execution.
        
        In Phase 1, this generates example code changes.
        In later phases, this would integrate with actual code generation.
        """
        changes = []
        log_parts = []
        
        # Get learning content
        learning = task.learning_content
        if isinstance(learning, dict):
            learning = LearningContent(**learning)
        
        log_parts.append(f"Starting execution for task: {task.title}")
        log_parts.append(f"Target: {task.description}")
        
        # Analyze task and generate appropriate changes
        dimension = self._extract_dimension(task.title)
        
        if dimension == "testing":
            changes.extend(self._generate_test_changes(task, project_path))
            log_parts.append("Generated test files")
        
        elif dimension == "error_handling":
            changes.extend(self._generate_error_handling_changes(task, project_path))
            log_parts.append("Added error handling")
        
        elif dimension == "monitoring":
            changes.extend(self._generate_logging_changes(task, project_path))
            log_parts.append("Added logging")
        
        elif dimension == "deployment":
            changes.extend(self._generate_dockerfile(task, project_path))
            log_parts.append("Generated Dockerfile")
        
        else:
            # Generic changes
            changes.append(CodeChange(
                file_path="upgrade_note.md",
                change_type="added",
                diff=f"# Upgrade: {task.title}\n\n{task.description}",
                purpose="Document the upgrade",
            ))
            log_parts.append("Generated documentation")
        
        return {
            "changes": changes,
            "log": "\n".join(log_parts),
        }
    
    def _extract_dimension(self, title: str) -> str:
        """Extract dimension from task title"""
        title_lower = title.lower()
        
        if "测试" in title or "test" in title_lower:
            return "testing"
        elif "错误" in title or "异常" in title or "error" in title_lower:
            return "error_handling"
        elif "监控" in title or "日志" in title or "monitor" in title_lower or "log" in title_lower:
            return "monitoring"
        elif "部署" in title or "docker" in title_lower:
            return "deployment"
        
        return "general"
    
    def _generate_test_changes(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> List[CodeChange]:
        """Generate test file changes"""
        changes = []
        
        # Check if pytest is available
        has_pytest = os.path.exists(os.path.join(project_path, "pytest.ini")) or \
                    os.path.exists(os.path.join(project_path, "pyproject.toml"))
        
        if has_pytest:
            changes.append(CodeChange(
                file_path="tests/test_upgrade.py",
                change_type="added",
                diff="""import pytest

class TestUpgrade:
    def test_placeholder(self):
        '''Test placeholder for upgrade task'''
        assert True
""",
                purpose="Add test for upgrade task",
            ))
        else:
            changes.append(CodeChange(
                file_path="test/test_upgrade.js",
                change_type="added",
                diff="""describe('Upgrade Task', () => {
    it('should pass placeholder test', () => {
        expect(true).toBe(true);
    });
});
""",
                purpose="Add test for upgrade task",
            ))
        
        return changes
    
    def _generate_error_handling_changes(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> List[CodeChange]:
        """Generate error handling changes"""
        changes = []
        
        # Check project language
        has_python = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_python:
            changes.append(CodeChange(
                file_path="utils/exceptions.py",
                change_type="added",
                diff="""'''Custom exceptions for the project'''

class ProjectError(Exception):
    '''Base exception for project errors'''
    pass

class ConfigurationError(ProjectError):
    '''Raised when configuration is invalid'''
    pass

class DataError(ProjectError):
    '''Raised when data is invalid or unavailable'''
    pass
""",
                purpose="Add custom exception classes",
            ))
        else:
            changes.append(CodeChange(
                file_path="src/errors.js",
                change_type="added",
                diff="""// Custom error classes
class ProjectError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ProjectError';
    }
}

class ConfigurationError extends ProjectError {
    constructor(message) {
        super(message);
        this.name = 'ConfigurationError';
    }
}
""",
                purpose="Add custom error classes",
            ))
        
        return changes
    
    def _generate_logging_changes(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> List[CodeChange]:
        """Generate logging changes"""
        changes = []
        
        has_python = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_python:
            changes.append(CodeChange(
                file_path="utils/logger.py",
                change_type="added",
                diff="""'''Logging configuration'''
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    '''Get a configured logger'''
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
""",
                purpose="Add logging configuration",
            ))
        else:
            changes.append(CodeChange(
                file_path="src/logger.js",
                change_type="added",
                diff="""// Simple logger implementation
const LOG_LEVELS = { ERROR: 0, WARN: 1, INFO: 2, DEBUG: 3 };

function createLogger(name, level = 'INFO') {
    return {
        info: (msg) => console.log(`[INFO] ${name}: ${msg}`),
        warn: (msg) => console.warn(`[WARN] ${name}: ${msg}`),
        error: (msg) => console.error(`[ERROR] ${name}: ${msg}`),
        debug: (msg) => console.debug(`[DEBUG] ${name}: ${msg}`),
    };
}

module.exports = { createLogger };
""",
                purpose="Add logging utility",
            ))
        
        return changes
    
    def _generate_dockerfile(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> List[CodeChange]:
        """Generate Dockerfile"""
        changes = []
        
        has_python = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_python:
            changes.append(CodeChange(
                file_path="Dockerfile",
                change_type="added",
                diff="""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["python", "-m", "app"]
""",
                purpose="Add Dockerfile for deployment",
            ))
            
            changes.append(CodeChange(
                file_path="docker-compose.yml",
                change_type="added",
                diff="""version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
""",
                purpose="Add docker-compose configuration",
            ))
        else:
            changes.append(CodeChange(
                file_path="Dockerfile",
                change_type="added",
                diff="""FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
""",
                purpose="Add Dockerfile for deployment",
            ))
        
        return changes
    
    def _run_project_tests(self, project_path: str) -> List[TestResult]:
        """Run project tests"""
        results = []
        
        # Check for pytest
        if os.path.exists(os.path.join(project_path, "pytest.ini")):
            try:
                result = subprocess.run(
                    ["pytest", "-v", "--tb=short"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                
                # Parse pytest output
                for line in result.stdout.split("\n"):
                    if "PASSED" in line or "FAILED" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            test_name = parts[0]
                            passed = "PASSED" in line
                            results.append(TestResult(
                                test_name=test_name,
                                passed=passed,
                                duration_ms=0,  # Would need to parse this
                                error=None if passed else "Test failed",
                            ))
                
                if not results:
                    results.append(TestResult(
                        test_name="pytest_run",
                        passed=result.returncode == 0,
                        duration_ms=0,
                        error=None if result.returncode == 0 else result.stderr[:200],
                    ))
                    
            except subprocess.TimeoutExpired:
                results.append(TestResult(
                    test_name="pytest_run",
                    passed=False,
                    duration_ms=120000,
                    error="Test execution timed out",
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name="pytest_run",
                    passed=False,
                    duration_ms=0,
                    error=str(e),
                ))
        
        # Check for npm test
        if os.path.exists(os.path.join(project_path, "package.json")):
            try:
                result = subprocess.run(
                    ["npm", "test", "--", "--passWithNoTests"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                
                results.append(TestResult(
                    test_name="npm_test",
                    passed=result.returncode == 0,
                    duration_ms=0,
                    error=None if result.returncode == 0 else result.stderr[:200],
                ))
                
            except Exception as e:
                results.append(TestResult(
                    test_name="npm_test",
                    passed=False,
                    duration_ms=0,
                    error=str(e),
                ))
        
        return results
    
    def _generate_benchmarks(
        self,
        project_path: str,
        changes: List[CodeChange],
    ) -> List[BenchmarkResult]:
        """Generate benchmark comparison"""
        # In Phase 1, we don't have real before/after metrics
        # This would be expanded in later phases
        return []
    
    def rollback(self, project_path: str, baseline_id: str) -> bool:
        """
        Rollback to a previous baseline.
        
        Args:
            project_path: Path to project
            baseline_id: ID of the baseline to restore
        
        Returns:
            True if rollback was successful
        """
        baseline_dir = Path(project_path) / self.baseline_path / baseline_id
        
        if not baseline_dir.exists():
            return False
        
        try:
            # Restore files from baseline
            for src in baseline_dir.rglob("*"):
                if src.is_file():
                    rel_path = src.relative_to(baseline_dir)
                    dst = Path(project_path) / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            
            return True
            
        except Exception:
            return False
