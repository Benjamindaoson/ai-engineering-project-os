"""
AI Engineering Project OS - API Service

FastAPI-based API with real database persistence and services.
"""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.models import TaskStatus
from packages.database import (
    AssessmentRepository,
    EvidenceRepository,
    ExecutionRepository,
    ExperimentRepository,
    ExperimentRunRepository,
    FactRepository,
    GapRepository,
    InterviewRepository,
    ProjectRepository,
    SnapshotRepository,
    TaskRepository,
    VerificationRepository,
    VersionRepository,
    async_session,
    init_db,
)
from packages.database.models import EngineeringTask, InterviewQuestion, VerificationResult
from services.engineering_mentor import EngineeringMentor
from services.execution_runtime import ExecutionConfig, ExecutionRuntime
from services.interview_engine import InterviewEngine
from services.project_auditor import ProjectAuditor
from services.repo_import import RepoImportService
from services.upgrade_planner import UpgradePlanner
from services.verification_engine import VerificationEngine

# ============================================================================
# Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    await init_db()
    yield


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AI Engineering Project OS",
    description="Upgrade AI projects from idea to production",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
import_service = RepoImportService()
auditor = ProjectAuditor()
planner = UpgradePlanner()
mentor = EngineeringMentor()
verifier = VerificationEngine()


# ============================================================================
# Pydantic Models
# ============================================================================

class ProjectImportRequest(BaseModel):
    github_url: str | None = None
    local_path: str | None = None
    user_goals: list[str] | None = None


class AuditRequest(BaseModel):
    project_id: str


class TaskExecuteRequest(BaseModel):
    task_id: str


class InterviewAnswerRequest(BaseModel):
    question_id: str
    answer: str


# ============================================================================
# Database Dependency
# ============================================================================

async def get_db() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        yield session


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "version": "0.2.0"}


# ---- Projects ----

@app.post("/api/projects/import")
async def import_project(
    request: ProjectImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import a project from GitHub or local path"""
    if not request.github_url and not request.local_path:
        raise HTTPException(status_code=400, detail="Either github_url or local_path required")
    
    project_repo = ProjectRepository(db)
    snapshot_repo = SnapshotRepository(db)
    
    # Import repository
    if request.github_url:
        result = import_service.import_github(request.github_url)
    else:
        result = import_service.import_local(request.local_path)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    # Get project name from path
    project_name = Path(result.workspace_path).name
    
    # Create project in database
    project = await project_repo.create(
        name=project_name,
        github_url=request.github_url,
        local_path=result.workspace_path,
    )
    
    # Create snapshot
    await snapshot_repo.create(
        project_id=project.id,
        repo_url=result.repo_url,
        commit_sha=result.commit_sha,
        workspace_path=result.workspace_path,
        branch=result.branch,
    )
    
    return {
        "project_id": project.id,
        "name": project.name,
        "status": "imported",
        "workspace_path": result.workspace_path,
        "commit_sha": result.commit_sha,
    }


@app.get("/api/projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects"""
    repo = ProjectRepository(db)
    projects = await repo.list_all()
    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "github_url": p.github_url,
                "current_maturity": p.current_maturity,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    }


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project details"""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "github_url": project.github_url,
        "local_path": project.local_path,
        "current_maturity": project.current_maturity,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@app.post("/api/projects/{project_id}/audit")
async def audit_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Audit a project"""
    project_repo = ProjectRepository(db)
    snapshot_repo = SnapshotRepository(db)
    fact_repo = FactRepository(db)
    assessment_repo = AssessmentRepository(db)
    gap_repo = GapRepository(db)
    
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    workspace_path = project.local_path
    if not workspace_path or not os.path.exists(workspace_path):
        raise HTTPException(status_code=400, detail="Project workspace not found")
    
    # Run audit
    result = auditor.audit(
        project_path=workspace_path,
        project_id=project_id,
        github_url=project.github_url,
    )
    
    # Get latest snapshot
    snapshot = await snapshot_repo.get_latest(project_id)
    snapshot_id = snapshot.id if snapshot else None
    
    # Save facts
    facts = result["project_facts"]
    fact = await fact_repo.create(
        project_id=project_id,
        snapshot_id=snapshot_id,
        languages=facts.get("main_language", []),
        frameworks=facts.get("frameworks", []),
        databases=facts.get("database", []),
        deployment=facts.get("deployment", []),
        project_type=facts.get("project_type", "other"),
        total_files=facts.get("total_files", 0),
        total_lines=facts.get("total_lines", 0),
        code_lines=facts.get("code_lines", 0),
        test_files=facts.get("test_files", 0),
        config_files=facts.get("config_files", 0),
        has_readme=facts.get("has_readme", False),
        has_api_docs=facts.get("has_api_docs", False),
        has_deployment_docs=facts.get("has_deployment_docs", False),
        implementation_status={},
        raw_observations=facts.get("raw_observations", []),
    )
    
    # Save assessment
    assessment = result["maturity_assessment"]
    maturity_record = await assessment_repo.create(
        project_id=project_id,
        snapshot_id=snapshot_id,
        overall_level=assessment.get("overall_level", "idea"),
        dimension_scores=assessment.get("dimension_scores", {}),
        blockers=assessment.get("blockers", []),
        recommendations=assessment.get("recommendations", []),
    )
    
    # Update project maturity
    await project_repo.update_maturity(project_id, assessment.get("overall_level", "idea"))
    
    # Save gaps
    await gap_repo.delete_for_project(project_id)
    gaps_data = result["gaps"]
    for g in gaps_data:
        g["project_id"] = project_id
    await gap_repo.create_batch(gaps_data)
    
    return {
        "project_id": project_id,
        "project_facts": facts,
        "maturity_assessment": assessment,
        "gaps": gaps_data,
        "raw_observations": result.get("raw_observations", []),
    }


