"""
Tests for Database Layer - Real persistence
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


@pytest.fixture
async def test_db():
    """Create a test database"""
    # Use a temporary file for the test database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Create async engine
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    
    # Create tables
    from packages.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    yield session_factory
    
    # Cleanup
    await engine.dispose()
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.mark.asyncio
class TestDatabaseModels:
    """Test database models"""
    
    async def test_create_project(self, test_db):
        """Test creating a project"""
        from packages.database.repositories import ProjectRepository
        
        async with test_db() as session:
            repo = ProjectRepository(session)
            project = await repo.create(
                name="Test Project",
                github_url="https://github.com/test/project",
                local_path="/path/to/project",
            )
            
            assert project.id is not None
            assert project.name == "Test Project"
            assert project.current_maturity == "idea"
    
    async def test_get_project(self, test_db):
        """Test getting a project"""
        from packages.database.repositories import ProjectRepository
        
        async with test_db() as session:
            repo = ProjectRepository(session)
            
            # Create project
            created = await repo.create(name="Test Project")
            
            # Get project
            fetched = await repo.get(created.id)
            
            assert fetched is not None
            assert fetched.id == created.id
            assert fetched.name == "Test Project"
    
    async def test_list_projects(self, test_db):
        """Test listing projects"""
        from packages.database.repositories import ProjectRepository
        
        async with test_db() as session:
            repo = ProjectRepository(session)
            
            # Create multiple projects
            await repo.create(name="Project 1")
            await repo.create(name="Project 2")
            
            # List all
            projects = await repo.list_all()
            
            assert len(projects) == 2
    
    async def test_update_maturity(self, test_db):
        """Test updating project maturity"""
        from packages.database.repositories import ProjectRepository
        
        async with test_db() as session:
            repo = ProjectRepository(session)
            
            # Create project
            project = await repo.create(name="Test Project")
            
            # Update maturity
            await repo.update_maturity(project.id, "demo")
            
            # Fetch again
            updated = await repo.get(project.id)
            
            assert updated.current_maturity == "demo"


@pytest.mark.asyncio
class TestGapRepository:
    """Test gap repository"""
    
    async def test_create_gaps(self, test_db):
        """Test creating gaps"""
        from packages.database.repositories import ProjectRepository, GapRepository
        
        async with test_db() as session:
            project_repo = ProjectRepository(session)
            gap_repo = GapRepository(session)
            
            # Create project
            project = await project_repo.create(name="Test Project")
            
            # Create gaps
            gaps_data = [
                {
                    "project_id": project.id,
                    "dimension": "testing",
                    "description": "Missing tests",
                    "priority": "high",
                },
                {
                    "project_id": project.id,
                    "dimension": "deployment",
                    "description": "Missing Dockerfile",
                    "priority": "medium",
                },
            ]
            
            gaps = await gap_repo.create_batch(gaps_data)
            
            assert len(gaps) == 2
            assert all(g.id is not None for g in gaps)


@pytest.mark.asyncio
class TestTaskRepository:
    """Test task repository"""
    
    async def test_create_task(self, test_db):
        """Test creating a task"""
        from packages.database.repositories import ProjectRepository, TaskRepository
        
        async with test_db() as session:
            project_repo = ProjectRepository(session)
            task_repo = TaskRepository(session)
            
            # Create project
            project = await project_repo.create(name="Test Project")
            
            # Create task
            task = await task_repo.create({
                "project_id": project.id,
                "title": "Add tests",
                "description": "Add pytest tests",
                "estimated_effort": "1-2 days",
            })
            
            assert task.id is not None
            assert task.title == "Add tests"
            assert task.status == "pending"
