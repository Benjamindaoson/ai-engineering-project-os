"""
Repository Layer

Data access layer for the AI Engineering Project OS.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.database.models import (
    Project, RepositorySnapshot, ProjectFact, MaturityAssessment,
    Gap, EngineeringTask, ExecutionRun, VerificationResult,
    Evidence, ProjectVersion, InterviewSession, InterviewQuestion
)


class ProjectRepository:
    """Repository for Project operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, name: str, github_url: str = None, local_path: str = None) -> Project:
        """Create a new project"""
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            github_url=github_url,
            local_path=local_path,
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project
    
    async def get(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.snapshots),
                selectinload(Project.facts),
                selectinload(Project.assessments),
                selectinload(Project.gaps),
                selectinload(Project.tasks),
                selectinload(Project.versions),
            )
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
    
    async def list_all(self) -> List[Project]:
        """List all projects"""
        result = await self.session.execute(select(Project))
        return list(result.scalars().all())
    
    async def update_maturity(self, project_id: str, maturity: str):
        """Update project maturity"""
        await self.session.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(current_maturity=maturity, updated_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def delete(self, project_id: str):
        """Delete project"""
        await self.session.execute(
            delete(Project).where(Project.id == project_id)
        )
        await self.session.commit()


class SnapshotRepository:
    """Repository for RepositorySnapshot operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        project_id: str,
        repo_url: str,
        commit_sha: str,
        workspace_path: str,
        branch: str = "main"
    ) -> RepositorySnapshot:
        """Create a new snapshot"""
        snapshot = RepositorySnapshot(
            id=str(uuid.uuid4()),
            project_id=project_id,
            repo_url=repo_url,
            branch=branch,
            commit_sha=commit_sha,
            workspace_path=workspace_path,
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot
    
    async def get_latest(self, project_id: str) -> Optional[RepositorySnapshot]:
        """Get latest snapshot for project"""
        result = await self.session.execute(
            select(RepositorySnapshot)
            .where(RepositorySnapshot.project_id == project_id)
            .order_by(RepositorySnapshot.imported_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class FactRepository:
    """Repository for ProjectFact operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        project_id: str,
        snapshot_id: str,
        languages: List[str],
        frameworks: List[str],
        databases: List[str],
        deployment: List[str],
        project_type: str,
        total_files: int,
        total_lines: int,
        code_lines: int,
        test_files: int,
        config_files: int,
        has_readme: bool,
        has_api_docs: bool,
        has_deployment_docs: bool,
        implementation_status: Dict[str, Any],
        raw_observations: List[Dict[str, Any]],
    ) -> ProjectFact:
        """Create new project facts"""
        fact = ProjectFact(
            id=str(uuid.uuid4()),
            project_id=project_id,
            snapshot_id=snapshot_id,
            languages=languages,
            frameworks=frameworks,
            databases=databases,
            deployment=deployment,
            project_type=project_type,
            total_files=total_files,
            total_lines=total_lines,
            code_lines=code_lines,
            test_files=test_files,
            config_files=config_files,
            has_readme=has_readme,
            has_api_docs=has_api_docs,
            has_deployment_docs=has_deployment_docs,
            implementation_status=implementation_status,
            raw_observations=raw_observations,
        )
        self.session.add(fact)
        await self.session.commit()
        await self.session.refresh(fact)
        return fact
    
    async def get_latest(self, project_id: str) -> Optional[ProjectFact]:
        """Get latest facts for project"""
        result = await self.session.execute(
            select(ProjectFact)
            .where(ProjectFact.project_id == project_id)
            .order_by(ProjectFact.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class AssessmentRepository:
    """Repository for MaturityAssessment operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        project_id: str,
        snapshot_id: str,
        overall_level: str,
        dimension_scores: Dict[str, Any],
        blockers: List[Dict[str, Any]],
        recommendations: List[str],
    ) -> MaturityAssessment:
        """Create new assessment"""
        assessment = MaturityAssessment(
            id=str(uuid.uuid4()),
            project_id=project_id,
            snapshot_id=snapshot_id,
            overall_level=overall_level,
            dimension_scores=dimension_scores,
            blockers=blockers,
            recommendations=recommendations,
        )
        self.session.add(assessment)
        await self.session.commit()
        await self.session.refresh(assessment)
        return assessment
    
    async def get_latest(self, project_id: str) -> Optional[MaturityAssessment]:
        """Get latest assessment for project"""
        result = await self.session.execute(
            select(MaturityAssessment)
            .where(MaturityAssessment.project_id == project_id)
            .order_by(MaturityAssessment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class GapRepository:
    """Repository for Gap operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_batch(self, gaps: List[Dict[str, Any]]) -> List[Gap]:
        """Create multiple gaps"""
        gap_objects = []
        for g in gaps:
            gap = Gap(
                id=str(uuid.uuid4()),
                project_id=g["project_id"],
                dimension=g["dimension"],
                description=g["description"],
                current_state=g.get("current_state", ""),
                target_state=g.get("target_state", ""),
                priority=g.get("priority", "medium"),
                effort_estimate=g.get("effort_estimate", "medium"),
                risk=g.get("risk", "medium"),
                related_criteria=g.get("related_criteria", []),
            )
            self.session.add(gap)
            gap_objects.append(gap)
        
        await self.session.commit()
        for gap in gap_objects:
            await self.session.refresh(gap)
        return gap_objects
    
    async def get_for_project(self, project_id: str) -> List[Gap]:
        """Get all gaps for project"""
        result = await self.session.execute(
            select(Gap)
            .where(Gap.project_id == project_id)
            .order_by(Gap.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def delete_for_project(self, project_id: str):
        """Delete all gaps for project"""
        await self.session.execute(
            delete(Gap).where(Gap.project_id == project_id)
        )
        await self.session.commit()


class TaskRepository:
    """Repository for EngineeringTask operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, task_data: Dict[str, Any]) -> EngineeringTask:
        """Create new task"""
        task = EngineeringTask(
            id=str(uuid.uuid4()),
            project_id=task_data["project_id"],
            gap_id=task_data.get("gap_id"),
            title=task_data["title"],
            description=task_data.get("description", ""),
            learning_content=task_data.get("learning_content", {}),
            completion_criteria=task_data.get("completion_criteria", []),
            estimated_effort=task_data.get("estimated_effort", ""),
            prerequisites=task_data.get("prerequisites", []),
            status="pending",
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task
    
    async def get(self, task_id: str) -> Optional[EngineeringTask]:
        """Get task by ID"""
        result = await self.session.execute(
            select(EngineeringTask)
            .options(selectinload(EngineeringTask.executions))
            .where(EngineeringTask.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_for_project(self, project_id: str) -> List[EngineeringTask]:
        """Get all tasks for project"""
        result = await self.session.execute(
            select(EngineeringTask)
            .where(EngineeringTask.project_id == project_id)
            .order_by(EngineeringTask.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update_status(self, task_id: str, status: str):
        """Update task status"""
        update_data = {"status": status}
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        await self.session.execute(
            update(EngineeringTask)
            .where(EngineeringTask.id == task_id)
            .values(**update_data)
        )
        await self.session.commit()


class ExecutionRepository:
    """Repository for ExecutionRun operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, execution_data: Dict[str, Any]) -> ExecutionRun:
        """Create new execution record"""
        execution = ExecutionRun(
            id=str(uuid.uuid4()),
            task_id=execution_data["task_id"],
            project_id=execution_data["project_id"],
            changes=execution_data.get("changes", []),
            test_results=execution_data.get("test_results", []),
            benchmark_results=execution_data.get("benchmark_results", []),
            execution_log=execution_data.get("execution_log", ""),
            status=execution_data.get("status", "pending"),
        )
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution
    
    async def get(self, execution_id: str) -> Optional[ExecutionRun]:
        """Get execution by ID"""
        result = await self.session.execute(
            select(ExecutionRun)
            .options(selectinload(ExecutionRun.verifications))
            .where(ExecutionRun.id == execution_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, execution_id: str, data: Dict[str, Any]):
        """Update execution record"""
        data["completed_at"] = datetime.utcnow()
        await self.session.execute(
            update(ExecutionRun)
            .where(ExecutionRun.id == execution_id)
            .values(**data)
        )
        await self.session.commit()


class VerificationRepository:
    """Repository for VerificationResult operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, verification_data: Dict[str, Any]) -> VerificationResult:
        """Create new verification result"""
        verification = VerificationResult(
            id=str(uuid.uuid4()),
            execution_id=verification_data["execution_id"],
            task_id=verification_data["task_id"],
            verification_results=verification_data.get("verification_results", []),
            overall_status=verification_data.get("overall_status", "unverifiable"),
            missing_evidence=verification_data.get("missing_evidence", []),
            recommendations=verification_data.get("recommendations", []),
        )
        self.session.add(verification)
        await self.session.commit()
        await self.session.refresh(verification)
        return verification


class EvidenceRepository:
    """Repository for Evidence operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, evidence_data: Dict[str, Any]) -> Evidence:
        """Create new evidence"""
        evidence = Evidence(
            id=str(uuid.uuid4()),
            project_id=evidence_data["project_id"],
            version_id=evidence_data.get("version_id"),
            evidence_type=evidence_data["evidence_type"],
            source_path=evidence_data["source_path"],
            title=evidence_data.get("title", ""),
            description=evidence_data.get("description", ""),
            content=evidence_data.get("content", ""),
            line_start=evidence_data.get("line_start"),
            line_end=evidence_data.get("line_end"),
            score=evidence_data.get("score", 0.0),
        )
        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)
        return evidence
    
    async def get_for_project(self, project_id: str) -> List[Evidence]:
        """Get all evidence for project"""
        result = await self.session.execute(
            select(Evidence)
            .where(Evidence.project_id == project_id)
            .order_by(Evidence.created_at.desc())
        )
        return list(result.scalars().all())


class VersionRepository:
    """Repository for ProjectVersion operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, version_data: Dict[str, Any]) -> ProjectVersion:
        """Create new version"""
        # Get next version number
        result = await self.session.execute(
            select(ProjectVersion)
            .where(ProjectVersion.project_id == version_data["project_id"])
            .order_by(ProjectVersion.version_number.desc())
            .limit(1)
        )
        last_version = result.scalar_one_or_none()
        next_number = (last_version.version_number + 1) if last_version else 1
        
        version = ProjectVersion(
            id=str(uuid.uuid4()),
            project_id=version_data["project_id"],
            version_number=next_number,
            title=version_data["title"],
            description=version_data.get("description", ""),
            maturity_before=version_data.get("maturity_before"),
            maturity_after=version_data.get("maturity_after"),
            files_changed=version_data.get("files_changed", []),
        )
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version
    
    async def get_for_project(self, project_id: str) -> List[ProjectVersion]:
        """Get all versions for project"""
        result = await self.session.execute(
            select(ProjectVersion)
            .where(ProjectVersion.project_id == project_id)
            .options(selectinload(ProjectVersion.evidence))
            .order_by(ProjectVersion.version_number.asc())
        )
        return list(result.scalars().all())


class InterviewRepository:
    """Repository for InterviewSession operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_session(self, project_id: str, task_id: str = None) -> InterviewSession:
        """Create new interview session"""
        session = InterviewSession(
            id=str(uuid.uuid4()),
            project_id=project_id,
            task_id=task_id,
            status="in_progress",
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Get interview session by ID"""
        result = await self.session.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.questions))
            .where(InterviewSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def create_question(self, question_data: Dict[str, Any]) -> InterviewQuestion:
        """Create new question"""
        question = InterviewQuestion(
            id=str(uuid.uuid4()),
            session_id=question_data["session_id"],
            question=question_data["question"],
            context=question_data.get("context", ""),
            follow_ups=question_data.get("follow_ups", []),
            gap_type=question_data.get("gap_type"),
        )
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def update_answer(self, question_id: str, answer: str):
        """Update question with user's answer"""
        await self.session.execute(
            update(InterviewQuestion)
            .where(InterviewQuestion.id == question_id)
            .values(user_answer=answer, status="answered")
        )
        await self.session.commit()

    async def get_session_questions(self, session_id: str) -> List[InterviewQuestion]:
        """Get all questions for a session"""
        result = await self.session.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.id)
        )
        return list(result.scalars().all())

    async def get_session_gaps(self, session_id: str) -> List[Dict[str, Any]]:
        """Get gaps identified during interview"""
        questions = await self.get_session_questions(session_id)
        gaps = []
        for q in questions:
            if q.gap_type and q.user_answer:
                gaps.append({
                    "gap_type": q.gap_type,
                    "description": f"Question about {q.gap_type}: {q.question[:100]}",
                    "severity": "medium",
                })
        return gaps