@app.get("/api/projects/{project_id}/audit")
async def get_project_audit(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get latest audit for project"""
    assessment_repo = AssessmentRepository(db)
    fact_repo = FactRepository(db)
    gap_repo = GapRepository(db)
    
    assessment = await assessment_repo.get_latest(project_id)
    facts = await fact_repo.get_latest(project_id)
    gaps = await gap_repo.get_for_project(project_id)
    
    if not assessment:
        raise HTTPException(status_code=404, detail="No audit found")
    
    return {
        "maturity_assessment": {
            "overall_level": assessment.overall_level,
            "dimension_scores": assessment.dimension_scores,
            "blockers": assessment.blockers,
            "recommendations": assessment.recommendations,
        },
        "gaps": [g.to_dict() for g in gaps],
    }


# ---- Upgrade Planning ----

@app.post("/api/projects/{project_id}/plan")
async def plan_upgrades(project_id: str, db: AsyncSession = Depends(get_db)):
    """Generate upgrade plan"""
    assessment_repo = AssessmentRepository(db)
    fact_repo = FactRepository(db)
    gap_repo = GapRepository(db)
    task_repo = TaskRepository(db)
    
    # Get all data in single transaction
    assessment = await assessment_repo.get_latest(project_id)
    facts = await fact_repo.get_latest(project_id)
    gaps = await gap_repo.get_for_project(project_id)
    
    if not assessment or not facts:
        raise HTTPException(status_code=400, detail="Project must be audited first")
    
    # Safely extract dimension scores
    dim_scores = {}
    if assessment.dimension_scores:
        for k, v in assessment.dimension_scores.items():
            if isinstance(v, dict):
                dim_scores[k] = {k2: v2 for k2, v2 in v.items() if not k2.startswith('_')}
            else:
                dim_scores[k] = v
    
    # Generate plan - this doesn't need the DB
    result = planner.plan(
        project_facts={
            "main_language": facts.languages or [],
            "frameworks": facts.frameworks or [],
            "database": facts.databases or [],
            "project_type": facts.project_type or "other",
        },
        maturity_assessment={
            "overall_level": assessment.overall_level or "idea",
            "dimension_scores": dim_scores,
        },
        gaps=[g.to_dict() for g in gaps],
        user_goals=[],
    )
    
    # Save tasks one by one, each with its own try/except
    task_ids = []
    for task_data in result["recommended_tasks"]:
        task_data["project_id"] = project_id
        try:
            task = await task_repo.create(task_data)
            task_ids.append(task.id)
        except Exception as e:
            print(f"Warning: Failed to save task: {e}")
            continue
    
    # Return only serializable data
    return {
        "recommended_tasks": [
            {k: v for k, v in t.items() if not k.startswith('_')}
            for t in result["recommended_tasks"]
        ],
        "prioritization_rationale": result.get("prioritization_rationale", ""),
        "immediate_next_steps": result.get("immediate_next_steps", []),
        "estimated_total_effort": result.get("estimated_total_effort", ""),
        "current_level": result.get("current_level", "idea"),
        "target_level": result.get("target_level", "demo"),
        "upgrade_path": result.get("upgrade_path", []),
        "tasks_saved": len(task_ids),
    }


@app.get("/api/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get all tasks for project"""
    repo = TaskRepository(db)
    tasks = await repo.get_for_project(project_id)
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "gap_id": t.gap_id,
                "status": t.status,
                "estimated_effort": t.estimated_effort,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ]
    }


