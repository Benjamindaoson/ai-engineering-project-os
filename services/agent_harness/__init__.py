from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from packages.agent_harness import (
    AgentEvaluator,
    ApprovalStore,
    ContextDriftEvaluator,
    ContextItem,
    ContextManager,
    ContextPolicy,
    EvalThresholds,
    FailureClassifier,
    RecoveryPolicy,
    RiskLevel,
    SandboxPolicy,
    TraceStore,
)


@dataclass
class HarnessConfig:
    enable_tracing: bool = True
    enable_context_management: bool = True
    enable_recovery: bool = True
    enable_sandbox: bool = True
    enable_hitl: bool = True
    trace_jsonl_path: str | None = "./data/traces/agent_harness.jsonl"
    max_context_tokens: int = 8000
    reserve_context_tokens: int = 1200
    allow_context_compression: bool = True
    max_retries: int = 1
    allow_network: bool = False
    max_changed_files: int = 50


@dataclass
class HarnessSession:
    trace_id: str
    project_id: str
    task_id: str
    workspace: str
    trace_store: TraceStore
    sandbox_policy: SandboxPolicy
    approval_store: ApprovalStore
    failure_classifier: FailureClassifier
    recovery_policy: RecoveryPolicy
    evaluator: AgentEvaluator
    context_manager: ContextManager
    context_drift_evaluator: ContextDriftEvaluator
    recovery_attempts: int = 0
    recovery_successes: int = 0
    failure_events: list[dict[str, Any]] = field(default_factory=list)
    approval_requests: list[dict[str, Any]] = field(default_factory=list)
    context_metrics: dict[str, Any] = field(default_factory=dict)

    def record_failure(
        self,
        *,
        message: str,
        phase: str,
        return_code: int | None = None,
        timed_out: bool = False,
        attempt: int = 0,
        max_retries: int = 1,
        irreversible: bool = False,
    ) -> dict[str, Any]:
        signal = self.failure_classifier.classify(
            message=message,
            return_code=return_code,
            timed_out=timed_out,
            phase=phase,
        )
        decision = self.recovery_policy.decide(
            signal,
            attempt=attempt,
            max_retries=max_retries,
            has_baseline=True,
            irreversible=irreversible,
        )
        self.recovery_attempts += 1
        event = {
            "failure_type": signal.failure_type.value,
            "message": signal.message,
            "phase": phase,
            "return_code": return_code,
            "retryable": signal.retryable,
            "recovery_action": decision.action.value,
            "requires_approval": decision.requires_approval,
            "resolved": False,
        }
        self.failure_events.append(event)
        return event

    def request_approval(self, action: str, reason: str, risk: RiskLevel, payload: dict[str, Any]) -> dict[str, Any]:
        req = self.approval_store.request(action, reason, risk, payload)
        data = asdict(req)
        self.approval_requests.append(data)
        return data

    def build_context(self, items: list[ContextItem], objective: str, required_facts: dict[str, str] | None = None) -> str:
        pack = self.context_manager.build(items, objective)
        rendered = pack.render()
        drift = self.context_drift_evaluator.evaluate(required_facts or {}, rendered)
        self.context_metrics = {
            "token_estimate": pack.token_estimate,
            "source_tokens": pack.source_tokens,
            "compression_ratio": pack.compression_ratio,
            "stale_ratio": pack.stale_ratio,
            "dropped_keys": pack.dropped_keys,
            "compressed_keys": pack.compressed_keys,
            **drift,
        }
        return rendered

    def summary(self) -> dict[str, Any]:
        trace = self.trace_store.summary(self.trace_id)
        return {
            "trace": trace,
            "context": self.context_metrics,
            "recovery_attempts": self.recovery_attempts,
            "recovery_successes": self.recovery_successes,
            "failure_events": self.failure_events,
            "approval_requests": self.approval_requests,
        }


class AgentHarnessRuntime:
    """Control plane for tracing, context, sandbox, recovery, HITL and eval."""

    def __init__(self, config: HarnessConfig | None = None):
        self.config = config or HarnessConfig()
        self.trace_store = TraceStore(self.config.trace_jsonl_path if self.config.enable_tracing else None)
        self.approval_store = ApprovalStore()
        self.failure_classifier = FailureClassifier()
        self.recovery_policy = RecoveryPolicy()
        self.evaluator = AgentEvaluator()
        self.context_drift_evaluator = ContextDriftEvaluator()

    def start(self, *, project_id: str, task_id: str, workspace: str) -> HarnessSession:
        root = Path(workspace).resolve()
        context_policy = ContextPolicy(
            max_tokens=self.config.max_context_tokens,
            reserve_tokens=self.config.reserve_context_tokens,
            allow_compression=self.config.allow_context_compression,
        )
        sandbox = SandboxPolicy(
            workspace_root=str(root),
            allow_network=self.config.allow_network,
            max_changed_files=self.config.max_changed_files,
        )
        trace_id = self.trace_store.new_trace_id()
        return HarnessSession(
            trace_id=trace_id,
            project_id=project_id,
            task_id=task_id,
            workspace=str(root),
            trace_store=self.trace_store,
            sandbox_policy=sandbox,
            approval_store=self.approval_store,
            failure_classifier=self.failure_classifier,
            recovery_policy=self.recovery_policy,
            evaluator=self.evaluator,
            context_manager=ContextManager(context_policy),
            context_drift_evaluator=self.context_drift_evaluator,
        )

    def evaluate(
        self,
        session: HarnessSession,
        *,
        verification_statuses: list[str],
        completion_claimed: bool,
        thresholds: EvalThresholds | None = None,
    ):
        return self.evaluator.evaluate(
            trace_summary=session.trace_store.summary(session.trace_id),
            verification_statuses=verification_statuses,
            completion_claimed=completion_claimed,
            context_drift=float(session.context_metrics.get("drift_score", 0.0) or 0.0),
            recovery_attempts=session.recovery_attempts,
            recovery_successes=session.recovery_successes,
            thresholds=thresholds,
        )
