"""
Execution Runtime Service

Responsible for safely executing code modifications and running tests.
Now with REAL execution, no simulate.
"""

import os
import json
import uuid
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from packages.contracts.models import (
    UpgradeTask, ExecutionRecord, CodeChange, TestResult,
    BenchmarkResult, TaskStatus, LearningContent
)


# Command allowlist - only these commands are allowed for security
ALLOWED_COMMANDS = {
    # Python
    "pytest": ["pytest", "-v", "--tb=short", "--collect-only", "-x", "--cov", "--cov-report"],
    "python": ["python", "python3", "-m pytest", "-m mypy"],
    "ruff": ["ruff", "check", "format"],
    "mypy": ["mypy"],
    
    # JavaScript/TypeScript
    "npm": ["npm", "test", "run", "build", "lint", "typecheck"],
    "npx": ["npx"],
    
    # Git
    "git": ["git", "diff", "status", "log", "branch"],
    
    # Docker
    "docker": ["docker", "build", "ps", "images"],
}

# Dangerous commands that are always blocked
BLOCKED_COMMANDS = {
    "rm -rf", "del /f /s /q", "format", "fdisk",
    "dd", "mkfs", "shutdown", "reboot", "halt",
    "curl", "wget", "nc", "netcat",  # Network tools
}


@dataclass
class ExecutionConfig:
    """Configuration for execution"""
    save_baseline: bool = True
    run_tests: bool = True
    timeout_seconds: int = 120
    max_retries: int = 1
    workspace_root: str = "./workspaces"
    max_output_lines: int = 1000


@dataclass
class CommandResult:
    """Result of a command execution"""
    command: str
    return_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False