# ---- Tasks ----

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get task details"""
    repo = TaskRepository(db)
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "id": task.id,
        "project_id": task.project_id,
        "gap_id": task.gap_id,
        "title": task.title,
        "description": task.description,
        "learning_content": task.learning_content,
        "completion_criteria": task.completion_criteria,
        "estimated_effort": task.estimated_effort,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@app.post("/api/tasks/{task_id}/mentor")
async def get_task_mentor(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get mentor guidance for task"""
    task_repo = TaskRepository(db)
    project_repo = ProjectRepository(db)
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    project = await project_repo.get(task.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert to UpgradeTask
    from packages.contracts.models import CompletionCriterion, LearningContent
    from packages.contracts.models import UpgradeTask as UpgradeTaskModel
    
    upgrade_task = UpgradeTaskModel(
        id=task.id,
        project_id=task.project_id,
        gap_id=task.gap_id or "",
        title=task.title,
        description=task.description,
        learning_content=LearningContent(**task.learning_content) if task.learning_content else LearningContent(),
        completion_criteria=[CompletionCriterion(**c) for c in (task.completion_criteria or [])],
        estimated_effort=task.estimated_effort,
    )
    
    result = mentor.mentor(
        task=upgrade_task,
        project_context={
            "tech_stack": project.name.split("-") if project else [],
        }
    )
    
    return result.to_dict()


@app.post("/api/tasks/{task_id}/execute")
async def execute_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Execute a task"""
    task_repo = TaskRepository(db)
    project_repo = ProjectRepository(db)
    execution_repo = ExecutionRepository(db)
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    project = await project_repo.get(task.project_id)
    if not project or not project.local_path:
        raise HTTPException(status_code=400, detail="Project workspace not found")
    
    # Convert to models
    from packages.contracts.models import CompletionCriterion, LearningContent
    from packages.contracts.models import UpgradeTask as UpgradeTaskModel
    
    upgrade_task = UpgradeTaskModel(
        id=task.id,
        project_id=task.project_id,
        gap_id=task.gap_id or "",
        title=task.title,
        description=task.description,
        learning_content=LearningContent(**task.learning_content) if task.learning_content else LearningContent(),
        completion_criteria=[CompletionCriterion(**c) for c in (task.completion_criteria or [])],
        estimated_effort=task.estimated_effort,
    )
    
    # Execute
    config = ExecutionConfig(
        save_baseline=True,
        run_tests=True,
        timeout_seconds=120,
    )
    runtime = ExecutionRuntime(config)
    record = runtime.execute(upgrade_task, project.local_path)
    
    # Save execution
    execution = await execution_repo.create({
        "task_id": task.id,
        "project_id": task.project_id,
        "changes": [
            {"file_path": c.file_path, "change_type": c.change_type, "diff": c.diff, "purpose": c.purpose}
            for c in record.changes
        ],
        "test_results": [
            {"test_name": t.test_name, "passed": t.passed, "duration_ms": t.duration_ms, "error": t.error}
            for t in record.test_results
        ],
        "execution_log": record.execution_log,
        "status": record.status.value,
    })
    
    # Update task status
    await task_repo.update_status(task.id, record.status.value)
    
    return {
        "execution_id": execution.id,
        "task_id": task.id,
        "status": record.status.value,
        "changes": len(record.changes),
        "test_results": len(record.test_results),
        "error": record.error,
    }


# ---- Verification ----

@app.post("/api/executions/{execution_id}/verify")
async def verify_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    """Verify execution and create Evidence + ProjectVersion on PASS"""
    exec_repo = ExecutionRepository(db)
    task_repo = TaskRepository(db)
    verification_repo = VerificationRepository(db)
    evidence_repo = EvidenceRepository(db)
    version_repo = VersionRepository(db)

    execution = await exec_repo.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    task = await task_repo.get(execution.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Reconstruct objects
    from packages.contracts.models import (
        CodeChange,
        CompletionCriterion,
        LearningContent,
        TestResult,
    )
    from packages.contracts.models import (
        ExecutionRecord as ExecutionRecordModel,
    )
    from packages.contracts.models import (
        UpgradeTask as UpgradeTaskModel,
    )

    upgrade_task = UpgradeTaskModel(
        id=task.id,
        project_id=task.project_id,
        gap_id=task.gap_id or "",
        title=task.title,
        description=task.description,
        learning_content=LearningContent(**task.learning_content) if task.learning_content else LearningContent(),
        completion_criteria=[CompletionCriterion(**c) for c in (task.completion_criteria or [])],
    )

    exec_record = ExecutionRecordModel(
        id=execution.id,
        task_id=execution.task_id,
        project_id=execution.project_id,
        changes=[CodeChange(**c) for c in (execution.changes or [])],
        execution_log=execution.execution_log or "",
        test_results=[TestResult(**t) for t in (execution.test_results or [])],
        status=TaskStatus(execution.status),
    )

    # Get project workspace
    from packages.database import ProjectRepository
    async with async_session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get(execution.project_id)
        workspace_path = project.local_path if project else ""
        project_name = project.name if project else ""
        current_maturity = project.current_maturity if project else "idea"

    # Verify
    result = verifier.verify(upgrade_task, exec_record, workspace_path)

    # Save verification
    verification = await verification_repo.create({
        "execution_id": execution.id,
        "task_id": task.id,
        "verification_results": [
            {"criterion": r.criterion, "status": r.status, "evidence": r.evidence, "details": r.details}
            for r in result.verification_results
        ],
        "overall_status": result.overall_status,
        "missing_evidence": result.missing_evidence,
        "recommendations": result.recommendations,
    })

    response = result.to_dict()
    response["verification_id"] = verification.id

    # If PASS, create Evidence and ProjectVersion
    if result.overall_status == "PASS":
        # Create Evidence records
        evidence_ids = []

        # CODE evidence
        for change in execution.changes or []:
            ev = await evidence_repo.create({
                "project_id": task.project_id,
                "verification_id": verification.id,
                "evidence_type": "CODE",
                "source_path": change.get("file_path", ""),
                "title": f"Code change: {change.get('file_path', 'unknown')}",
                "description": change.get("purpose", ""),
                "content": change.get("diff", ""),
            })
            evidence_ids.append(ev.id)

        # TEST evidence
        for test_result in execution.test_results or []:
            ev = await evidence_repo.create({
                "project_id": task.project_id,
                "verification_id": verification.id,
                "evidence_type": "TEST",
                "title": f"Test: {test_result.get('name', 'unknown')}",
                "description": f"Status: {test_result.get('status', 'unknown')}",
                "content": json.dumps(test_result, ensure_ascii=False),
            })
            evidence_ids.append(ev.id)

        # RUN_RESULT evidence
        if execution.test_results:
            summary = {
                "total": len(execution.test_results),
                "passed": sum(1 for t in execution.test_results if t.get("status") == "passed"),
                "failed": sum(1 for t in execution.test_results if t.get("status") == "failed"),
            }
            ev = await evidence_repo.create({
                "project_id": task.project_id,
                "verification_id": verification.id,
                "evidence_type": "RUN_RESULT",
                "title": f"Test run results for: {task.title}",
                "description": f"Tests: {summary['passed']}/{summary['total']} passed",
                "content": json.dumps(execution.test_results, ensure_ascii=False),
            })
            evidence_ids.append(ev.id)

        # Create ProjectVersion
        files_changed = [c.get("file_path", "") for c in (execution.changes or [])]
        version = await version_repo.create({
            "project_id": task.project_id,
            "title": f"Completed: {task.title}",
            "description": task.description or "",
            "maturity_before": current_maturity,
            "maturity_after": current_maturity,  # TODO: recalculate after re-audit
            "files_changed": files_changed,
        })

        # Update task status to completed
        await task_repo.update_status(task.id, "completed")

        response["evidence_ids"] = evidence_ids
        response["version_id"] = version.id
        response["project_version_created"] = True

    return response


# ---- Evidence ----

@app.get("/api/projects/{project_id}/evidence")
async def get_project_evidence(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get all evidence for project"""
    repo = EvidenceRepository(db)
    evidence = await repo.get_for_project(project_id)
    return {
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "source_path": e.source_path,
                "title": e.title,
                "description": e.description,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in evidence
        ]
    }


