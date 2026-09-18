"""
AI Engineering Project OS - API Service

FastAPI-based API for the AI Engineering Project OS.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from packages.contracts.models import (
    ProjectType, GapPriority, TaskStatus, MaturityLevel
)
from packages.maturity-model import MaturityEvaluator, MaturityLevel
from services.project-auditor import ProjectAuditor
from services.upgrade-planner import UpgradePlanner
from services.engineering-mentor import EngineeringMentor
from services.execution-runtime import ExecutionRuntime, ExecutionConfig
from services.verification-engine import VerificationEngine
from services.interview-engine import InterviewEngine


# ============================================================================
# Pydantic Models for API
# ============================================================================

class ProjectImportRequest(BaseModel):
    github_url: Optional[str] = None
    local_path: Optional[str] = None
    user_goals: Optional[List[str]] = None


class ProjectImportResponse(BaseModel):
    project_id: str
    name: str
    status: str
    message: str


class AuditResponse(BaseModel):
    project_id: str
    project_facts: Dict[str, Any]
    maturity_assessment: Dict[str, Any]
    gaps: List[Dict[str, Any]]
    raw_observations: List[Dict[str, Any]]


class UpgradePlanResponse(BaseModel):
    project_id: str
    recommended_tasks: List[Dict[str, Any]]
    prioritization_rationale: str
    immediate_next_steps: List[str]
    estimated_total_effort: str
    current_level: str
    target_level: str
    upgrade_path: List[str]


class MentorRequest(BaseModel):
    task_id: str
    project_context: Dict[str, Any]


class MentorResponse(BaseModel):
    task_id: str
    learning_content: Dict[str, Any]
    code_examples: Optional[List[Dict[str, Any]]]
    related_concepts: List[Dict[str, Any]]
    common_pitfalls: List[str]


class ExecutionResponse(BaseModel):
    execution_id: str
    task_id: str
    status: str
    changes: List[Dict[str, Any]]
    test_results: List[Dict[str, Any]]
    error: Optional[str]


class VerificationResponse(BaseModel):
    task_id: str
    verification_results: List[Dict[str, Any]]
    overall_status: str
    missing_evidence: List[Dict[str, str]]
    recommendations: List[str]


class InterviewRequest(BaseModel):
    project_id: str
    execution_record_ids: Optional[List[str]] = None


class InterviewResponse(BaseModel):
    session_id: str
    project_id: str
    initial_questions: List[Dict[str, Any]]
    gap_analysis: List[Dict[str, Any]]


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AI Engineering Project OS",
    description="Upgrade AI projects from idea to production",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
projects_db: Dict[str, Dict[str, Any]] = {}
audits_db: Dict[str, Dict[str, Any]] = {}
tasks_db: Dict[str, Dict[str, Any]] = {}
executions_db: Dict[str, Dict[str, Any]] = {}
sessions_db: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def get_project_dir(project_id: str) -> Optional[str]:
    """Get project directory from database"""
    if project_id in projects_db:
        return projects_db[project_id].get("local_path")
    return None


def save_project_state(project_id: str, state: Dict[str, Any]):
    """Save project state"""
    if project_id in projects_db:
        projects_db[project_id].update(state)


# ============================================================================
# API Endpoints - Project Management
# ============================================================================

@app.post("/api/projects/import", response_model=ProjectImportResponse)
async def import_project(request: ProjectImportRequest):
    """Import a project from GitHub or local path"""
    project_id = str(uuid.uuid4())
    
    # Validate input
    if not request.github_url and not request.local_path:
        raise HTTPException(status_code=400, detail="Either github_url or local_path must be provided")
    
    # Determine project path
    if request.local_path:
        project_path = request.local_path
    else:
        # Clone from GitHub (simplified - would need git clone in real implementation)
        raise HTTPException(status_code=501, detail="GitHub import not yet implemented")
    
    if not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail=f"Project path not found: {project_path}")
    
    # Get project name
    project_name = Path(project_path).name
    
    # Save project
    projects_db[project_id] = {
        "id": project_id,
        "name": project_name,
        "github_url": request.github_url,
        "local_path": project_path,
        "user_goals": request.user_goals or [],
        "created_at": datetime.now().isoformat(),
    }
    
    return ProjectImportResponse(
        project_id=project_id,
        name=project_name,
        status="imported",
        message=f"Project '{project_name}' imported successfully",
    )


@app.get("/api/projects")
async def list_projects():
    """List all imported projects"""
    return {
        "projects": [
            {
                "id": p["id"],
                "name": p["name"],
                "github_url": p.get("github_url"),
                "created_at": p["created_at"],
            }
            for p in projects_db.values()
        ]
    }


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]


# ============================================================================
# API Endpoints - Project Audit
# ============================================================================

@app.post("/api/projects/{project_id}/audit", response_model=AuditResponse)
async def audit_project(project_id: str, background_tasks: BackgroundTasks):
    """Audit a project and assess its maturity"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    project_path = project.get("local_path")
    
    if not project_path or not os.path.exists(project_path):
        raise HTTPException(status_code=400, detail="Project path not available")
    
    # Run auditor
    auditor = ProjectAuditor()
    result = auditor.audit(
        project_path=project_path,
        project_id=project_id,
        github_url=project.get("github_url"),
        user_goals=project.get("user_goals"),
    )
    
    # Save audit
    audits_db[project_id] = result
    save_project_state(project_id, {"last_audit": result})
    
    return AuditResponse(
        project_id=project_id,
        project_facts=result["project_facts"],
        maturity_assessment=result["maturity_assessment"],
        gaps=result["gaps"],
        raw_observations=result["raw_observations"],
    )


