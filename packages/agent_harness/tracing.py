from __future__ import annotations

import json
import threading
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    name: str
    kind: str
    parent_span_id: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str | None = None
    status: str = "running"
    latency_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    cost_usd: float = 0.0
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["token_usage"] = self.token_usage.to_dict()
        return data


class TraceStore:
    """Dependency-free OpenTelemetry-like trace store for harness observability."""

    def __init__(self, jsonl_path: str | None = None):
        self._spans: dict[str, TraceSpan] = {}
        self._trace_index: dict[str, list[str]] = {}
        self._lock = threading.Lock()
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None
        if self.jsonl_path:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._current_span: ContextVar[str | None] = ContextVar("current_harness_span", default=None)

    def new_trace_id(self) -> str:
        return uuid.uuid4().hex

    def start_span(
        self,
        name: str,
        kind: str = "internal",
        *,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        parent_span_id = parent_span_id or self._current_span.get()
        if trace_id is None and parent_span_id and parent_span_id in self._spans:
            trace_id = self._spans[parent_span_id].trace_id
        trace_id = trace_id or self.new_trace_id()
        span = TraceSpan(
            trace_id=trace_id,
            span_id=uuid.uuid4().hex,
            name=name,
            kind=kind,
            parent_span_id=parent_span_id,
            attributes=dict(attributes or {}),
        )
        with self._lock:
            self._spans[span.span_id] = span
            self._trace_index.setdefault(trace_id, []).append(span.span_id)
        return span

    def end_span(
        self,
        span: TraceSpan,
        *,
        status: str = "ok",
        error: BaseException | None = None,
        token_usage: TokenUsage | None = None,
        cost_usd: float | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        ended = datetime.now(timezone.utc)
        started = datetime.fromisoformat(span.started_at)
        span.ended_at = ended.isoformat()
        span.latency_ms = max(0.0, (ended - started).total_seconds() * 1000.0)
        span.status = "error" if error else status
        if token_usage:
            span.token_usage = token_usage
        if cost_usd is not None:
            span.cost_usd = float(cost_usd)
        if attributes:
            span.attributes.update(attributes)
        if error:
            span.error_type = type(error).__name__
            span.error_message = str(error)
        if self.jsonl_path:
            with self._lock, self.jsonl_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(span.to_dict(), ensure_ascii=False) + "\n")
        return span

    @contextmanager
    def span(
        self,
        name: str,
        kind: str = "internal",
        *,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[TraceSpan]:
        span = self.start_span(name, kind, trace_id=trace_id, parent_span_id=parent_span_id, attributes=attributes)
        token = self._current_span.set(span.span_id)
        try:
            yield span
        except BaseException as exc:
            self.end_span(span, error=exc)
            raise
        else:
            if span.status == "running":
                self.end_span(span)
        finally:
            self._current_span.reset(token)

    def annotate(
        self,
        span: TraceSpan,
        *,
        attributes: dict[str, Any] | None = None,
        token_usage: TokenUsage | None = None,
        cost_usd: float | None = None,
    ) -> None:
        if attributes:
            span.attributes.update(attributes)
        if token_usage:
            span.token_usage = token_usage
        if cost_usd is not None:
            span.cost_usd = float(cost_usd)

    def get_trace(self, trace_id: str) -> list[TraceSpan]:
        with self._lock:
            return [self._spans[sid] for sid in self._trace_index.get(trace_id, [])]

    def summary(self, trace_id: str) -> dict[str, Any]:
        spans = self.get_trace(trace_id)
        tool_spans = [s for s in spans if s.kind == "tool"]
        llm_spans = [s for s in spans if s.kind == "llm"]
        errors = [s for s in spans if s.status == "error"]
        retries = [s for s in spans if bool(s.attributes.get("retry"))]
        total_input = sum(s.token_usage.input_tokens for s in spans)
        total_output = sum(s.token_usage.output_tokens for s in spans)
        total_cache_read = sum(s.token_usage.cache_read_tokens for s in spans)
        total_cost = sum(s.cost_usd for s in spans)
        total_latency = sum(s.latency_ms for s in spans if s.parent_span_id is None)
        if total_latency == 0:
            total_latency = sum(s.latency_ms for s in spans)
        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            "tool_calls": len(tool_spans),
            "llm_calls": len(llm_spans),
            "error_count": len(errors),
            "retry_count": len(retries),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "cache_read_tokens": total_cache_read,
            "total_tokens": total_input + total_output,
            "cost_usd": round(total_cost, 8),
            "latency_ms": round(total_latency, 3),
            "success": bool(spans) and not errors,
        }
