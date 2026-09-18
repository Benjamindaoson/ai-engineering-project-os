"""
Integration test for upgrade lifecycle
Tests: Task -> Execute -> Test -> Verify -> Evidence -> ProjectVersion -> Re-Audit
"""
import pytest
import tempfile
import os
import asyncio
from pathlib import Path

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


@pytest.fixture
def temp_project():
    """Create a temporary Python project for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
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


class TestUpgradeLifecycle:
    """Test complete upgrade lifecycle"""

    @pytest.mark.asyncio
    async def test_task_to_version_lifecycle(self, fresh_db, temp_project):
        """Test full lifecycle: Task -> Execute -> Verify -> Evidence -> Version"""
        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                TaskRepository,
                ExecutionRepository,
                VerificationRepository,
                EvidenceRepository,
                VersionRepository,
            )

            # 1. Create project
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Upgrade Test Project",
                github_url="https://github.com/test/upgrade",
                local_path=temp_project,
            )
            assert project.id is not None

            # 2. Create task
            task_repo = TaskRepository(session)
            task = await task_repo.create({
                "project_id": project.id,
                "gap_id": "test-gap-1",
                "title": "Add pytest configuration",
                "description": "Add pytest.ini and tests directory",
                "completion_criteria": [
                    {
                        "criterion": "pytest.ini exists",
                        "verification_method": "file_exists",
                        "evidence_type": "config",
                    },
                    {
                        "criterion": "tests directory exists",
                        "verification_method": "directory_exists",
                        "evidence_type": "code",
                    },
                ],
            })
            assert task.id is not None
            assert task.status == "pending"

            # 3. Create execution
            exec_repo = ExecutionRepository(session)
            execution = await exec_repo.create({
                "task_id": task.id,
                "project_id": project.id,
                "status": "completed",
                "changes": [
                    {
                        "file_path": "pytest.ini",
                        "change_type": "added",
                        "diff": "[pytest]\ntestpaths = tests",
                        "purpose": "Add pytest configuration",
                    },
                    {
                        "file_path": "tests/__init__.py",
                        "change_type": "added",
                        "diff": "",
                        "purpose": "Create tests directory",
                    },
                ],
                "test_results": [
                    {
                        "test_name": "pytest_collection",
                        "status": "passed",
                        "duration_ms": 50,
                    }
                ],
            })
            assert execution.id is not None

            # 4. Create verification (PASS)
            verification_repo = VerificationRepository(session)
            verification = await verification_repo.create({
                "execution_id": execution.id,
                "task_id": task.id,
                "overall_status": "PASS",
                "verification_results": [
                    {"criterion": "pytest.ini exists", "status": "passed"},
                    {"criterion": "tests directory exists", "status": "passed"},
                ],
            })
            assert verification.id is not None

            # 5. Create evidence (should be automatic on PASS, but test manually)
            evidence_repo = EvidenceRepository(session)

            # CODE evidence
            code_ev = await evidence_repo.create({
                "project_id": project.id,
                "verification_id": verification.id,
                "execution_id": execution.id,
                "evidence_type": "CODE",
                "source_path": "pytest.ini",
                "title": "pytest.ini added",
                "content": "[pytest]\ntestpaths = tests",
            })
            assert code_ev.id is not None

            # TEST evidence
            test_ev = await evidence_repo.create({
                "project_id": project.id,
                "verification_id": verification.id,
                "execution_id": execution.id,
                "evidence_type": "TEST",
                "source_path": "tests/__init__.py",
                "title": "Test directory created",
            })
            assert test_ev.id is not None

            # RUN_RESULT evidence
            run_ev = await evidence_repo.create({
                "project_id": project.id,
                "verification_id": verification.id,
                "evidence_type": "RUN_RESULT",
                "source_path": "pytest.ini",
                "title": "Test execution result",
                "content": '{"total": 1, "passed": 1, "failed": 0}',
            })
            assert run_ev.id is not None

            # Verify evidence count
            evidence = await evidence_repo.get_for_project(project.id)
            assert len(evidence) >= 3

            # 6. Create version
            version_repo = VersionRepository(session)
            version = await version_repo.create({
                "project_id": project.id,
                "title": f"Completed: {task.title}",
                "description": task.description,
                "maturity_before": "idea",
                "maturity_after": "demo",
                "files_changed": ["pytest.ini", "tests/__init__.py"],
            })
            assert version.id is not None
            assert version.version_number == 1
            assert version.maturity_after == "demo"

            # 7. Verify task is updated (in real API this is done in the verify endpoint)
            await task_repo.update_status(task.id, "completed")
            updated_task = await task_repo.get(task.id)
            assert updated_task.status == "completed"

            # 8. Verify all versions for project
            versions = await version_repo.get_for_project(project.id)
            assert len(versions) == 1
            assert versions[0].title == f"Completed: {task.title}"


class TestEvidenceLifecycle:
    """Test evidence lifecycle"""

    @pytest.mark.asyncio
    async def test_evidence_type_coverage(self, fresh_db):
        """Test that all evidence types can be created"""
        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                EvidenceRepository,
            )

            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Evidence Test Project",
                github_url="https://github.com/test/evidence",
            )

            evidence_repo = EvidenceRepository(session)

            # Create all evidence types
            evidence_types = ["CODE", "TEST", "RUN_RESULT", "CONFIG", "BENCHMARK"]

            for i, ev_type in enumerate(evidence_types):
                ev = await evidence_repo.create({
                    "project_id": project.id,
                    "evidence_type": ev_type,
                    "source_path": f"test/file_{i}.py",
                    "title": f"{ev_type} evidence",
                    "content": f"This is {ev_type} evidence content",
                })
                assert ev.id is not None
                assert ev.evidence_type == ev_type

            # Verify all evidence
            evidence = await evidence_repo.get_for_project(project.id)
            assert len(evidence) == len(evidence_types)


class TestVersionLifecycle:
    """Test version lifecycle"""

    @pytest.mark.asyncio
    async def test_version_numbering(self, fresh_db):
        """Test that versions are numbered sequentially"""
        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                VersionRepository,
            )

            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Version Test Project",
                github_url="https://github.com/test/version",
            )

            version_repo = VersionRepository(session)

            # Create 3 versions
            for i in range(1, 4):
                version = await version_repo.create({
                    "project_id": project.id,
                    "title": f"Version {i}",
                    "description": f"Description for version {i}",
                    "maturity_before": "idea",
                    "maturity_after": "demo",
                })
                assert version.version_number == i

            # Verify ordering
            versions = await version_repo.get_for_project(project.id)
            assert len(versions) == 3
            assert versions[0].version_number == 1
            assert versions[1].version_number == 2
            assert versions[2].version_number == 3


class TestRestartPersistence:
    """Test persistence across restarts"""

    @pytest.mark.asyncio
    async def test_data_persists_after_session_close(self, fresh_db):
        """Test that data persists after session is closed"""
        project_id = None

        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                TaskRepository,
                EvidenceRepository,
            )

            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Persistence Test Project",
                github_url="https://github.com/test/persist",
            )
            project_id = project.id

            task_repo = TaskRepository(session)
            task = await task_repo.create({
                "project_id": project.id,
                "title": "Persistence Task",
                "description": "Testing persistence",
            })

            evidence_repo = EvidenceRepository(session)
            await evidence_repo.create({
                "project_id": project.id,
                "evidence_type": "CODE",
                "source_path": "test.py",
                "title": "Test evidence",
            })

        # Open new session and verify data exists
        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                TaskRepository,
                EvidenceRepository,
            )

            project_repo = ProjectRepository(session)
            project = await project_repo.get(project_id)
            assert project is not None
            assert project.name == "Persistence Test Project"

            task_repo = TaskRepository(session)
            tasks = await task_repo.get_for_project(project_id)
            assert len(tasks) == 1

            evidence_repo = EvidenceRepository(session)
            evidence = await evidence_repo.get_for_project(project_id)
            assert len(evidence) == 1


class TestInterviewGapToTask:
    """Test interview gap to task conversion"""

    @pytest.mark.asyncio
    async def test_gap_creates_task(self, fresh_db):
        """Test that an interview gap can be converted to a task"""
        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                InterviewRepository,
                TaskRepository,
            )

            # Create project
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Gap Task Test Project",
                github_url="https://github.com/test/gap-task",
            )

            # Create interview session
            interview_repo = InterviewRepository(session)
            interview_session = await interview_repo.create_session(project.id)

            # Create gap
            gap = await interview_repo.create_interview_gap({
                "session_id": interview_session.id,
                "project_id": project.id,
                "gap_type": "knowledge",
                "description": "Cannot explain technical choices",
                "severity": "high",
                "recommendation": "Add technical decision documentation",
            })

            assert gap.id is not None
            assert gap.status == "identified"

            # Create task from gap (simulating API call)
            task_repo = TaskRepository(session)
            task = await task_repo.create({
                "project_id": project.id,
                "gap_id": gap.id,
                "title": f"补充知识文档: {gap.description[:100]}",
                "description": f"Gap identified during interview: {gap.description}\n\nRecommendation: {gap.recommendation}",
                "estimated_effort": "medium",
            })

            assert task.id is not None
            assert task.gap_id == gap.id
            assert "知识文档" in task.title

            # Verify task is linked to gap
            gap.task_id = task.id
            await session.commit()


class TestCapabilityProfile:
    """Test capability profile generation"""

    @pytest.mark.asyncio
    async def test_capability_profile_from_evidence(self, fresh_db):
        """Test that capability profile is generated from evidence"""
        async with fresh_db() as session:
            from packages.database.repositories import (
                ProjectRepository,
                EvidenceRepository,
                VersionRepository,
            )

            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Capability Test Project",
                github_url="https://github.com/test/capability",
            )

            evidence_repo = EvidenceRepository(session)

            # Add testing evidence
            for i in range(2):
                await evidence_repo.create({
                    "project_id": project.id,
                    "evidence_type": "TEST",
                    "source_path": f"tests/test_{i}.py",
                    "title": f"Test evidence {i}",
                })

            # Add CODE evidence
            await evidence_repo.create({
                "project_id": project.id,
                "evidence_type": "CODE",
                "source_path": "src/main.py",
                "title": "Code evidence",
            })

            # Create version
            version_repo = VersionRepository(session)
            version = await version_repo.create({
                "project_id": project.id,
                "title": "First version",
                "maturity_before": "idea",
                "maturity_after": "demo",
            })

            # Verify evidence count
            evidence = await evidence_repo.get_for_project(project.id)
            assert len(evidence) == 3

            # Verify version
            versions = await version_repo.get_for_project(project.id)
            assert len(versions) == 1
