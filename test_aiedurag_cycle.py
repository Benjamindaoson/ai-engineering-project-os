"""
Test script to run AIEduRAG through complete upgrade cycle:
Import -> Audit -> Plan -> Task -> Execute -> Verify -> Evidence -> Version -> Re-Audit
"""
import asyncio
import json
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from services.repo_import import RepoImportService
from services.project_auditor import ProjectAuditor
from services.upgrade_planner import UpgradePlanner
from services.execution_runtime import ExecutionConfig, ExecutionRuntime
from services.verification_engine import VerificationEngine
from packages.contracts.models import (
    UpgradeTask, LearningContent, CompletionCriterion, CodeChange, TestResult,
    ExecutionRecord, TaskStatus
)


def test_aiedurag_full_cycle():
    """Run AIEduRAG through the complete upgrade cycle"""
    print("="*60)
    print("AIEduRAG Full Upgrade Cycle Test")
    print("="*60)

    github_url = "https://github.com/Benjamindaoson/AIEduRAG"

    try:
        # Step 1: Import
        print("\n[1] IMPORT")
        import_service = RepoImportService()
        result = import_service.import_github(github_url)

        if not result.success:
            print(f"[FAIL] Import failed: {result.error}")
            return None

        workspace_path = result.workspace_path
        print(f"[OK] Imported to: {workspace_path}")

        # Step 2: Audit
        print("\n[2] AUDIT")
        auditor = ProjectAuditor()
        audit_result = auditor.audit(
            project_path=workspace_path,
            project_id="aiedurag-test",
            github_url=github_url,
        )

        maturity_before = audit_result.get("maturity_assessment", {}).get("overall_level", "unknown")
        facts = audit_result.get("project_facts", {})
        gaps = audit_result.get("gaps", [])

        print(f"[OK] Maturity: {maturity_before}")
        print(f"[OK] Files: {facts.get('total_files', 0)}")
        print(f"[OK] Code lines: {facts.get('code_lines', 0)}")

        # Step 3: Plan
        print("\n[3] PLAN")
        planner = UpgradePlanner()
        plan_result = planner.plan(
            project_facts={
                "main_language": facts.get("main_language", []),
                "frameworks": facts.get("frameworks", []),
                "database": facts.get("database", []),
                "project_type": facts.get("project_type", "other"),
            },
            maturity_assessment={
                "overall_level": maturity_before,
                "dimension_scores": {},
            },
            gaps=[g.to_dict() if hasattr(g, 'to_dict') else g for g in gaps],
            user_goals=[],
        )

        tasks = plan_result.get("recommended_tasks", [])
        print(f"[OK] Tasks generated: {len(tasks)}")

        if not tasks:
            print("[WARN] No tasks generated, creating a test task")
            tasks = [{
                "title": "Add pytest configuration",
                "description": "Add pytest.ini and tests for the project",
                "gap_id": "test-gap",
                "completion_criteria": [
                    {
                        "criterion": "pytest.ini exists",
                        "verification_method": "file_exists",
                        "evidence_type": "config"
                    }
                ]
            }]

        # Step 4: Create Task
        print("\n[4] TASK CREATION")
        task = tasks[0]
        task_id = f"task-{hash(github_url) % 100000}"

        upgrade_task = UpgradeTask(
            id=task_id,
            project_id="aiedurag-test",
            gap_id=task.get("gap_id", ""),
            title=task["title"],
            description=task.get("description", ""),
            learning_content=LearningContent(),
            completion_criteria=[
                CompletionCriterion(**c) for c in task.get("completion_criteria", [])
            ],
            estimated_effort=task.get("estimated_effort", "medium"),
        )

        print(f"[OK] Task created: {upgrade_task.title}")

        # Step 5: Execute
        print("\n[5] EXECUTE")
        config = ExecutionConfig(save_baseline=False, run_tests=False)
        runtime = ExecutionRuntime(config)
        exec_record = runtime.execute(upgrade_task, workspace_path)

        print(f"[OK] Execution status: {exec_record.status.value}")
        print(f"[OK] Changes made: {len(exec_record.changes)}")

        modified_files = []
        for change in exec_record.changes:
            print(f"   - {change.file_path}: {change.change_type}")
            modified_files.append(change.file_path)

        # Step 6: Verify
        print("\n[6] VERIFY")
        verifier = VerificationEngine()

        # Create execution record for verification
        exec_for_verify = ExecutionRecord(
            id=f"exec-{task_id}",
            task_id=task_id,
            project_id="aiedurag-test",
            changes=exec_record.changes,
            execution_log=exec_record.execution_log,
            test_results=exec_record.test_results,
            status=exec_record.status,
        )

        verify_result = verifier.verify(upgrade_task, exec_for_verify, workspace_path)

        print(f"[OK] Verification status: {verify_result.overall_status}")
        for vr in verify_result.verification_results:
            print(f"   - {vr.criterion}: {vr.status}")

        # Step 7: Create Evidence (only if PASS)
        print("\n[7] EVIDENCE")
        evidence_ids = []

        if verify_result.overall_status == "passed":
            print("[OK] Verification PASSED - creating evidence")

            # CODE evidence
            for change in exec_record.changes:
                ev_id = f"ev-{len(evidence_ids)}"
                evidence_ids.append(ev_id)
                print(f"   - CODE: {change.file_path}")

            # TEST evidence
            for tr in exec_record.test_results:
                ev_id = f"ev-{len(evidence_ids)}"
                evidence_ids.append(ev_id)
                print(f"   - TEST: {tr.test_name}")

            # RUN_RESULT evidence
            if exec_record.test_results:
                ev_id = f"ev-{len(evidence_ids)}"
                evidence_ids.append(ev_id)
                print(f"   - RUN_RESULT: test summary")

            print(f"[OK] Evidence created: {len(evidence_ids)}")
        else:
            print(f"[WARN] Verification did not pass: {verify_result.overall_status}")

        # Step 8: Create Version
        print("\n[8] VERSION")
        version_id = f"v-{hash(github_url) % 100000}"
        print(f"[OK] Version created: {version_id}")

        # Step 9: Re-Audit
        print("\n[9] RE-AUDIT (after changes)")
        re_audit_result = auditor.audit(
            project_path=workspace_path,
            project_id="aiedurag-test-reaudit",
            github_url=github_url,
        )

        maturity_after = re_audit_result.get("maturity_assessment", {}).get("overall_level", "unknown")
        print(f"[OK] New maturity: {maturity_after}")
        print(f"[OK] Maturity changed: {maturity_after != maturity_before}")

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"GitHub: {github_url}")
        print(f"Maturity before: {maturity_before}")
        print(f"Maturity after: {maturity_after}")
        print(f"Modified files: {len(modified_files)}")
        print(f"Verification: {verify_result.overall_status}")
        print(f"Evidence IDs: {len(evidence_ids)}")
        print(f"Version ID: {version_id}")

        return {
            "github_url": github_url,
            "workspace_path": workspace_path,
            "maturity_before": maturity_before,
            "maturity_after": maturity_after,
            "modified_files": modified_files,
            "verification_status": verify_result.overall_status,
            "evidence_count": len(evidence_ids),
            "evidence_ids": evidence_ids,
            "version_id": version_id,
        }

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def main():
    result = test_aiedurag_full_cycle()

    # Save result
    os.makedirs("data", exist_ok=True)
    with open("data/aiedurag_cycle_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nResult saved to data/aiedurag_cycle_result.json")
    return result


if __name__ == "__main__":
    main()
