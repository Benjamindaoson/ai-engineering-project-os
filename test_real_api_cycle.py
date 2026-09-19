"""
Proper integration test that uses the REAL database through the API.
Tests the complete AIEduRAG cycle: Import -> Audit -> Plan -> Execute -> Verify -> Evidence -> Version
"""
import asyncio
import sys
import os
import json
import tempfile
import time
import httpx
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Change to project directory for workspace isolation
os.chdir(Path(__file__).parent)

# Test configuration
API_BASE = "http://127.0.0.1:8000"
AIEDURAG_URL = "https://github.com/Benjamindaoson/AIEduRAG"


async def wait_for_api(timeout: int = 30):
    """Wait for API to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/health", timeout=5)
                if resp.status_code == 200:
                    return True
        except:
            pass
        await asyncio.sleep(1)
    return False


async def import_project(github_url: str):
    """Import a project via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/api/projects/import",
            json={"github_url": github_url},
            timeout=120
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["project_id"], data
        else:
            raise Exception(f"Import failed: {resp.status_code} - {resp.text}")


async def audit_project(project_id: str):
    """Audit a project via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/api/projects/{project_id}/audit",
            timeout=120
        )
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            raise Exception(f"Audit failed: {resp.status_code} - {resp.text}")


async def plan_upgrades(project_id: str):
    """Plan upgrades via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/api/projects/{project_id}/plan",
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            raise Exception(f"Plan failed: {resp.status_code} - {resp.text}")


async def get_tasks(project_id: str):
    """Get project tasks via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}/api/projects/{project_id}/tasks",
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("tasks", [])
        else:
            raise Exception(f"Get tasks failed: {resp.status_code}")


async def execute_task(task_id: str):
    """Execute a task via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/api/tasks/{task_id}/execute",
            timeout=120
        )
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            raise Exception(f"Execute failed: {resp.status_code} - {resp.text}")


async def verify_execution(execution_id: str):
    """Verify execution via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/api/executions/{execution_id}/verify",
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            raise Exception(f"Verify failed: {resp.status_code} - {resp.text}")


async def get_evidence(project_id: str):
    """Get project evidence via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}/api/projects/{project_id}/evidence",
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("evidence", [])
        else:
            raise Exception(f"Get evidence failed: {resp.status_code}")


async def get_versions(project_id: str):
    """Get project versions via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}/api/projects/{project_id}/versions",
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("versions", [])
        else:
            raise Exception(f"Get versions failed: {resp.status_code}")


async def get_project(project_id: str):
    """Get project details via API"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}/api/projects/{project_id}",
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"Get project failed: {resp.status_code}")


async def main():
    """Run the complete AIEduRAG cycle via real API"""
    print("="*60)
    print("AIEduRAG Complete Cycle - REAL API Test")
    print("="*60)

    # Check API is ready
    print("\n[0] Checking API...")
    if not await wait_for_api():
        print("[FAIL] API not available")
        return {"error": "API not available"}
    print("[OK] API is ready")

    try:
        # Step 1: Import
        print("\n[1] IMPORT via API")
        project_id, import_result = await import_project(AIEDURAG_URL)
        print(f"[OK] Project imported: {project_id}")

        # Step 2: Audit
        print("\n[2] AUDIT via API")
        audit_result = await audit_project(project_id)
        maturity = audit_result.get("maturity_assessment", {}).get("overall_level", "unknown")
        facts = audit_result.get("project_facts", {})
        print(f"[OK] Maturity: {maturity}")
        print(f"[OK] Files: {facts.get('total_files', 0)}")
        print(f"[OK] Code lines: {facts.get('code_lines', 0)}")

        # Step 3: Plan
        print("\n[3] PLAN via API")
        plan_result = await plan_upgrades(project_id)
        tasks_created = plan_result.get("tasks_saved", 0)
        print(f"[OK] Tasks created: {tasks_created}")

        # Step 4: Get Tasks
        print("\n[4] GET TASKS via API")
        tasks = await get_tasks(project_id)
        print(f"[OK] Tasks retrieved: {len(tasks)}")

        if not tasks:
            print("[WARN] No tasks available, creating one via Plan...")
            # The plan already created tasks, just get them again
            tasks = await get_tasks(project_id)

        if not tasks:
            print("[FAIL] No tasks to execute")
            return {"error": "No tasks"}

        task = tasks[0]
        task_id = task["id"]
        print(f"[OK] Task selected: {task_id} - {task.get('title', 'N/A')}")

        # Step 5: Execute
        print("\n[5] EXECUTE via API")
        exec_result = await execute_task(task_id)
        execution_id = exec_result.get("execution_id")
        print(f"[OK] Execution created: {execution_id}")
        print(f"[OK] Execution status: {exec_result.get('status')}")
        print(f"[OK] Changes: {exec_result.get('changes', 0)}")

        # Step 6: Verify
        print("\n[6] VERIFY via API")
        verify_result = await verify_execution(execution_id)
        verify_status = verify_result.get("overall_status")
        verification_id = verify_result.get("verification_id")
        print(f"[OK] Verification status: {verify_status}")
        print(f"[OK] Verification ID: {verification_id}")

        # Step 7: Check Evidence (created by verification on PASS)
        print("\n[7] CHECK EVIDENCE in database")
        evidence = await get_evidence(project_id)
        evidence_ids = [e["id"] for e in evidence]
        print(f"[OK] Evidence count: {len(evidence_ids)}")
        print(f"[OK] Evidence IDs: {evidence_ids}")

        # Step 8: Check Versions (created by verification on PASS)
        print("\n[8] CHECK VERSIONS in database")
        versions = await get_versions(project_id)
        version_ids = [v["id"] for v in versions]
        print(f"[OK] Version count: {len(versions)}")
        print(f"[OK] Version IDs: {version_ids}")

        # Step 9: Get updated project maturity
        print("\n[9] GET UPDATED PROJECT")
        updated_project = await get_project(project_id)
        maturity_after = updated_project.get("current_maturity")
        print(f"[OK] Maturity after: {maturity_after}")

        # Summary
        print("\n" + "="*60)
        print("FINAL RESULTS (from REAL database)")
        print("="*60)
        print(f"Project ID: {project_id}")
        print(f"Maturity before: {maturity}")
        print(f"Maturity after: {maturity_after}")
        print(f"Execution ID: {execution_id}")
        print(f"Verification ID: {verification_id}")
        print(f"Evidence IDs: {evidence_ids}")
        print(f"Version IDs: {version_ids}")

        # Save to data file
        os.makedirs("data", exist_ok=True)
        result = {
            "project_id": project_id,
            "maturity_before": maturity,
            "maturity_after": maturity_after,
            "execution_id": execution_id,
            "verification_id": verification_id,
            "evidence_ids": evidence_ids,
            "version_ids": version_ids,
            "tasks_executed": 1,
            "verification_status": verify_status,
        }
        with open("data/real_aiedurag_cycle_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n[OK] Results saved to data/real_aiedurag_cycle_result.json")

        return result

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
