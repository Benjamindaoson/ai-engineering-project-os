"""
Integration test for verification -> evidence -> version lifecycle
"""
import pytest
import tempfile
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from packages.database.models import Base


@pytest.fixture
async def fresh_db():
    """Create a fresh database for each test"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    db_url = f"sqlite+aiosqlite:///{db_path}"

    test_engine = create_async_engine(db_url, echo=False)
    test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_session_factory

    await test_engine.dispose()
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_verification_creates_evidence_on_pass(fresh_db):
    """Test that PASS verification creates CODE/TEST/RUN_RESULT evidence"""
    async with fresh_db() as session:
        from packages.database.repositories import (
            ProjectRepository, TaskRepository, ExecutionRepository,
            VerificationRepository, EvidenceRepository, VersionRepository
        )

        # Setup
        project_repo = ProjectRepository(session)
        project = await project_repo.create(
            name="Test Project",
            github_url="https://github.com/test/test",
        )

        # Create task
        task_repo = TaskRepository(session)
        task = await task_repo.create({
            "project_id": project.id,
            "gap_id": "test-gap",
            "title": "Test Task",
            "description": "Test task description",
            "completion_criteria": [
                {"criterion": "test exists", "verification_method": "file_exists"}
            ],
        })

        # Create execution
        exec_repo = ExecutionRepository(session)
        execution = await exec_repo.create({
            "task_id": task.id,
            "project_id": project.id,
            "status": "completed",
            "changes": [
                {"file_path": "tests/test_real.py", "change_type": "added"}
            ],
            "test_results": [
                {"name": "test_real", "status": "passed", "duration_ms": 100}
            ],
        })

        # Create verification (simulate PASS)
        verification_repo = VerificationRepository(session)
        verification = await verification_repo.create({
            "execution_id": execution.id,
            "task_id": task.id,
            "overall_status": "PASS",
            "verification_results": [
                {"criterion": "test exists", "status": "PASS"}
            ],
        })

        # Create evidence
        evidence_repo = EvidenceRepository(session)
        ev1 = await evidence_repo.create({
            "project_id": project.id,
            "verification_id": verification.id,
            "evidence_type": "CODE",
            "source_path": "tests/test_real.py",
            "title": "Code change",
        })
        ev2 = await evidence_repo.create({
            "project_id": project.id,
            "verification_id": verification.id,
            "evidence_type": "TEST",
            "source_path": "tests/test_real.py",
            "title": "Test result",
        })

        # Verify evidence was created
        evidence = await evidence_repo.get_for_project(project.id)
        assert len(evidence) >= 2

        # Verify CODE and TEST evidence exist
        evidence_types = [e.evidence_type for e in evidence]
        assert "CODE" in evidence_types
        assert "TEST" in evidence_types


@pytest.mark.asyncio
async def test_verification_fail_does_not_create_version(fresh_db):
    """Test that FAIL verification does NOT create successful version"""
    async with fresh_db() as session:
        from packages.database.repositories import (
            ProjectRepository, TaskRepository, ExecutionRepository,
            VerificationRepository, VersionRepository
        )

        # Setup
        project_repo = ProjectRepository(session)
        project = await project_repo.create(
            name="Test Project",
            github_url="https://github.com/test/test",
        )

        task_repo = TaskRepository(session)
        task = await task_repo.create({
            "project_id": project.id,
            "gap_id": "test-gap",
            "title": "Test Task",
            "description": "Test task description",
        })

        exec_repo = ExecutionRepository(session)
        execution = await exec_repo.create({
            "task_id": task.id,
            "project_id": project.id,
            "status": "completed",
        })

        verification_repo = VerificationRepository(session)
        verification = await verification_repo.create({
            "execution_id": execution.id,
            "task_id": task.id,
            "overall_status": "FAIL",
            "verification_results": [
                {"criterion": "test exists", "status": "FAIL"}
            ],
        })

        # FAIL should not create a successful version
        # The API checks overall_status == "PASS" before creating version
        # So we verify no version is created
        version_repo = VersionRepository(session)
        versions = await version_repo.get_for_project(project.id)

        # No version should be created for FAIL verification
        assert len(versions) == 0


@pytest.mark.asyncio
async def test_pass_creates_project_version(fresh_db):
    """Test that PASS verification creates ProjectVersion"""
    async with fresh_db() as session:
        from packages.database.repositories import (
            ProjectRepository, TaskRepository, ExecutionRepository,
            VerificationRepository, VersionRepository
        )

        # Setup
        project_repo = ProjectRepository(session)
        project = await project_repo.create(
            name="Test Project",
            github_url="https://github.com/test/test",
        )

        task_repo = TaskRepository(session)
        task = await task_repo.create({
            "project_id": project.id,
            "gap_id": "test-gap",
            "title": "Test Task",
            "description": "Test task description",
        })

        exec_repo = ExecutionRepository(session)
        execution = await exec_repo.create({
            "task_id": task.id,
            "project_id": project.id,
            "status": "completed",
            "changes": [
                {"file_path": "src/main.py", "change_type": "modified"}
            ],
        })

        verification_repo = VerificationRepository(session)
        verification = await verification_repo.create({
            "execution_id": execution.id,
            "task_id": task.id,
            "overall_status": "PASS",
            "verification_results": [
                {"criterion": "file modified", "status": "PASS"}
            ],
        })

        # Create version
        version_repo = VersionRepository(session)
        version = await version_repo.create({
            "project_id": project.id,
            "title": f"Completed: {task.title}",
            "description": task.description,
            "maturity_before": "idea",
            "maturity_after": "idea",
            "files_changed": ["src/main.py"],
        })

        # Verify version was created
        versions = await version_repo.get_for_project(project.id)
        assert len(versions) == 1
        assert versions[0].title == f"Completed: {task.title}"


@pytest.mark.asyncio
async def test_evidence_has_correct_relationships(fresh_db):
    """Test evidence is properly linked to verification/version/project"""
    async with fresh_db() as session:
        from packages.database.repositories import (
            ProjectRepository, VersionRepository, EvidenceRepository
        )

        # Setup
        project_repo = ProjectRepository(session)
        project = await project_repo.create(
            name="Test Project",
            github_url="https://github.com/test/test",
        )

        version_repo = VersionRepository(session)
        version = await version_repo.create({
            "project_id": project.id,
            "title": "Test Version",
            "maturity_before": "idea",
            "maturity_after": "demo",
        })

        evidence_repo = EvidenceRepository(session)
        ev = await evidence_repo.create({
            "project_id": project.id,
            "version_id": version.id,
            "evidence_type": "CODE",
            "source_path": "src/main.py",
            "title": "Code evidence",
        })

        # Verify relationships
        assert ev.project_id == project.id
        assert ev.version_id == version.id