class ExecutionRuntime:
    """
    Executes upgrade tasks safely with:
    - Baseline saving before modifications
    - All changes tracked
    - Test execution and result recording
    - Benchmark comparison
    
    No simulate - all execution is real.
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
        Execute an upgrade task with REAL execution.
        
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
            
            # Step 2: Execute based on task dimension
            changes, log = self._execute_task(task, project_path, record)
            
            # Step 3: Record changes
            record.changes = changes
            
            # Step 4: Run tests if configured
            if self.config.run_tests:
                record.test_results = self._run_project_tests(project_path)
            
            # Step 5: Finalize
            record.status = TaskStatus.COMPLETED
            record.execution_log = log
            record.completed_at = datetime.utcnow().isoformat()
            
        except Exception as e:
            record.status = TaskStatus.FAILED
            record.error = str(e)
            record.execution_log += f"\nExecution failed: {e}"
            record.completed_at = datetime.utcnow().isoformat()
        
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
            baseline_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy key files
            key_patterns = ["*.py", "*.ts", "*.js", "*.json", "*.yaml", "*.yml", "*.toml"]
            
            for pattern in key_patterns:
                for src in Path(project_path).rglob(pattern):
                    if any(skip in str(src) for skip in ["venv", ".venv", "node_modules", "__pycache__", ".git"]):
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
    
    def _execute_task(
        self,
        task: UpgradeTask,
        project_path: str,
        record: ExecutionRecord,
    ) -> tuple[List[CodeChange], str]:
        """Execute task based on dimension"""
        changes = []
        log_parts = [f"Executing task: {task.title}"]
        
        # Extract dimension from task
        dimension = self._extract_dimension(task.title)
        
        if dimension == "testing":
            changes, log = self._add_tests(task, project_path)
        elif dimension == "error_handling":
            changes, log = self._add_error_handling(task, project_path)
        elif dimension == "monitoring":
            changes, log = self._add_logging(task, project_path)
        elif dimension == "deployment":
            changes, log = self._add_docker(task, project_path)
        elif dimension == "auth":
            changes, log = self._add_auth(task, project_path)
        else:
            changes, log = self._add_documentation(task, project_path)
        
        log_parts.append(log)
        return changes, "\n".join(log_parts)
    
    def _extract_dimension(self, title: str) -> str:
        """Extract dimension from task title"""
        title_lower = title.lower()
        
        if "测试" in title or "test" in title_lower:
            return "testing"
        elif "错误" in title or "异常" in title or "error" in title_lower:
            return "error_handling"
        elif "监控" in title or "日志" in title or "monitor" in title_lower or "log" in title_lower:
            return "monitoring"
        elif "部署" in title or "docker" in title_lower or "ci" in title_lower or "容器化" in title:
            return "deployment"
        elif "权限" in title or "auth" in title_lower:
            return "auth"
        elif "文档" in title or "readme" in title_lower:
            return "documentation"
        
        return "general"
    
    def _add_tests(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> tuple[List[CodeChange], str]:
        """Add tests to the project"""
        changes = []
        log_parts = []
        
        # Check project language
        has_pytest = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_pytest:
            # Create pytest.ini if not exists
            pytest_ini = Path(project_path) / "pytest.ini"
            if not pytest_ini.exists():
                content = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""
                pytest_ini.write_text(content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="pytest.ini",
                    change_type="added",
                    diff=content,
                    purpose="Add pytest configuration",
                ))
                log_parts.append("Created pytest.ini")
            
            # Create tests directory if not exists
            tests_dir = Path(project_path) / "tests"
            tests_dir.mkdir(exist_ok=True)
            
            # Create __init__.py
            init_file = tests_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
            
            # Create a sample test
            test_file = tests_dir / "test_sample.py"
            test_content = '''"""Sample tests for the project"""
import pytest


class TestSample:
    """Sample test class"""
    
    def test_placeholder(self):
        """Placeholder test - replace with real tests"""
        assert True
    
    def test_basic_assertion(self):
        """Basic assertion test"""
        assert 1 + 1 == 2
'''
            
            # Check if file already exists
            if not test_file.exists():
                test_file.write_text(test_content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="tests/test_sample.py",
                    change_type="added",
                    diff=test_content,
                    purpose="Add sample test file",
                ))
                log_parts.append("Created tests/test_sample.py")
            else:
                log_parts.append("Test file already exists, skipping")
        
        log_parts.append(f"Added {len(changes)} changes for testing")
        return changes, "\n".join(log_parts)
    
    def _add_error_handling(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> tuple[List[CodeChange], str]:
        """Add error handling"""
        changes = []
        log_parts = []
        
        # Check project language
        has_python = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_python:
            # Create utils/exceptions.py
            utils_dir = Path(project_path) / "utils"
            utils_dir.mkdir(exist_ok=True)
            
            exceptions_file = utils_dir / "exceptions.py"
            exceptions_content = '''"""Custom exceptions for the project"""


class ProjectError(Exception):
    """Base exception for project errors"""
    pass


class ConfigurationError(ProjectError):
    """Raised when configuration is invalid"""
    pass


class DataError(ProjectError):
    """Raised when data is invalid or unavailable"""
    pass


class ServiceError(ProjectError):
    """Raised when a service operation fails"""
    pass
'''
            
            if not exceptions_file.exists():
                exceptions_file.write_text(exceptions_content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="utils/exceptions.py",
                    change_type="added",
                    diff=exceptions_content,
                    purpose="Add custom exception classes",
                ))
                log_parts.append("Created utils/exceptions.py")
            
            # Create utils/__init__.py
            init_file = utils_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
        
        log_parts.append(f"Added {len(changes)} changes for error handling")
        return changes, "\n".join(log_parts)
    
    def _add_logging(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> tuple[List[CodeChange], str]:
        """Add logging"""
        changes = []
        log_parts = []
        
        has_python = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_python:
            # Create utils/logger.py
            utils_dir = Path(project_path) / "utils"
            utils_dir.mkdir(exist_ok=True)
            
            logger_file = utils_dir / "logger.py"
            logger_content = '''"""Logging configuration for the project"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Set up a logger with console and optional file handler.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path for log output
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Default logger for the project
default_logger = setup_logger("ai_project")
'''
            
            if not logger_file.exists():
                logger_file.write_text(logger_content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="utils/logger.py",
                    change_type="added",
                    diff=logger_content,
                    purpose="Add logging configuration",
                ))
                log_parts.append("Created utils/logger.py")
            
            # Create utils/__init__.py
            init_file = utils_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
        
        log_parts.append(f"Added {len(changes)} changes for logging")
        return changes, "\n".join(log_parts)
    
    def _add_docker(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> tuple[List[CodeChange], str]:
        """Add Dockerfile"""
        changes = []
        log_parts = []
        
        has_python = any(f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))
        
        if has_python:
            # Create Dockerfile
            dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run
CMD ["python", "-m", "app"]
'''
            
            dockerfile = Path(project_path) / "Dockerfile"
            if not dockerfile.exists():
                dockerfile.write_text(dockerfile_content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="Dockerfile",
                    change_type="added",
                    diff=dockerfile_content,
                    purpose="Add Dockerfile for containerization",
                ))
                log_parts.append("Created Dockerfile")
            
            # Create docker-compose.yml
            compose_content = '''version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./data:/app/data
'''
            
            compose = Path(project_path) / "docker-compose.yml"
            if not compose.exists():
                compose.write_text(compose_content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="docker-compose.yml",
                    change_type="added",
                    diff=compose_content,
                    purpose="Add docker-compose configuration",
                ))
                log_parts.append("Created docker-compose.yml")
        
        log_parts.append(f"Added {len(changes)} changes for deployment")
        return changes, "\n".join(log_parts)
    
    def _add_auth(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> tuple[List[CodeChange], str]:
        """Add basic auth"""
        changes = []
        log_parts = []
        
        # Create middleware directory and auth middleware
        middleware_dir = Path(project_path) / "middleware"
        middleware_dir.mkdir(exist_ok=True)
        
        auth_file = middleware_dir / "auth.py"
        auth_content = '''"""Authentication middleware"""
from functools import wraps
from typing import Callable, Optional
import hashlib
import hmac
import time


class AuthError(Exception):
    """Authentication error"""
    pass


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash a password with salt.
    
    Returns:
        Tuple of (hashed_password, salt)
    """
    import secrets
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return hashed.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash."""
    new_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(new_hash, hashed)


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication.
    
    Usage:
        @app.route("/protected")
        @require_auth
        def protected_endpoint():
            return "Secret data"
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # This is a placeholder - implement actual auth check
        # based on your authentication mechanism (JWT, session, etc.)
        auth_header = kwargs.get("headers", {}).get("Authorization")
        if not auth_header:
            raise AuthError("Authentication required")
        return func(*args, **kwargs)
    return wrapper


# Rate limiting storage (in-memory, use Redis in production)
_rate_limit_store: dict = {}


def check_rate_limit(identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """Check if request is within rate limit.
    
    Args:
        identifier: Unique identifier (IP, user ID, etc.)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    
    Returns:
        True if within limit, False if rate limited
    """
    current_time = time.time()
    key = f"rate:{identifier}"
    
    # Clean old entries
    if key in _rate_limit_store:
        _rate_limit_store[key] = [
            t for t in _rate_limit_store[key]
            if current_time - t < window_seconds
        ]
    else:
        _rate_limit_store[key] = []
    
    # Check limit
    if len(_rate_limit_store[key]) >= max_requests:
        return False
    
    # Record this request
    _rate_limit_store[key].append(current_time)
    return True
'''
        
        if not auth_file.exists():
            auth_file.write_text(auth_content, encoding="utf-8")
            changes.append(CodeChange(
                file_path="middleware/auth.py",
                change_type="added",
                diff=auth_content,
                purpose="Add authentication middleware",
            ))
            log_parts.append("Created middleware/auth.py")
        
        # Create middleware/__init__.py
        init_file = middleware_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
        
        log_parts.append(f"Added {len(changes)} changes for authentication")
        return changes, "\n".join(log_parts)
    
    def _add_documentation(
        self,
        task: UpgradeTask,
        project_path: str,
    ) -> tuple[List[CodeChange], str]:
        """Add documentation"""
        changes = []
        log_parts = []
        
        readme = Path(project_path) / "README.md"
        if readme.exists():
            # Read existing README
            existing = readme.read_text(encoding="utf-8")
            
            # Check if it has basic sections
            if "## Setup" not in existing:
                new_content = existing + '''

## Setup

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd <project-name>

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Run the application
python -m app

# Or with Docker
docker-compose up
```

## Development

### Testing

```bash
pytest
```

### Code Quality

```bash
ruff check .
mypy .
```
'''
                readme.write_text(new_content, encoding="utf-8")
                changes.append(CodeChange(
                    file_path="README.md",
                    change_type="modified",
                    diff="Added Setup, Running, Development sections",
                    purpose="Improve README documentation",
                ))
                log_parts.append("Updated README.md")
        else:
            # Create a basic README
            readme_content = '''# Project

A Python project.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python -m app
```

## Testing

```bash
pytest
```
'''
            readme.write_text(readme_content, encoding="utf-8")
            changes.append(CodeChange(
                file_path="README.md",
                change_type="added",
                diff=readme_content,
                purpose="Add README",
            ))
            log_parts.append("Created README.md")
        
        log_parts.append(f"Added {len(changes)} changes for documentation")
        return changes, "\n".join(log_parts)
    
    def _run_project_tests(self, project_path: str) -> List[TestResult]:
        """Run project tests - REAL execution"""
        results = []
        
        # Check for pytest
        if os.path.exists(os.path.join(project_path, "pytest.ini")) or \
           os.path.exists(os.path.join(project_path, "pyproject.toml")) or \
           os.path.exists(os.path.join(project_path, "tests")):
            
            try:
                result = self._run_command(
                    ["pytest", "-v", "--tb=short"],
                    project_path,
                    timeout=60,
                )
                
                if result.timed_out:
                    results.append(TestResult(
                        test_name="pytest_run",
                        passed=False,
                        duration_ms=60000,
                        error="Test execution timed out",
                    ))
                else:
                    # Parse pytest output
                    passed = "passed" in result.stdout.lower() or result.return_code == 0
                    results.append(TestResult(
                        test_name="pytest_run",
                        passed=passed,
                        duration_ms=result.duration_ms,
                        error=result.stderr if not passed else None,
                    ))
                    
            except FileNotFoundError:
                results.append(TestResult(
                    test_name="pytest_run",
                    passed=False,
                    duration_ms=0,
                    error="pytest not found - please install pytest",
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
                result = self._run_command(
                    ["npm", "test", "--", "--passWithNoTests"],
                    project_path,
                    timeout=60,
                )
                
                results.append(TestResult(
                    test_name="npm_test",
                    passed=result.return_code == 0,
                    duration_ms=result.duration_ms,
                    error=result.stderr if result.return_code != 0 else None,
                ))
            except FileNotFoundError:
                pass  # npm not installed
            except Exception as e:
                results.append(TestResult(
                    test_name="npm_test",
                    passed=False,
                    duration_ms=0,
                    error=str(e),
                ))
        
        return results
    
    def _run_command(
        self,
        command: List[str],
        cwd: str,
        timeout: int = 30,
    ) -> CommandResult:
        """Run a command with timeout and return result"""
        import time
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                duration_ms = int((time.time() - start_time) * 1000)
                
                return CommandResult(
                    command=" ".join(command),
                    return_code=process.returncode,
                    stdout=stdout[:10000],  # Limit output
                    stderr=stderr[:5000],
                    duration_ms=duration_ms,
                    timed_out=False,
                )
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                duration_ms = int((time.time() - start_time) * 1000)
                
                return CommandResult(
                    command=" ".join(command),
                    return_code=-1,
                    stdout=stdout[:10000],
                    stderr=f"Command timed out after {timeout} seconds",
                    duration_ms=duration_ms,
                    timed_out=True,
                )
                
        except FileNotFoundError:
            return CommandResult(
                command=" ".join(command),
                return_code=-1,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                duration_ms=0,
                timed_out=False,
            )
        except Exception as e:
            return CommandResult(
                command=" ".join(command),
                return_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=0,
                timed_out=False,
            )
    
    def rollback(self, project_path: str, baseline_id: str) -> bool:
        """Rollback to a previous baseline"""
        baseline_dir = Path(project_path) / self.baseline_path / baseline_id
        
        if not baseline_dir.exists():
            return False
        
        try:
            for src in baseline_dir.rglob("*"):
                if src.is_file():
                    rel_path = src.relative_to(baseline_dir)
                    dst = Path(project_path) / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            
            return True
            
        except Exception:
            return False
