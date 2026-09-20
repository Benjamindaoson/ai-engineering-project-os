from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Protocol


@dataclass
class MemoryRecord:
    key: str
    content: str
    memory_type: str = "episodic"
    tags: list[str] = field(default_factory=list)
    score: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryStore(Protocol):
    def put(self, record: MemoryRecord) -> None: ...
    def search(self, query: str, limit: int = 5) -> list[MemoryRecord]: ...


class InMemoryMemoryStore:
    """P2 reference store; deliberately not wired into planning by default."""

    def __init__(self):
        self._records: dict[str, MemoryRecord] = {}

    def put(self, record: MemoryRecord) -> None:
        self._records[record.key] = record

    def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        terms = {t.lower() for t in query.split() if t.strip()}
        ranked: list[tuple[float, MemoryRecord]] = []
        for record in self._records.values():
            hay = (record.content + " " + " ".join(record.tags)).lower()
            overlap = sum(1 for t in terms if t in hay)
            ranked.append((overlap + record.score * 0.01, record))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in ranked[:limit]]


@dataclass
class TrajectoryExample:
    task_type: str
    success: bool
    actions: list[str]
    failure_type: str | None = None
    tokens: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrajectoryMiner:
    """Offline-only P2 trajectory mining primitive, not online learning."""

    def summarize(self, examples: Iterable[TrajectoryExample]) -> dict[str, Any]:
        rows = list(examples)
        by_type: dict[str, list[TrajectoryExample]] = defaultdict(list)
        for row in rows:
            by_type[row.task_type].append(row)
        summary: dict[str, Any] = {"total": len(rows), "task_types": {}}
        for task_type, group in by_type.items():
            success = sum(1 for r in group if r.success)
            summary["task_types"][task_type] = {
                "count": len(group),
                "success_rate": success / len(group),
                "avg_tokens": sum(r.tokens for r in group) / len(group),
                "avg_latency_ms": sum(r.latency_ms for r in group) / len(group),
                "failure_types": sorted({r.failure_type for r in group if r.failure_type}),
            }
        return summary
