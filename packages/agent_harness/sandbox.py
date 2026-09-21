from __future__ import annotations

import fnmatch
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuthorizationDecision:
    allowed: bool
    risk: RiskLevel
    reason: str
    requires_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk"] = self.risk.value
        return data


@dataclass
class ApprovalRequest:
    id: str
    action: str
    reason: str
    risk: str
    payload: dict[str, Any]
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: str | None = None
    decided_by: str | None = None


class ApprovalStore:
    def __init__(self):
        self._items: dict[str, ApprovalRequest] = {}

    def request(self, action: str, reason: str, risk: RiskLevel, payload: dict[str, Any]) -> ApprovalRequest:
        item = ApprovalRequest(uuid.uuid4().hex, action, reason, risk.value, dict(payload))
        self._items[item.id] = item
        return item

    def decide(self, request_id: str, approved: bool, actor: str = "human") -> ApprovalRequest:
        item = self._items[request_id]
        item.status = "approved" if approved else "denied"
        item.decided_at = datetime.now(timezone.utc).isoformat()
        item.decided_by = actor
        return item

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._items.get(request_id)

    def pending(self) -> list[ApprovalRequest]:
        return [i for i in self._items.values() if i.status == "pending"]


@dataclass
class SandboxPolicy:
    workspace_root: str
    allowed_commands: set[str] = field(default_factory=lambda: {"python", "python3", "pytest", "npm", "npx", "git", "ruff", "mypy", "docker"})
    network_commands: set[str] = field(default_factory=lambda: {"curl", "wget", "nc", "netcat", "ssh", "scp"})
    blocked_fragments: tuple[str, ...] = (
        "rm -rf",
        "mkfs",
        "shutdown",
        "reboot",
        "fdisk",
        "dd if=",
        "> /dev/",
    )
    approval_patterns: tuple[str, ...] = (
        "git push*",
        "docker push*",
        "pip install*",
        "npm install*",
        "alembic upgrade*",
        "*delete*",
    )
    allow_network: bool = False
    max_changed_files: int = 50

    def _inside_workspace(self, path: str) -> bool:
        root = Path(self.workspace_root).resolve()
        candidate = Path(path).resolve()
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False

    def authorize_file(self, path: str, action: str = "read") -> AuthorizationDecision:
        if not self._inside_workspace(path):
            return AuthorizationDecision(False, RiskLevel.CRITICAL, "Path escapes workspace boundary")
        if action in {"delete", "overwrite_many"}:
            return AuthorizationDecision(True, RiskLevel.HIGH, "Destructive file action requires approval", True)
        return AuthorizationDecision(True, RiskLevel.LOW, "Workspace-scoped file action")

    def authorize_command(self, command: list[str], cwd: str) -> AuthorizationDecision:
        if not command:
            return AuthorizationDecision(False, RiskLevel.HIGH, "Empty command")
        if not self._inside_workspace(cwd):
            return AuthorizationDecision(False, RiskLevel.CRITICAL, "Command cwd escapes workspace boundary")
        executable = Path(command[0]).name.lower()
        rendered = " ".join(command).strip().lower()
        if any(fragment in rendered for fragment in self.blocked_fragments):
            return AuthorizationDecision(False, RiskLevel.CRITICAL, "Destructive command blocked by policy")
        if executable in self.network_commands and not self.allow_network:
            return AuthorizationDecision(False, RiskLevel.HIGH, "Network command blocked by sandbox policy")
        if executable not in self.allowed_commands:
            return AuthorizationDecision(False, RiskLevel.HIGH, f"Command not allowlisted: {executable}")
        if any(fnmatch.fnmatch(rendered, pattern) for pattern in self.approval_patterns):
            return AuthorizationDecision(True, RiskLevel.HIGH, "Command requires human approval", True)
        if executable == "docker":
            return AuthorizationDecision(True, RiskLevel.MEDIUM, "Container operation allowed with elevated risk")
        return AuthorizationDecision(True, RiskLevel.LOW, "Command allowed")

    def sanitized_env(self, env: dict[str, str] | None = None) -> dict[str, str]:
        source = env or os.environ
        safe_keys = {"PATH", "PYTHONPATH", "VIRTUAL_ENV", "HOME", "TMP", "TEMP", "LANG", "LC_ALL"}
        return {k: v for k, v in source.items() if k in safe_keys}
