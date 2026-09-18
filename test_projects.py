"""
Test script to run the three GitHub projects through Import -> Audit -> Maturity -> Gap -> Plan
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.repo_import import RepoImportService
from services.project_auditor import ProjectAuditor
from services.upgrade_planner import UpgradePlanner


def test_project_github(project_name: str, github_url: str):
    """Test a project through the full pipeline"""
    print(f"\n{'='*60}")
    print(f"Testing: {project_name}")
    print(f"URL: {github_url}")
    print('='*60)

    try:
        # Import
        import_service = RepoImportService()
        result = import_service.import_github(github_url)

        if not result.success:
            print(f"[FAIL] Import failed: {result.error}")
            return {
                "project": project_name,
                "status": "import_failed",
                "error": result.error,
            }

        print(f"[OK] Import successful: {result.workspace_path}")

        # Audit
        auditor = ProjectAuditor()
        audit_result = auditor.audit(
            project_path=result.workspace_path,
            project_id=f"test-{project_name.lower().replace(' ', '-')}",
            github_url=github_url,
        )

        maturity = audit_result.get("maturity_assessment", {}).get("overall_level", "unknown")
        print(f"[OK] Audit complete - Maturity: {maturity}")

        facts = audit_result.get("project_facts", {})
        print(f"   - Files: {facts.get('total_files', 0)}")
        print(f"   - Code lines: {facts.get('code_lines', 0)}")
        print(f"   - Test files: {facts.get('test_files', 0)}")
        print(f"   - Frameworks: {facts.get('frameworks', [])}")

        # Get gaps
        gaps = audit_result.get("gaps", [])
        print(f"[OK] Gaps identified: {len(gaps)}")

        # Plan
        planner = UpgradePlanner()
        plan_result = planner.plan(
            project_facts={
                "main_language": facts.get("main_language", []),
                "frameworks": facts.get("frameworks", []),
                "database": facts.get("database", []),
                "project_type": facts.get("project_type", "other"),
            },
            maturity_assessment={
                "overall_level": maturity,
                "dimension_scores": {},
            },
            gaps=[g.to_dict() if hasattr(g, 'to_dict') else g for g in gaps],
            user_goals=[],
        )

        tasks = plan_result.get("recommended_tasks", [])
        print(f"[OK] Plan generated: {len(tasks)} tasks")

        return {
            "project": project_name,
            "status": "success",
            "import_path": result.workspace_path,
            "maturity": maturity,
            "files": facts.get("total_files", 0),
            "code_lines": facts.get("code_lines", 0),
            "test_files": facts.get("test_files", 0),
            "frameworks": facts.get("frameworks", []),
            "gaps": len(gaps),
            "tasks": len(tasks),
        }

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "project": project_name,
            "status": "error",
            "error": str(e),
        }


def main():
    projects = [
        ("AIEduRAG", "https://github.com/Benjamindaoson/AIEduRAG"),
        ("enterprise-data-agent", "https://github.com/Benjamindaoson/enterprise-data-agent"),
        ("SalesBoost", "https://github.com/Benjamindaoson/SalesBoost"),
    ]

    results = []
    for name, url in projects:
        result = test_project_github(name, url)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for r in results:
        status = "[OK]" if r.get("status") == "success" else "[FAIL]"
        print(f"{status} {r.get('project')}: {r.get('maturity', 'N/A')} - {r.get('files', 0)} files")

    # Save results
    import json
    with open("data/test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to data/test_results.json")


if __name__ == "__main__":
    main()
