from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class HarnessVariant:
    name: str
    verification: bool = True
    persistent_state: bool = True
    context_compression: bool = True
    recovery: bool = True
    sandbox: bool = True
    hitl: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AblationRun:
    variant: HarnessVariant
    metrics: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"variant": self.variant.to_dict(), "metrics": self.metrics, "metadata": self.metadata}


class AblationRunner:
    """Controlled harness ablations with explicit metric directionality."""

    HIGHER_IS_BETTER = {"task_success_rate", "verification_pass_rate", "recovery_success_rate", "context_retention_rate"}
    LOWER_IS_BETTER = {"false_completion_rate", "tool_error_rate", "context_drift", "avg_total_tokens", "avg_cost_usd", "avg_latency_ms", "avg_steps"}

    def run(self, variants: Iterable[HarnessVariant], run_fn: Callable[[HarnessVariant], dict[str, float]]) -> list[AblationRun]:
        return [AblationRun(variant=v, metrics=dict(run_fn(v))) for v in variants]

    def compare(self, baseline: AblationRun, variant: AblationRun) -> dict[str, Any]:
        metrics: list[dict[str, Any]] = []
        keys = sorted(set(baseline.metrics) & set(variant.metrics))
        for key in keys:
            before = float(baseline.metrics[key])
            after = float(variant.metrics[key])
            delta = after - before
            if key in self.HIGHER_IS_BETTER:
                improved = delta > 0
            elif key in self.LOWER_IS_BETTER:
                improved = delta < 0
            else:
                improved = None
            metrics.append({"metric": key, "baseline": before, "variant": after, "delta": delta, "improved": improved})
        return {"baseline": baseline.variant.name, "variant": variant.variant.name, "metrics": metrics}

    @staticmethod
    def canonical_variants() -> list[HarnessVariant]:
        full = HarnessVariant("full_harness")
        return [
            full,
            HarnessVariant("no_verification", verification=False),
            HarnessVariant("no_persistent_state", persistent_state=False),
            HarnessVariant("no_context_compression", context_compression=False),
            HarnessVariant("no_recovery", recovery=False),
            HarnessVariant("no_sandbox_hitl", sandbox=False, hitl=False),
        ]
