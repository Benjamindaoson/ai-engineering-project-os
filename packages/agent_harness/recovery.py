from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class FailureType(str, Enum):
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    TOOL_INPUT = "tool_input"
    DEPENDENCY = "dependency"
    TEST_FAILURE = "test_failure"
    RUNTIME = "runtime"
    NETWORK_BLOCKED = "network_blocked"
    RESOURCE_LIMIT = "resource_limit"
    VERIFICATION = "verification"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    REPLAN = "replan"
    ROLLBACK = "rollback"
    FIX_DEPENDENCY = "fix_dependency"
    REQUEST_APPROVAL = "request_approval"
    ABORT = "abort"


@dataclass
class FailureSignal:
    failure_type: FailureType
    message: str
    return_code: int | None = None
    retryable: bool = False
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["failure_type"] = self.failure_type.value
        return data


@dataclass
class RecoveryDecision:
    action: RecoveryAction
    reason: str
    retry_after_seconds: float = 0.0
    requires_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["action"] = self.action.value
        return data


class FailureClassifier:
    def classify(
        self,
        *,
        message: str = "",
        return_code: int | None = None,
        timed_out: bool = False,
        phase: str = "runtime",
    ) -> FailureSignal:
        text = (message or "").lower()
        if timed_out or "timed out" in text or "timeout" in text:
            return FailureSignal(FailureType.TIMEOUT, message, return_code, retryable=True)
        if "permission denied" in text or "not permitted" in text or "approval required" in text:
            return FailureSignal(FailureType.PERMISSION, message, return_code, retryable=False)
        if "network is disabled" in text or "network blocked" in text:
            return FailureSignal(FailureType.NETWORK_BLOCKED, message, return_code, retryable=False)
        if "no module named" in text or "module not found" in text or "command not found" in text:
            return FailureSignal(FailureType.DEPENDENCY, message, return_code, retryable=True)
        if "memoryerror" in text or "out of memory" in text or "resource limit" in text:
            return FailureSignal(FailureType.RESOURCE_LIMIT, message, return_code, retryable=False)
        if phase == "verification":
            return FailureSignal(FailureType.VERIFICATION, message, return_code, retryable=False)
        if phase == "test" or ("failed" in text and ("pytest" in text or "test" in text)):
            return FailureSignal(FailureType.TEST_FAILURE, message, return_code, retryable=False)
        if "invalid argument" in text or "usage:" in text:
            return FailureSignal(FailureType.TOOL_INPUT, message, return_code, retryable=True)
        if return_code not in (None, 0):
            return FailureSignal(FailureType.RUNTIME, message, return_code, retryable=True)
        return FailureSignal(FailureType.UNKNOWN, message, return_code, retryable=False)


class RecoveryPolicy:
    def decide(
        self,
        signal: FailureSignal,
        *,
        attempt: int,
        max_retries: int,
        has_baseline: bool = True,
        irreversible: bool = False,
    ) -> RecoveryDecision:
        if irreversible or signal.failure_type == FailureType.PERMISSION:
            return RecoveryDecision(
                RecoveryAction.REQUEST_APPROVAL,
                "High-risk or permission-gated action requires human approval",
                requires_approval=True,
            )
        if signal.failure_type == FailureType.DEPENDENCY and attempt < max_retries:
            return RecoveryDecision(RecoveryAction.FIX_DEPENDENCY, "Dependency failure may be repairable before retry")
        if signal.failure_type in {FailureType.TIMEOUT, FailureType.TOOL_INPUT, FailureType.RUNTIME} and attempt < max_retries:
            return RecoveryDecision(RecoveryAction.RETRY, "Transient or correctable execution failure", retry_after_seconds=0.2)
        if signal.failure_type in {FailureType.TEST_FAILURE, FailureType.VERIFICATION}:
            return RecoveryDecision(RecoveryAction.REPLAN, "Environment evidence invalidated the current plan")
        if signal.failure_type == FailureType.RESOURCE_LIMIT:
            return RecoveryDecision(RecoveryAction.REPLAN, "Resource limit requires a lower-cost execution plan")
        if has_baseline and signal.failure_type in {FailureType.RUNTIME, FailureType.UNKNOWN}:
            return RecoveryDecision(RecoveryAction.ROLLBACK, "Unknown execution failure; preserve repository integrity")
        return RecoveryDecision(RecoveryAction.ABORT, "No safe automated recovery policy matched")
