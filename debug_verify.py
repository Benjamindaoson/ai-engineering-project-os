"""Debug script to test verification directly"""
import sys

sys.path.insert(0, '.')

import asyncio
import json
import os

from packages.contracts.models import (
    CodeChange,
    CompletionCriterion,
    LearningContent,
    TaskStatus,
    TestResult,
)
from packages.contracts.models import ExecutionRecord as ExecutionRecordModel
from packages.contracts.models import UpgradeTask as UpgradeTaskModel
from packages.database import async_session, init_db
from packages.database.repositories import (
    ExecutionRepository,
    TaskRepository,
)
from services.verification_engine import VerificationEngine


async def test_verify():
    await init_db()
    
    execution_id = '53b22403-4666-4cce-b532-6e7209b8fdc5'
    
    async with async_session() as session:
        exec_repo = ExecutionRepository(session)
        task_repo = TaskRepository(session)
        
        execution = await exec_repo.get(execution_id)
        print(f"Execution: {execution}")
        print(f"  task_id: {execution.task_id}")
        print(f"  project_id: {execution.project_id}")
        print(f"  changes: {execution.changes}")
        print(f"  test_results: {execution.test_results}")
        
        task = await task_repo.get(execution.task_id)
        print(f"\nTask: {task}")
        print(f"  title: {task.title}")
        print(f"  learning_content: {task.learning_content}")
        print(f"  completion_criteria: {task.completion_criteria}")
        print(f"  gap_id: {task.gap_id}")
        
        # Try to reconstruct objects
        try:
            lc_data = task.learning_content
            if isinstance(lc_data, str):
                lc_data = json.loads(lc_data)
            lc = LearningContent(**lc_data) if lc_data else LearningContent()
            print(f"\nLearningContent: {lc}")
        except Exception as e:
            print(f"\nError creating LearningContent: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            cc_list = task.completion_criteria or []
            if cc_list and isinstance(cc_list[0], str):
                cc_list = [json.loads(c) for c in cc_list]
            criteria = [CompletionCriterion(**c) for c in cc_list]
            print(f"CompletionCriteria: {criteria}")
        except Exception as e:
            print(f"Error creating CompletionCriteria: {e}")
            import traceback
            traceback.print_exc()
        
        # Try verification
        try:
            verifier = VerificationEngine()
            
            # Reconstruct upgrade task
            upgrade_task = UpgradeTaskModel(
                id=task.id,
                project_id=task.project_id,
                gap_id=task.gap_id or "",
                title=task.title,
                description=task.description,
                learning_content=lc,
                completion_criteria=criteria,
            )
            
            # Reconstruct execution record
            changes = [CodeChange(**c) for c in (execution.changes or [])]
            test_results = [TestResult(**t) for t in (execution.test_results or [])]
            
            exec_record = ExecutionRecordModel(
                id=execution.id,
                task_id=execution.task_id,
                project_id=execution.project_id,
                changes=changes,
                execution_log=execution.execution_log or "",
                test_results=test_results,
                status=TaskStatus(execution.status),
            )
            
            print(f"\nUpgradeTask: {upgrade_task}")
            print(f"ExecutionRecord: {exec_record}")
            
            # Get workspace path
            from packages.database import ProjectRepository
            project_repo = ProjectRepository(session)
            project = await project_repo.get(execution.project_id)
            workspace_path = project.local_path if project else ""
            print(f"\nWorkspace path: {workspace_path}")
            print(f"Workspace exists: {os.path.exists(workspace_path)}")
            
            # Verify
            result = verifier.verify(upgrade_task, exec_record, workspace_path)
            print(f"\nVerification result: {result}")
            print(f"  overall_status: {result.overall_status}")
            print(f"  verification_results: {result.verification_results}")
            
        except Exception as e:
            print(f"\nError during verification: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test_verify())