@app.get("/api/projects/{project_id}/audit")
async def get_project_audit(project_id: str):
    """Get the latest audit for a project"""
    if project_id not in audits_db:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audits_db[project_id]


# ============================================================================
# API Endpoints - Upgrade Planning
# ============================================================================

@app.post("/api/projects/{project_id}/plan", response_model=UpgradePlanResponse)
async def plan_upgrades(project_id: str):
    """Generate upgrade plan for a project"""
    if project_id not in audits_db:
        raise HTTPException(status_code=400, detail="Project must be audited first")
    
    audit = audits_db[project_id]
    project = projects_db.get(project_id, {})
    
    # Run planner
    planner = UpgradePlanner()
    result = planner.plan(
        project_facts=audit["project_facts"],
        maturity_assessment=audit["maturity_assessment"],
        gaps=audit["gaps"],
        user_goals=project.get("user_goals", []),
    )
    
    # Save tasks
    for task_dict in result["recommended_tasks"]:
        task_id = task_dict["id"]
        tasks_db[task_id] = task_dict
    
    return UpgradePlanResponse(
        project_id=project_id,
        recommended_tasks=result["recommended_tasks"],
        prioritization_rationale=result["prioritization_rationale"],
        immediate_next_steps=result["immediate_next_steps"],
        estimated_total_effort=result["estimated_total_effort"],
        current_level=result["current_level"],
        target_level=result["target_level"],
        upgrade_path=result["upgrade_path"],
    )


# ============================================================================
# API Endpoints - Engineering Mentor
# ============================================================================

@app.post("/api/tasks/{task_id}/mentor", response_model=MentorResponse)
async def get_mentor_guidance(task_id: str):
    """Get mentoring for a specific task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_dict = tasks_db[task_id]
    
    # Create task object
    from packages.contracts.models import UpgradeTask, LearningContent, CompletionCriterion
    
    task = UpgradeTask(
        id=task_dict["id"],
        project_id=task_dict["project_id"],
        gap_id=task_dict["gap_id"],
        title=task_dict["title"],
        description=task_dict["description"],
        learning_content=LearningContent(**task_dict.get("learning_content", {})),
        completion_criteria=[
            CompletionCriterion(**c) for c in task_dict.get("completion_criteria", [])
        ],
        estimated_effort=task_dict.get("estimated_effort", ""),
        prerequisites=task_dict.get("prerequisites", []),
        status=TaskStatus(task_dict.get("status", "pending")),
    )
    
    # Run mentor
    mentor = EngineeringMentor()
    result = mentor.mentor(
        task=task,
        project_context={"tech_stack": []},  # Would get from project facts
    )
    
    return MentorResponse(
        task_id=task_id,
        learning_content=result.learning_content.to_dict(),
        code_examples=result.code_examples,
        related_concepts=result.related_concepts,
        common_pitfalls=result.common_pitfalls,
    )


# ============================================================================
# API Endpoints - Execution
# ============================================================================

@app.post("/api/tasks/{task_id}/execute", response_model=ExecutionResponse)
async def execute_task(task_id: str, background_tasks: BackgroundTasks):
    """Execute a task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_dict = tasks_db[task_id]
    project_id = task_dict["project_id"]
    
    if project_id not in projects_db:
        raise HTTPException(status_code=400, detail="Project not found")
    
    project = projects_db[project_id]
    project_path = project.get("local_path")
    
    if not project_path:
        raise HTTPException(status_code=400, detail="Project path not available")
    
    # Create task object
    from packages.contracts.models import UpgradeTask, LearningContent, CompletionCriterion
    
    task = UpgradeTask(
        id=task_dict["id"],
        project_id=task_dict["project_id"],
        gap_id=task_dict["gap_id"],
        title=task_dict["title"],
        description=task_dict["description"],
        learning_content=LearningContent(**task_dict.get("learning_content", {})),
        completion_criteria=[
            CompletionCriterion(**c) for c in task_dict.get("completion_criteria", [])
        ],
        estimated_effort=task_dict.get("estimated_effort", ""),
        prerequisites=task_dict.get("prerequisites", []),
        status=TaskStatus.IN_PROGRESS,
    )
    
    # Execute
    runtime = ExecutionRuntime(ExecutionConfig(save_baseline=True, run_tests=True))
    record = runtime.execute(task, project_path)
    
    # Save execution
    executions_db[record.id] = record.to_dict()
    task_dict["status"] = record.status.value
    tasks_db[task_id] = task_dict
    
    return ExecutionResponse(
        execution_id=record.id,
        task_id=task_id,
        status=record.status.value,
        changes=[{"file_path": c.file_path, "change_type": c.change_type, "purpose": c.purpose} 
                 for c in record.changes],
        test_results=[{"test_name": t.test_name, "passed": t.passed, "error": t.error}
                      for t in record.test_results],
        error=record.error,
    )


