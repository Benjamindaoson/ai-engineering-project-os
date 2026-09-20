from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


def estimate_tokens(text: str) -> int:
    """Tokenizer-independent estimate for budgeting; never use this for billing."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


@dataclass
class ContextItem:
    key: str
    text: str
    category: str = "general"
    priority: float = 0.5
    pinned: bool = False
    source: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stale_after_seconds: int | None = None

    @property
    def token_estimate(self) -> int:
        return estimate_tokens(self.text)


@dataclass
class ContextPolicy:
    max_tokens: int = 8000
    reserve_tokens: int = 1200
    compression_trigger_ratio: float = 0.80
    max_item_tokens: int = 1200
    keep_recent: int = 6
    allow_compression: bool = True

    @property
    def usable_tokens(self) -> int:
        return max(1, self.max_tokens - self.reserve_tokens)


@dataclass
class ContextPack:
    items: list[ContextItem]
    dropped_keys: list[str]
    compressed_keys: list[str]
    token_estimate: int
    source_tokens: int
    compression_ratio: float
    stale_ratio: float

    def render(self) -> str:
        return "\n\n".join(f"[{item.category}:{item.key}]\n{item.text}" for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [asdict(i) for i in self.items],
            "dropped_keys": self.dropped_keys,
            "compressed_keys": self.compressed_keys,
            "token_estimate": self.token_estimate,
            "source_tokens": self.source_tokens,
            "compression_ratio": self.compression_ratio,
            "stale_ratio": self.stale_ratio,
        }


class ContextManager:
    def __init__(self, policy: ContextPolicy | None = None):
        self.policy = policy or ContextPolicy()

    @staticmethod
    def _terms(text: str) -> set[str]:
        return {t for t in re.findall(r"[a-zA-Z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}", text.lower())}

    def _relevance(self, item: ContextItem, objective: str) -> float:
        objective_terms = self._terms(objective)
        item_terms = self._terms(item.text + " " + item.key + " " + item.category)
        overlap = len(objective_terms & item_terms) / max(1, len(objective_terms))
        pin_bonus = 2.0 if item.pinned else 0.0
        return pin_bonus + float(item.priority) + overlap

    def _is_stale(self, item: ContextItem, now: datetime) -> bool:
        if item.stale_after_seconds is None:
            return False
        try:
            created = datetime.fromisoformat(item.created_at)
        except ValueError:
            return False
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (now - created).total_seconds() > item.stale_after_seconds

    def _compress(self, item: ContextItem) -> ContextItem:
        max_chars = self.policy.max_item_tokens * 4
        text = item.text.strip()
        if len(text) <= max_chars:
            return item
        head = int(max_chars * 0.65)
        tail = max_chars - head
        compressed = text[:head] + "\n...[context compressed]...\n" + text[-tail:]
        return ContextItem(
            key=item.key,
            text=compressed,
            category=item.category,
            priority=item.priority,
            pinned=item.pinned,
            source=item.source,
            created_at=item.created_at,
            stale_after_seconds=item.stale_after_seconds,
        )

    def build(self, items: Iterable[ContextItem], objective: str, now: datetime | None = None) -> ContextPack:
        now = now or datetime.now(timezone.utc)
        source = list(items)
        source_tokens = sum(i.token_estimate for i in source)
        stale_count = sum(1 for i in source if self._is_stale(i, now))
        ranked = sorted(source, key=lambda i: self._relevance(i, objective), reverse=True)
        budget = self.policy.usable_tokens
        selected: list[ContextItem] = []
        dropped: list[str] = []
        compressed: list[str] = []
        used = 0
        for item in ranked:
            candidate = item
            if self.policy.allow_compression and item.token_estimate > self.policy.max_item_tokens:
                candidate = self._compress(item)
                if candidate.text != item.text:
                    compressed.append(item.key)
            cost = candidate.token_estimate
            if used + cost <= budget or (candidate.pinned and not selected):
                selected.append(candidate)
                used += cost
            else:
                dropped.append(item.key)
        ratio = used / source_tokens if source_tokens else 1.0
        return ContextPack(
            items=selected,
            dropped_keys=dropped,
            compressed_keys=compressed,
            token_estimate=used,
            source_tokens=source_tokens,
            compression_ratio=ratio,
            stale_ratio=stale_count / len(source) if source else 0.0,
        )


class ContextDriftEvaluator:
    """Deterministic fact-retention check for long-horizon context regression."""

    def evaluate(self, required_facts: dict[str, str], current_context: str) -> dict[str, Any]:
        normalized = current_context.lower()
        missing: list[str] = []
        for key, value in required_facts.items():
            if str(value).lower() not in normalized:
                missing.append(key)
        total = len(required_facts)
        retention = (total - len(missing)) / total if total else 1.0
        return {
            "required_fact_count": total,
            "missing_facts": missing,
            "retention_rate": retention,
            "drift_score": 1.0 - retention,
        }
