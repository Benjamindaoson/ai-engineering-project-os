"""Production-oriented Agent Harness primitives.

P0/P1 modules are runtime-ready and dependency-free. P2 memory/trajectory modules are
explicitly opt-in and are not used to make planning decisions by default.
"""

from .ablation import AblationRun, AblationRunner, HarnessVariant
from .context import ContextDriftEvaluator, ContextItem, ContextManager, ContextPack, ContextPolicy, estimate_tokens
from .evaluation import AgentEvalResult, AgentEvaluator, EvalThresholds
from .memory import InMemoryMemoryStore, MemoryRecord, TrajectoryExample, TrajectoryMiner
from .recovery import FailureClassifier, FailureSignal, FailureType, RecoveryAction, RecoveryDecision, RecoveryPolicy
from .sandbox import ApprovalRequest, ApprovalStore, AuthorizationDecision, RiskLevel, SandboxPolicy
from .tracing import TokenUsage, TraceSpan, TraceStore

__all__ = [
    "AblationRun", "AblationRunner", "HarnessVariant",
    "ContextDriftEvaluator", "ContextItem", "ContextManager", "ContextPack", "ContextPolicy", "estimate_tokens",
    "AgentEvalResult", "AgentEvaluator", "EvalThresholds",
    "InMemoryMemoryStore", "MemoryRecord", "TrajectoryExample", "TrajectoryMiner",
    "FailureClassifier", "FailureSignal", "FailureType", "RecoveryAction", "RecoveryDecision", "RecoveryPolicy",
    "ApprovalRequest", "ApprovalStore", "AuthorizationDecision", "RiskLevel", "SandboxPolicy",
    "TokenUsage", "TraceSpan", "TraceStore",
]
