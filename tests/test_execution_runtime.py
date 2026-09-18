"""
Tests for Execution Runtime - Real execution
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile

import pytest

from packages.contracts.models import (
    CompletionCriterion,
    LearningContent,
    TaskStatus,
    UpgradeTask,
)
from services.execution_runtime import ExecutionConfig, ExecutionRuntime


@pytest.fixture
def temp_project():
    """Create a temporary Python project for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple Python project
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        
        # Create main.py
        (project_dir / "main.py").write_text("""
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
""")
        
        # Create requirements.txt
        (project_dir / "requirements.txt").write_text("# No dependencies needed")
        
        yield str(project_dir)


class TestExecutionRuntime:
    """Test execution runtime with real execution"""
    
    def test_execute_testing_task(self, temp_project):
        """Test adding tests to a project"""
        task = UpgradeTask(
            id="test-task-1",
            project_id="test-project",
            gap_id="test-gap",
            title="增加测试覆盖",
            description="Add pytest tests",
            learning_content=LearningContent(),
            completion_criteria=[
                CompletionCriterion(
                    criterion="pytest.ini exists",
                    verification_method="file_exists",
                    evidence_type="config"
                ),
            ],
        )
        
        runtime = ExecutionRuntime(ExecutionConfig(
            save_baseline=False,  # Don't save baseline in tests
            run_tests=True,
        ))
        
        result = runtime.execute(task, temp_project)
        
        # Should complete successfully
        assert result.status == TaskStatus.COMPLETED
        
        # Should have created files
        assert len(result.changes) > 0
        
        # Check that pytest.ini was created
        pytest_ini = Path(temp_project) / "pytest.ini"
        assert pytest_ini.exists()
        
        # Check that tests directory was created
        tests_dir = Path(temp_project) / "tests"
        assert tests_dir.exists()
    
    def test_execute_logging_task(self, temp_project):
        """Test adding logging to a project"""
        task = UpgradeTask(
            id="test-task-2",
            project_id="test-project",
            gap_id="test-gap",
            title="增加日志记录",
            description="Add logging",
            learning_content=LearningContent(),
            completion_criteria=[
                CompletionCriterion(
                    criterion="logger.py exists",
                    verification_method="file_exists",
                    evidence_type="code"
                ),
            ],
        )
        
        runtime = ExecutionRuntime(ExecutionConfig(save_baseline=False))
        result = runtime.execute(task, temp_project)
        
        assert result.status == TaskStatus.COMPLETED
        
        # Check that logger.py was created
        logger_py = Path(temp_project) / "utils" / "logger.py"
        assert logger_py.exists()
    
    def test_execute_docker_task(self, temp_project):
        """Test adding Docker to a project"""
        task = UpgradeTask(
            id="test-task-3",
            project_id="test-project",
            gap_id="test-gap",
            title="增加容器化",
            description="Add Dockerfile",
            learning_content=LearningContent(),
            completion_criteria=[
                CompletionCriterion(
                    criterion="Dockerfile exists",
                    verification_method="file_exists",
                    evidence_type="config"
                ),
            ],
        )
        
        runtime = ExecutionRuntime(ExecutionConfig(save_baseline=False))
        result = runtime.execute(task, temp_project)
        
        assert result.status == TaskStatus.COMPLETED
        
        # Check that Dockerfile was created
        dockerfile = Path(temp_project) / "Dockerfile"
        assert dockerfile.exists()
        
        # Check that docker-compose.yml was created
        compose = Path(temp_project) / "docker-compose.yml"
        assert compose.exists()
    
    def test_run_command(self, temp_project):
        """Test running a real command"""
        runtime = ExecutionRuntime(ExecutionConfig())
        
        # Run a simple Python command
        result = runtime._run_command(
            ["python", "-c", "print('hello')"],
            temp_project,
            timeout=10,
        )
        
        assert result.return_code == 0
        assert "hello" in result.stdout
        assert not result.timed_out


class TestCommandExecution:
    """Test command execution"""
    
    def test_invalid_command(self, temp_project):
        """Test handling of invalid command"""
        runtime = ExecutionRuntime(ExecutionConfig())
        
        result = runtime._run_command(
            ["nonexistent_command_12345"],
            temp_project,
            timeout=5,
        )
        
        assert result.return_code != 0
    
    def test_timeout(self, temp_project):
        """Test command timeout"""
        runtime = ExecutionRuntime(ExecutionConfig(timeout_seconds=1))
        
        # Run a command that sleeps longer than timeout
        result = runtime._run_command(
            ["python", "-c", "import time; time.sleep(10)"],
            temp_project,
            timeout=1,
        )
        
        assert result.timed_out