# ============================================================================
# API Endpoints - Verification
# ============================================================================

@app.post("/api/executions/{execution_id}/verify", response_model=VerificationResponse)
async def verify_execution(execution_id: str):
    """Verify task execution"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    exec_dict = executions_db[execution_id]
    task_id = exec_dict["task_id"]
    
    if task_id not in tasks_db:
        raise HTTPException(status_code=400, detail="Task not found")
    
    task_dict = tasks_db[task_id]
    project_id = task_dict["project_id"]
    
    # Get project path
    if project_id not in projects_db:
        raise HTTPException(status_code=400, detail="Project not found")
    
    project = projects_db[project_id]
    project_path = project.get("local_path")
    
    # Reconstruct objects
    from packages.contracts.models import UpgradeTask, ExecutionRecord, LearningContent, CompletionCriterion, CodeChange, TestResult
    
    task = UpgradeTask(
        id=task_dict["id"],
        project_id=task_dict["project_id"],
        gap_id=task_dict["gap_id"],
        title=task_dict["title"],
        description=task_dict["description"],
        learning_content=LearningContent(**task_dict.get("learning_content", {})),
        completion_criteria=[
            CompletionCriterion(**c) for c in task_dict.get("completion_criteria", [])
        ],
        estimated_effort=task_dict.get("estimated_effort", ""),
        prerequisites=task_dict.get("prerequisites", []),
        status=TaskStatus(exec_dict.get("status", "pending")),
    )
    
    record = ExecutionRecord(
        id=exec_dict["id"],
        task_id=exec_dict["task_id"],
        project_id=exec_dict["project_id"],
        changes=[CodeChange(**c) for c in exec_dict.get("changes", [])],
        execution_log=exec_dict.get("execution_log", ""),
        test_results=[TestResult(**t) for t in exec_dict.get("test_results", [])],
        status=TaskStatus(exec_dict.get("status", "pending")),
    )
    
    # Verify
    verifier = VerificationEngine()
    result = verifier.verify(task, record, project_path)
    
    return VerificationResponse(
        task_id=task_id,
        verification_results=[
            {"criterion": r.criterion, "status": r.status, "evidence": r.evidence, "details": r.details}
            for r in result.verification_results
        ],
        overall_status=result.overall_status,
        missing_evidence=result.missing_evidence,
        recommendations=result.recommendations,
    )


# ============================================================================
# API Endpoints - Interview
# ============================================================================

@app.post("/api/projects/{project_id}/interview", response_model=InterviewResponse)
async def start_interview(project_id: str, request: InterviewRequest):
    """Start an interview session for a project"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project data
    project = projects_db[project_id]
    audit = audits_db.get(project_id, {})
    
    # Get execution records
    records = []
    if request.execution_record_ids:
        for exec_id in request.execution_record_ids:
            if exec_id in executions_db:
                records.append(executions_db[exec_id])
    
    # Run interview engine
    engine = InterviewEngine()
    result = engine.conduct_interview(
        project_facts=audit.get("project_facts", {}),
        execution_records=records,
        architecture_decisions=[],  # Would come from project data
        maturity_assessment=audit.get("maturity_assessment", {}),
        project_id=project_id,
    )
    
    # Save session
    sessions_db[result.session.id] = result.to_dict()
    
    return InterviewResponse(
        session_id=result.session.id,
        project_id=project_id,
        initial_questions=[q.to_dict() for q in result.initial_questions],
        gap_analysis=[
            {
                "gap_type": g.gap_type,
                "description": g.description,
                "related_task_id": g.related_task_id,
                "severity": g.severity,
            }
            for g in result.gap_analysis
        ],
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "projects": len(projects_db),
        "audits": len(audits_db),
        "tasks": len(tasks_db),
        "executions": len(executions_db),
        "sessions": len(sessions_db),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