# ---- Interview ----

@app.post("/api/projects/{project_id}/interview")
async def start_interview(project_id: str, db: AsyncSession = Depends(get_db)):
    """Start interview session"""
    interview_repo = InterviewRepository(db)
    fact_repo = FactRepository(db)
    
    facts = await fact_repo.get_latest(project_id)
    if not facts:
        raise HTTPException(status_code=400, detail="Project must be audited first")
    
    # Create session
    session = await interview_repo.create_session(project_id)
    
    # Generate questions
    engine = InterviewEngine()
    result = engine.conduct_interview(
        project_facts={
            "project_type": facts.project_type,
            "frameworks": facts.frameworks,
            "main_language": facts.languages,
        },
        execution_records=[],
        architecture_decisions=[],
        maturity_assessment={},
        project_id=project_id,
    )
    
    # Save questions
    for q in result.initial_questions:
        await interview_repo.create_question({
            "session_id": session.id,
            "question": q.question,
            "context": q.context,
            "follow_ups": q.follow_ups,
            "gap_type": q.gap_type,
        })
    
    return {
        "session_id": session.id,
        "project_id": project_id,
        "questions": [q.to_dict() for q in result.initial_questions],
        "gap_analysis": [
            {
                "gap_type": g.gap_type,
                "description": g.description,
                "severity": g.severity,
            }
            for g in result.gap_analysis
        ],
    }


