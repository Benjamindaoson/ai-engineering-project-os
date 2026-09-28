from pathlib import Path

from services.project_lab_assessment import ProjectLabAssessmentService, ProjectLabCriterion


def test_project_lab_assessment_is_read_only_and_runs_project_tests(tmp_path: Path):
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "def test_sample():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))

    result = ProjectLabAssessmentService().assess(
        project_id="project-1",
        project_path=str(tmp_path),
        skill_ids=["rag.hybrid-retrieval"],
        criteria=[
            ProjectLabCriterion(
                criterion="Project tests are discoverable",
                evidence_type="test",
                verification_method="pytest_collection",
            )
        ],
    )

    after = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))

    assert result["read_only"] is True
    assert result["repository_mutated"] is False
    assert result["verification"]["overall_status"] == "passed"
    assert result["summary"]["pass_rate"] == 1.0

    # Ignore pytest's own cache artifacts; Project Lab itself must not create learner code.
    before_source = [item for item in before if ".pytest_cache" not in item and "__pycache__" not in item]
    after_source = [item for item in after if ".pytest_cache" not in item and "__pycache__" not in item]
    assert before_source == after_source


def test_project_lab_supports_non_test_verification_without_execution(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    result = ProjectLabAssessmentService().assess(
        project_id="project-2",
        project_path=str(tmp_path),
        skill_ids=["agent.evaluation"],
        criteria=[
            ProjectLabCriterion(
                criterion="Project contains configuration",
                evidence_type="config",
                verification_method="config_presence",
            )
        ],
    )

    assert result["verification"]["overall_status"] == "passed"
    assert result["summary"]["passed"] == 1
