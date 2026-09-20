from datetime import datetime, timedelta, timezone

from packages.agent_harness import (
    AblationRun,
    AblationRunner,
    AgentEvaluator,
    ApprovalStore,
    ContextDriftEvaluator,
    ContextItem,
    ContextManager,
    ContextPolicy,
    FailureClassifier,
    HarnessVariant,
    RecoveryAction,
    RecoveryPolicy,
    RiskLevel,
    SandboxPolicy,
    TraceStore,
)


def test_trace_store_collects_runtime_metrics(tmp_path):
    store = TraceStore(str(tmp_path / "trace.jsonl"))
    trace_id = store.new_trace_id()
    with store.span("execution", trace_id=trace_id) as root:
        with store.span("pytest", kind="tool", trace_id=trace_id, parent_span_id=root.span_id):
            pass
    summary = store.summary(trace_id)
    assert summary["span_count"] == 2
    assert summary["tool_calls"] == 1
    assert summary["error_count"] == 0
    assert (tmp_path / "trace.jsonl").exists()


def test_eval_detects_false_completion():
    evaluator = AgentEvaluator()
    result = evaluator.evaluate(
        trace_summary={"span_count": 4, "tool_calls": 2, "error_count": 1, "total_tokens": 100},
        verification_statuses=["passed", "failed"],
        completion_claimed=True,
    )
    assert result.false_completion is True
    assert result.verification_pass_rate == 0.5
    assert result.tool_error_rate == 0.5


def test_context_budget_and_drift():
    policy = ContextPolicy(max_tokens=80, reserve_tokens=10, max_item_tokens=20)
    manager = ContextManager(policy)
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    items = [
        ContextItem("goal", "keep regression tests passing", pinned=True, priority=1.0),
        ContextItem("huge", "x" * 500, priority=0.6),
        ContextItem("stale", "old package version", created_at=old, stale_after_seconds=60),
    ]
    pack = manager.build(items, "regression tests")
    assert pack.token_estimate <= policy.usable_tokens + 20
    assert "goal" in [i.key for i in pack.items]
    drift = ContextDriftEvaluator().evaluate({"goal": "regression tests"}, pack.render())
    assert drift["drift_score"] == 0.0
    assert pack.stale_ratio > 0


def test_failure_taxonomy_and_recovery_policy():
    classifier = FailureClassifier()
    signal = classifier.classify(message="pytest failed", return_code=1, phase="test")
    decision = RecoveryPolicy().decide(signal, attempt=0, max_retries=1)
    assert decision.action == RecoveryAction.REPLAN


def test_sandbox_blocks_escape_and_network(tmp_path):
    policy = SandboxPolicy(workspace_root=str(tmp_path))
    assert policy.authorize_command(["pytest", "-q"], str(tmp_path)).allowed
    blocked = policy.authorize_command(["curl", "https://example.com"], str(tmp_path))
    assert not blocked.allowed
    escaped = policy.authorize_file(str(tmp_path.parent / "secret.txt"), "read")
    assert not escaped.allowed


def test_hitl_store():
    store = ApprovalStore()
    req = store.request("git push", "external side effect", RiskLevel.HIGH, {"branch": "main"})
    assert req.status == "pending"
    assert len(store.pending()) == 1
    decided = store.decide(req.id, True, actor="reviewer")
    assert decided.status == "approved"


def test_ablation_directionality():
    runner = AblationRunner()
    baseline = AblationRun(HarnessVariant("full"), {"task_success_rate": 0.9, "false_completion_rate": 0.01})
    variant = AblationRun(HarnessVariant("no_verify", verification=False), {"task_success_rate": 0.7, "false_completion_rate": 0.2})
    report = runner.compare(baseline, variant)
    by_name = {m["metric"]: m for m in report["metrics"]}
    assert by_name["task_success_rate"]["improved"] is False
    assert by_name["false_completion_rate"]["improved"] is False
