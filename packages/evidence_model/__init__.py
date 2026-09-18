"""
Evidence Model Package

Provides data structures and utilities for evidence collection and verification.
Evidence is the foundation of all maturity assessments - every claim must be backed by evidence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EvidenceType(str, Enum):
    CODE = "code"
    TEST = "test"
    RUN_RESULT = "run_result"
    BENCHMARK = "benchmark"
    CONFIG = "config"
    ARCHITECTURE_DECISION = "architecture_decision"
    COMMIT = "commit"
    DEPLOYMENT = "deployment"
    USER_EXPLANATION = "user_explanation"
    INTERVIEW_ANSWER = "interview_answer"


@dataclass(frozen=True)
class Evidence:
    """
    Immutable evidence record.
    
    Each piece of evidence must have:
    - A type (what kind of evidence)
    - A source (where it came from)
    - Content (what it contains)
    - A score (confidence/quality of evidence)
    """
    id: str
    type: EvidenceType
    source_path: str
    title: str
    description: str
    content: str
    line_start: int | None = None
    line_end: int | None = None
    score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "source_path": self.source_path,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "score": self.score,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class EvidencePacket:
    """
    Collection of evidence related to a query or claim.
    
    Used to group evidence together and provide confidence assessment.
    """
    query: str
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    blocked_evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    
    @property
    def has_evidence(self) -> bool:
        return len(self.evidence) > 0
    
    @property
    def is_blocked(self) -> bool:
        return len(self.blocked_evidence) > 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "evidence": [e.to_dict() for e in self.evidence],
            "confidence": self.confidence,
            "blocked_evidence": list(self.blocked_evidence),
        }


@dataclass
class EvidenceStore:
    """
    Store and manage evidence for a project.
    
    Provides methods for adding, querying, and validating evidence.
    """
    project_id: str
    evidence: list[Evidence] = field(default_factory=list)
    
    def add(self, evidence: Evidence) -> None:
        """Add evidence to the store"""
        self.evidence.append(evidence)
    
    def add_batch(self, evidence_list: list[Evidence]) -> None:
        """Add multiple evidence items"""
        self.evidence.extend(evidence_list)
    
    def get_by_type(self, evidence_type: EvidenceType) -> list[Evidence]:
        """Get all evidence of a specific type"""
        return [e for e in self.evidence if e.type == evidence_type]
    
    def get_by_source(self, source_path: str) -> list[Evidence]:
        """Get all evidence from a specific source"""
        return [e for e in self.evidence if e.source_path == source_path]
    
    def get_by_min_score(self, min_score: float) -> list[Evidence]:
        """Get all evidence with score >= min_score"""
        return [e for e in self.evidence if e.score >= min_score]
    
    def query(self, query: str, min_score: float = 0.0) -> EvidencePacket:
        """
        Query evidence related to a topic.
        
        Returns an EvidencePacket with matching evidence and confidence score.
        """
        # Simple keyword matching - in production, use vector search
        query_lower = query.lower()
        matched = []
        
        for e in self.evidence:
            if e.score < min_score:
                continue
            # Check if any keyword matches
            keywords = query_lower.split()
            content_lower = e.content.lower()
            title_lower = e.title.lower()
            
            if any(kw in content_lower or kw in title_lower for kw in keywords):
                matched.append(e)
        
        # Sort by score
        matched.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate confidence
        confidence = 0.0
        if matched:
            confidence = sum(e.score for e in matched) / len(matched)
            confidence = min(confidence, 1.0)
        
        return EvidencePacket(
            query=query,
            evidence=tuple(matched),
            confidence=confidence,
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "evidence": [e.to_dict() for e in self.evidence],
            "total_count": len(self.evidence),
        }


@dataclass
class EvidenceBuilder:
    """
    Builder for creating Evidence objects.
    
    Usage:
        evidence = (EvidenceBuilder()
            .with_id("test-001")
            .with_type(EvidenceType.CODE)
            .with_source("src/utils/helper.py")
            .with_title("Helper function")
            .with_content(code_snippet)
            .build())
    """
    _id: str = ""
    _type: EvidenceType = EvidenceType.CODE
    _source_path: str = ""
    _title: str = ""
    _description: str = ""
    _content: str = ""
    _line_start: int | None = None
    _line_end: int | None = None
    _score: float = 0.0
    
    def with_id(self, id: str) -> "EvidenceBuilder":
        self._id = id
        return self
    
    def with_type(self, evidence_type: EvidenceType) -> "EvidenceBuilder":
        self._type = evidence_type
        return self
    
    def with_source(self, source_path: str) -> "EvidenceBuilder":
        self._source_path = source_path
        return self
    
    def with_title(self, title: str) -> "EvidenceBuilder":
        self._title = title
        return self
    
    def with_description(self, description: str) -> "EvidenceBuilder":
        self._description = description
        return self
    
    def with_content(self, content: str) -> "EvidenceBuilder":
        self._content = content
        return self
    
    def with_lines(self, start: int, end: int) -> "EvidenceBuilder":
        self._line_start = start
        self._line_end = end
        return self
    
    def with_score(self, score: float) -> "EvidenceBuilder":
        self._score = score
        return self
    
    def build(self) -> Evidence:
        if not self._id:
            raise ValueError("Evidence must have an id")
        if not self._source_path:
            raise ValueError("Evidence must have a source_path")
        
        return Evidence(
            id=self._id,
            type=self._type,
            source_path=self._source_path,
            title=self._title,
            description=self._description,
            content=self._content,
            line_start=self._line_start,
            line_end=self._line_end,
            score=self._score,
        )


def build_evidence_packet(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    min_score: float = 0.0,
    blocked_filter: Callable | None = None,
) -> EvidencePacket:
    """
    Build an EvidencePacket from candidate evidence.
    
    Args:
        query: The query this evidence is for
        candidates: List of candidate evidence dicts
        min_score: Minimum score threshold
        blocked_filter: Optional function to filter blocked evidence
    
    Returns:
        EvidencePacket with matched and blocked evidence
    """
    evidence: list[Evidence] = []
    blocked: list[dict[str, Any]] = []
    
    for item in candidates:
        text = str(item.get("text") or item.get("content") or "").strip()
        if not text:
            continue
        
        score = float(item.get("score") or 0.0)
        if score < min_score:
            blocked.append({
                "reason": "low_score",
                "score": score,
                "source_path": item.get("source_path", ""),
            })
            continue
        
        # Apply blocked filter if provided
        if blocked_filter and blocked_filter(item):
            blocked.append({
                "reason": "blocked_by_filter",
                "source_path": item.get("source_path", ""),
            })
            continue
        
        evidence.append(Evidence(
            id=item.get("id", ""),
            type=EvidenceType(item.get("type", "code")),
            source_path=str(item.get("source_path") or item.get("source") or ""),
            title=str(item.get("title") or ""),
            description=str(item.get("description") or ""),
            content=text,
            line_start=item.get("start_line"),
            line_end=item.get("end_line"),
            score=score,
        ))
    
    # Calculate confidence
    confidence = 0.0
    if evidence:
        confidence = max(e.score for e in evidence)
    
    return EvidencePacket(
        query=query,
        evidence=tuple(evidence),
        confidence=confidence,
        blocked_evidence=tuple(blocked),
    )
