from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any, Iterable


@dataclass
class EvalThresholds:
    min_task_success_rate: float = 0.80
    min_verification_pass_rate: float = 0.95
    max_false_completion_rate: float = 0.02
    max_tool_error_rate: float = 0.05
    max_context_drift: float = 0.10
    max_cost_usd: float | None = None
    max_latency_ms: float | None = None


@dataclass
class AgentEvalResult:
    task_success: bool
    verification_pass_rate: float
    false_completion: bool
    tool_error_rate: float
    retry_rate: float
    recovery_success_rate: float
    context_drift: float
    step_count: int
    tool_calls: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    metrics: dict[str, float] = field(default_factory=dict)
    gate_passed: bool | None = None
    gate_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentEvaluator:
    """Turn verification + trace evidence into agent-level reliability and cost metrics."""

    def evaluate(
        self,
        *,
        trace_summary: dict[str, Any],
        verification_statuses: Iterable[str],
        completion_claimed: bool,
        context_drift: float = 0.0,
        recovery_attempts: int = 0,
        recovery_successes: int = 0,
        thresholds: EvalThresholds | None = None,
    ) -> AgentEvalResult:
        statuses = [str(s).lower() for s in verification_statuses]
        passed = sum(1 for s in statuses if s in {"pass", "passed"})
        total = len(statuses)
        verification_pass_rate = passed / total if total else 0.0
        task_success = total > 0 and passed == total
        false_completion = bool(completion_claimed and not task_success)
        tool_calls = int(trace_summary.get("tool_calls", 0) or 0)
        tool_errors = int(trace_summary.get("tool_error_count", trace_summary.get("error_count", 0)) or 0)
        retry_count = int(trace_summary.get("retry_count", 0) or 0)
        tool_error_rate = tool_errors / tool_calls if tool_calls else 0.0
        retry_rate = retry_count / tool_calls if tool_calls else 0.0
        recovery_success_rate = recovery_successes / recovery_attempts if recovery_attempts else 0.0
        result = AgentEvalResult(
            task_success=task_success,
            verification_pass_rate=verification_pass_rate,
            false_completion=false_completion,
            tool_error_rate=tool_error_rate,
            retry_rate=retry_rate,
            recovery_success_rate=recovery_success_rate,
            context_drift=max(0.0, min(1.0, float(context_drift))),
            step_count=int(trace_summary.get("span_count", 0) or 0),
            tool_calls=tool_calls,
            total_tokens=int(trace_summary.get("total_tokens", 0) or 0),
            cost_usd=float(trace_summary.get("cost_usd", 0.0) or 0.0),
            latency_ms=float(trace_summary.get("latency_ms", 0.0) or 0.0),
        )
        result.metrics = {
            "task_success": 1.0 if result.task_success else 0.0,
            "verification_pass_rate": result.verification_pass_rate,
            "false_completion_rate": 1.0 if result.false_completion else 0.0,
            "tool_error_rate": result.tool_error_rate,
            "retry_rate": result.retry_rate,
            "recovery_success_rate": result.recovery_success_rate,
            "context_drift": result.context_drift,
        }
        if thresholds:
            self.apply_gate(result, thresholds)
        return result

    def apply_gate(self, result: AgentEvalResult, thresholds: EvalThresholds) -> AgentEvalResult:
        failures: list[str] = []
        if (1.0 if result.task_success else 0.0) < thresholds.min_task_success_rate:
            failures.append("task_success_rate")
        if result.verification_pass_rate < thresholds.min_verification_pass_rate:
            failures.append("verification_pass_rate")
        if (1.0 if result.false_completion else 0.0) > thresholds.max_false_completion_rate:
            failures.append("false_completion_rate")
        if result.tool_error_rate > thresholds.max_tool_error_rate:
            failures.append("tool_error_rate")
        if result.context_drift > thresholds.max_context_drift:
            failures.append("context_drift")
        if thresholds.max_cost_usd is not None and result.cost_usd > thresholds.max_cost_usd:
            failures.append("cost_usd")
        if thresholds.max_latency_ms is not None and result.latency_ms > thresholds.max_latency_ms:
            failures.append("latency_ms")
        result.gate_failures = failures
        result.gate_passed = not failures
        return result

    def aggregate(self, results: Iterable[AgentEvalResult]) -> dict[str, float]:
        rows = list(results)
        if not rows:
            return {}
        return {
            "task_success_rate": mean(1.0 if r.task_success else 0.0 for r in rows),
            "verification_pass_rate": mean(r.verification_pass_rate for r in rows),
            "false_completion_rate": mean(1.0 if r.false_completion else 0.0 for r in rows),
            "tool_error_rate": mean(r.tool_error_rate for r in rows),
            "retry_rate": mean(r.retry_rate for r in rows),
            "recovery_success_rate": mean(r.recovery_success_rate for r in rows),
            "context_drift": mean(r.context_drift for r in rows),
            "avg_total_tokens": mean(r.total_tokens for r in rows),
            "avg_cost_usd": mean(r.cost_usd for r in rows),
            "avg_latency_ms": mean(r.latency_ms for r in rows),
            "avg_steps": mean(r.step_count for r in rows),
        }