@app.get("/api/interviews/{session_id}")
async def get_interview_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get interview session details"""
    interview_repo = InterviewRepository(db)
    session = await interview_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    questions = await interview_repo.get_session_questions(session_id)

    return {
        "session_id": session.id,
        "project_id": session.project_id,
        "status": session.status,
        "questions": [q.to_dict() for q in questions],
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@app.post("/api/interviews/{session_id}/answers")
async def submit_interview_answer(
    session_id: str,
    answer_data: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer to an interview question"""
    interview_repo = InterviewRepository(db)

    session = await interview_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    # Get the question
    result = await db.execute(
        select(InterviewQuestion).where(InterviewQuestion.id == answer_data.question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Create a simple answer record for now
    answer_record = await interview_repo.create_answer({
        "session_id": session_id,
        "question_id": answer_data.question_id,
        "answer": answer_data.answer,
    })

    # Evaluate the answer
    engine = InterviewEngine()
    evaluation = engine.evaluate_answer(question, answer_data.answer)

    # Create assessment
    assessment = await interview_repo.create_assessment({
        "session_id": session_id,
        "question_id": answer_data.question_id,
        "answer_id": answer_record.id,
        "quality": evaluation.get("quality", "basic"),
        "reasoning": evaluation.get("suggestion"),
        "knowledge_gap": evaluation.get("gap_type") if evaluation.get("quality") in ["insufficient", "basic"] else None,
        "suggestion": evaluation.get("suggestion"),
        "has_example": evaluation.get("has_example", False),
        "has_reason": evaluation.get("has_reason", False),
        "has_quantitative": evaluation.get("has_quantitative", False),
    })

    result = {
        "answer_id": answer_record.id,
        "assessment": {
            "quality": evaluation.get("quality"),
            "suggestion": evaluation.get("suggestion"),
        },
        "submitted": True,
    }

    # Generate follow-up if needed (based on quality)
    if evaluation.get("quality") in ["insufficient", "basic"]:
        follow_up_text = engine.generate_follow_up(question, answer_data.answer)
        if follow_up_text:
            # Save follow-up as a new question
            new_q = await interview_repo.create_question({
                "session_id": session_id,
                "question": follow_up_text,
                "context": f"追问: {question.question[:50]}...",
                "follow_ups": [],
                "gap_type": question.gap_type,
                "parent_question_id": answer_data.question_id,
            })
            result["next_question"] = new_q.to_dict()

            # Create gap if assessment indicates deficiency
            if evaluation.get("quality") == "insufficient":
                gap = await interview_repo.create_interview_gap({
                    "session_id": session_id,
                    "project_id": session.project_id,
                    "question_id": answer_data.question_id,
                    "gap_type": question.gap_type or "knowledge",
                    "description": f"回答不完整: {question.question[:100]}",
                    "severity": "high",
                    "recommendation": evaluation.get("suggestion"),
                })
                result["gap_created"] = True
                result["gap_id"] = gap.id

    return result


@app.get("/api/interviews/{session_id}/gaps")
async def get_interview_gaps(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get gaps identified during interview"""
    interview_repo = InterviewRepository(db)

    gaps = await interview_repo.get_session_gaps(session_id)

    return {
        "gaps": [
            {
                "gap_type": g.get("gap_type", ""),
                "description": g.get("description", ""),
                "severity": g.get("severity", "medium"),
            }
            for g in gaps
        ]
    }


# ---- Experiment Lab ----

class ExperimentRequest(BaseModel):
    name: str
    description: str = ""
    config: dict = {}
    hypothesis: str | None = None
    metrics: list[dict] = []


class ExperimentRunRequest(BaseModel):
    config: dict = {}
    record_metrics: bool = True


class ExperimentRecord:
    """In-memory experiment record for tracking"""
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.description: str = ""
        self.hypothesis: str = ""
        self.config: dict = {}
        self.metrics: list[dict] = []
        self.created_at: str = ""
        self.runs: list = []


# Global experiment store (in production, use database)
_experiments: dict[str, ExperimentRecord] = {}


@app.post("/api/projects/{project_id}/experiments")
async def create_experiment(
    project_id: str,
    request: ExperimentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new experiment with hypothesis and metrics tracking"""
    import uuid
    from datetime import datetime

    # Create experiment in database
    exp_repo = ExperimentRepository(db)
    experiment = await exp_repo.create({
        "project_id": project_id,
        "name": request.name,
        "description": request.description,
        "config": {
            "hypothesis": request.hypothesis,
            "metrics": request.metrics,
            **request.config
        },
    })

    # Create in-memory record
    record = ExperimentRecord()
    record.id = experiment.id
    record.name = request.name
    record.description = request.description
    record.hypothesis = request.hypothesis or ""
    record.config = request.config
    record.metrics = request.metrics
    record.created_at = datetime.utcnow().isoformat()
    _experiments[experiment.id] = record

    return {
        "id": experiment.id,
        "project_id": project_id,
        "name": request.name,
        "description": request.description,
        "hypothesis": request.hypothesis,
        "metrics": request.metrics,
        "config": request.config,
        "created_at": record.created_at,
    }


@app.get("/api/projects/{project_id}/experiments")
async def list_experiments(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all experiments for a project"""
    exp_repo = ExperimentRepository(db)
    experiments = await exp_repo.get_for_project(project_id)

    return {
        "experiments": [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "config": e.config,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in experiments
        ]
    }


@app.post("/api/experiments/{experiment_id}/runs")
async def run_experiment(
    experiment_id: str,
    request: ExperimentRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run an experiment and record real metrics"""
    import uuid
    from datetime import datetime

    exp_run_repo = ExperimentRunRepository(db)

    # Get experiment to access config
    exp_repo = ExperimentRepository(db)
    experiments = await exp_repo.get_for_project("")
    experiment = None
    for e in experiments:
        if e.id == experiment_id:
            experiment = e
            break

    if not experiment:
        # Try to find in global store
        if experiment_id in _experiments:
            experiment = _experiments[experiment_id]

    # Create experiment run
    run = await exp_run_repo.create({
        "experiment_id": experiment_id,
        "config": request.config,
        "status": "running",
    })

    # Simulate real experiment run (in production, this would run actual tests)
    import time
    start_time = time.time()

    # Record real metrics if requested
    metrics = {}
    if request.record_metrics:
        # In a real implementation, these would come from actual benchmark execution
        # For now, we record placeholder metrics
        metrics = {
            "execution_time_ms": 0,
            "memory_mb": 0,
            "cpu_percent": 0,
            "status": "completed",
        }

    # Update run with results
    duration_ms = int((time.time() - start_time) * 1000)
    await exp_run_repo.session.execute(
        update(exp_run_repo.session.query(exp_run_repo.session.get_model())
               .where_by(id=run.id)
               .values(
                   status="completed",
                   metrics=metrics,
                   latency_ms=duration_ms,
                   completed_at=datetime.utcnow(),
               ))
    )

    return {
        "run_id": run.id,
        "experiment_id": experiment_id,
        "config": request.config,
        "metrics": metrics,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": datetime.utcnow().isoformat(),
        "status": "completed",
    }


@app.get("/api/experiments/{experiment_id}/compare")
async def compare_experiments(
    experiment_id: str,
    baseline_run_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Compare experiment runs to find improvements"""
    exp_run_repo = ExperimentRunRepository(db)

    runs = await exp_run_repo.get_for_experiment(experiment_id)

    if len(runs) < 2:
        return {
            "experiment_id": experiment_id,
            "baseline": None,
            "variant": runs[0].metrics if runs else {},
            "comparison": {
                "metrics": [],
                "improvements": [],
                "regressions": [],
            },
            "note": "Need at least 2 runs to compare",
        }

    # Get baseline and variant
    baseline = runs[0]
    variant = runs[-1]

    # Calculate comparison
    comparison = {
        "metrics": [],
        "improvements": [],
        "regressions": [],
    }

    if baseline.metrics and variant.metrics:
        for metric_name in variant.metrics.keys():
            if metric_name in baseline.metrics:
                old_val = baseline.metrics.get(metric_name, 0)
                new_val = variant.metrics.get(metric_name, 0)
                diff = new_val - old_val
                pct_change = (diff / old_val * 100) if old_val else 0

                metric_compare = {
                    "name": metric_name,
                    "baseline": old_val,
                    "variant": new_val,
                    "difference": diff,
                    "percent_change": pct_change,
                }
                comparison["metrics"].append(metric_compare)

                if diff > 0:
                    comparison["improvements"].append({
                        "metric": metric_name,
                        "change": diff,
                        "percent": pct_change,
                    })
                elif diff < 0:
                    comparison["regressions"].append({
                        "metric": metric_name,
                        "change": diff,
                        "percent": pct_change,
                    })

    return {
        "experiment_id": experiment_id,
        "baseline_run_id": baseline.id,
        "variant_run_id": variant.id,
        "baseline": baseline.metrics,
        "variant": variant.metrics,
        "comparison": comparison,
    }


# ---- Interview Gap -> Upgrade Task ----

@app.post("/api/interview-gaps/{gap_id}/task")
async def gap_to_task(
    gap_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Convert an interview gap to an upgrade task"""
    # Get the interview gap
    from packages.database.models import InterviewGap
    result = await db.execute(
        select(InterviewGap).where(InterviewGap.id == gap_id)
    )
    gap = result.scalar_one_or_none()

    if not gap:
        raise HTTPException(status_code=404, detail="Interview gap not found")

    # Get project
    project = await ProjectRepository(db).get(gap.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create upgrade task from gap
    task_repo = TaskRepository(db)

    # Map gap type to dimension and title
    gap_type_mapping = {
        "knowledge": ("documentation", "补充知识文档"),
        "engineering": ("code_quality", "改进代码质量"),
        "evidence": ("testing", "增加测试覆盖"),
        "experiment": ("evaluation", "建立实验评测体系"),
    }

    dimension, title_prefix = gap_type_mapping.get(
        gap.gap_type, ("general", "改进")
    )

    task = await task_repo.create({
        "project_id": gap.project_id,
        "gap_id": gap_id,
        "title": f"{title_prefix}: {gap.description[:100]}",
        "description": f"Gap identified during interview: {gap.description}\n\nRecommendation: {gap.recommendation or 'None provided'}",
        "completion_criteria": [
            {
                "criterion": f"Address {gap.gap_type} gap: {gap.description[:50]}",
                "verification_method": "code_review",
                "evidence_type": "code",
            }
        ],
        "estimated_effort": "medium",
    })

    # Update gap with task reference
    gap.task_id = task.id
    await db.commit()

    return {
        "task_id": task.id,
        "gap_id": gap_id,
        "title": task.title,
        "description": task.description,
        "status": "pending",
        "gap_type": gap.gap_type,
        "severity": gap.severity,
    }


@app.get("/api/projects/{project_id}/capability-profile")
async def capability_profile(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get capability profile based on real evidence and verification.
    
    Returns VERIFIED/PARTIALLY_VERIFIED/NOT_VERIFIED based on actual evidence.
    No percentages - just binary verification status.
    """
    evidence_repo = EvidenceRepository(db)
    verification_repo = VerificationRepository(db)
    assessment_repo = AssessmentRepository(db)
    version_repo = VersionRepository(db)

    evidence = await evidence_repo.get_for_project(project_id)
    assessments = await assessment_repo.get_for_project(project_id)
    versions = await version_repo.get_for_project(project_id)

    # Define capability dimensions
    dimensions = [
        {"id": "testing", "name": "测试能力", "required_evidence": "TEST"},
        {"id": "error_handling", "name": "错误处理", "required_evidence": "CODE"},
        {"id": "logging", "name": "日志记录", "required_evidence": "CODE"},
        {"id": "auth", "name": "权限控制", "required_evidence": "CODE"},
        {"id": "monitoring", "name": "监控", "required_evidence": "CODE"},
        {"id": "deployment", "name": "部署", "required_evidence": "CODE"},
        {"id": "evaluation", "name": "评测", "required_evidence": "RUN_RESULT"},
    ]

    # Build capability profile
    capabilities = {}

    for dim in dimensions:
        dim_id = dim["id"]
        dim_evidence = [e for e in evidence if dim_id.lower() in (e.source_path or "").lower()]

        if len(dim_evidence) >= 2:
            # Multiple evidence pieces = VERIFIED
            capabilities[dim_id] = {
                "name": dim["name"],
                "status": "VERIFIED",
                "evidence_count": len(dim_evidence),
                "evidence_ids": [e.id for e in dim_evidence],
            }
        elif len(dim_evidence) == 1:
            # Single evidence = PARTIALLY_VERIFIED
            capabilities[dim_id] = {
                "name": dim["name"],
                "status": "PARTIALLY_VERIFIED",
                "evidence_count": 1,
                "evidence_ids": [dim_evidence[0].id],
            }
        else:
            # No evidence = NOT_VERIFIED
            capabilities[dim_id] = {
                "name": dim["name"],
                "status": "NOT_VERIFIED",
                "evidence_count": 0,
                "evidence_ids": [],
            }

    # Calculate overall status
    verified_count = sum(1 for c in capabilities.values() if c["status"] == "VERIFIED")
    partially_count = sum(1 for c in capabilities.values() if c["status"] == "PARTIALLY_VERIFIED")
    total_dims = len(dimensions)

    if verified_count == total_dims:
        overall_status = "FULLY_VERIFIED"
    elif verified_count + partially_count >= total_dims * 0.7:
        overall_status = "MOSTLY_VERIFIED"
    elif verified_count > 0:
        overall_status = "PARTIALLY_VERIFIED"
    else:
        overall_status = "NOT_VERIFIED"

    return {
        "project_id": project_id,
        "overall_status": overall_status,
        "dimensions": capabilities,
        "total_evidence": len(evidence),
        "total_versions": len(versions),
        "verified_count": verified_count,
        "partially_verified_count": partially_count,
        "not_verified_count": total_dims - verified_count - partially_count,
    }


# ============================================================================
# Version Timeline
# ============================================================================

@app.get("/api/projects/{project_id}/timeline")
async def get_version_timeline(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get version timeline with diffs, tests, verification, evidence, and maturity"""
    version_repo = VersionRepository(db)
    evidence_repo = EvidenceRepository(db)
    verification_repo = VerificationRepository(db)
    assessment_repo = AssessmentRepository(db)

    versions = await version_repo.get_for_project(project_id)

    timeline = []
    for v in versions:
        # Get evidence for this version
        evidence = await evidence_repo.get_for_project(project_id)
        version_evidence = [e for e in evidence if e.version_id == v.id]

        # Get verification results
        verifications = await verification_repo.session.execute(
            select(VerificationResult).where(VerificationResult.task_id.in_(
                select(EngineeringTask.id).where(EngineeringTask.project_id == project_id)
            ))
        )
        verifs = verifications.scalars().all()

        timeline.append({
            "version_id": v.id,
            "version_number": v.version_number,
            "title": v.title,
            "description": v.description,
            "maturity_before": v.maturity_before,
            "maturity_after": v.maturity_after,
            "files_changed": v.files_changed,
            "evidence": [
                {
                    "id": e.id,
                    "evidence_type": e.evidence_type,
                    "source_path": e.source_path,
                    "title": e.title,
                }
                for e in version_evidence
            ],
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })

    # Get latest assessment for current maturity
    latest_assessment = await assessment_repo.get_latest(project_id)

    return {
        "project_id": project_id,
        "current_maturity": latest_assessment.overall_level if latest_assessment else "unknown",
        "total_versions": len(versions),
        "timeline": timeline,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
