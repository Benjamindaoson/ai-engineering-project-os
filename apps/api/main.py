"""
AI Engineering Project OS - API Service

FastAPI-based API with real database persistence and services.
"""

import os
import json
import uuid
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.database import (
    init_db, get_session, async_session,
    ProjectRepository, SnapshotRepository, FactRepository,
    AssessmentRepository, GapRepository, TaskRepository,
    ExecutionRepository, VerificationRepository,
    EvidenceRepository, VersionRepository, InterviewRepository,
)
from packages.contracts.models import TaskStatus
from services.project_auditor import ProjectAuditor
from services.upgrade_planner import UpgradePlanner
from services.engineering_mentor import EngineeringMentor
from services.execution_runtime import ExecutionRuntime, ExecutionConfig
from services.verification_engine import VerificationEngine
from services.interview_engine import InterviewEngine
from services.repo_import import RepoImportService


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
    github_url: Optional[str] = None
    local_path: Optional[str] = None
    user_goals: Optional[List[str]] = None


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


@app.get("/test/planner")
async def test_planner():
    """Test the planner directly"""
    try:
        result = planner.plan(
            project_facts={
                "main_language": ["Python"],
                "frameworks": ["FastAPI"],
                "database": ["SQLite"],
                "project_type": "rag",
            },
            maturity_assessment={
                "overall_level": "idea",
                "dimension_scores": {},
            },
            gaps=[
                {"id": "1", "project_id": "test", "dimension": "testing", "description": "No tests", "current_state": "None", "target_state": "Tests exist", "priority": "critical"},
            ],
            user_goals=[],
        )
        return {"success": True, "tasks": len(result.get("recommended_tasks", []))}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


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
    from packages.contracts.models import UpgradeTask as UpgradeTaskModel, LearningContent, CompletionCriterion
    
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
    from packages.contracts.models import UpgradeTask as UpgradeTaskModel, LearningContent, CompletionCriterion
    
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
    """Verify execution"""
    exec_repo = ExecutionRepository(db)
    task_repo = TaskRepository(db)
    verification_repo = VerificationRepository(db)
    
    execution = await exec_repo.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    task = await task_repo.get(execution.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Reconstruct objects
    from packages.contracts.models import (
        UpgradeTask as UpgradeTaskModel, ExecutionRecord as ExecutionRecordModel,
        LearningContent, CompletionCriterion, CodeChange, TestResult,
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
    
    return result.to_dict()


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

    # Save the answer
    answer = await interview_repo.create_answer({
        "session_id": session_id,
        "question_id": answer_data.question_id,
        "answer": answer_data.answer,
    })

    # Generate follow-up if any
    engine = InterviewEngine()
    follow_up = engine.generate_follow_up(
        question_id=answer_data.question_id,
        user_answer=answer_data.answer,
        session_id=session_id,
    )

    result = {
        "answer_id": answer.id,
        "submitted": True,
    }

    if follow_up:
        # Save follow-up question
        new_q = await interview_repo.create_question({
            "session_id": session_id,
            "question": follow_up.question,
            "context": follow_up.context,
            "follow_ups": follow_up.follow_ups,
            "gap_type": follow_up.gap_type,
            "parent_question_id": answer_data.question_id,
        })
        result["next_question"] = new_q.to_dict()

    return result


@app.get("/api/interviews/{session_id}/gaps")
async def get_interview_gaps(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get gaps identified during interview"""
    interview_repo = InterviewRepository(db)

    gaps = await interview_repo.get_session_gaps(session_id)

    return {
        "gaps": [
            {
                "gap_type": g.gap_type,
                "description": g.description,
                "severity": g.severity,
            }
            for g in gaps
        ]
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
