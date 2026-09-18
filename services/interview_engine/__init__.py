"""
Interview Engine Service

Responsible for conducting technical interviews based on real project code,
decisions, and experiments.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from packages.contracts import (
    ArchitectureDecision,
    ExecutionRecord,
    InterviewQuestion,
    InterviewSession,
    MaturityLevel,
    ProjectFacts,
)


@dataclass
class GapAnalysis:
    """Analysis of gaps discovered during interview"""
    gap_type: str  # "knowledge", "engineering", "evidence", "experiment"
    description: str
    related_task_id: str | None = None
    severity: str = "medium"  # "low", "medium", "high"


@dataclass
class InterviewOutput:
    """Complete interview output"""
    session: InterviewSession
    initial_questions: list[InterviewQuestion]
    gap_analysis: list[GapAnalysis]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session.to_dict(),
            "initial_questions": [q.to_dict() for q in self.initial_questions],
            "gap_analysis": [
                {
                    "gap_type": g.gap_type,
                    "description": g.description,
                    "related_task_id": g.related_task_id,
                    "severity": g.severity,
                }
                for g in self.gap_analysis
            ],
        }


class InterviewEngine:
    """
    Conducts technical interviews based on:
    - Real project code
    - Real architectural decisions
    - Real experiments and their results
    - Real failure cases
    
    Generates continuous follow-up questions to probe deeper understanding.
    """
    
    def __init__(self):
        self.question_templates = self._build_question_templates()
    
    def _build_question_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Build question templates by category"""
        return {
            "architecture": [
                {
                    "template": "为什么选择 {component} 而不是其他方案？",
                    "follow_ups": [
                        "还有其他方案你考虑过吗？",
                        "你如何评估不同方案的优劣？",
                        "这个选择在当前场景下有什么trade-off？",
                    ],
                },
                {
                    "template": "描述 {component} 的设计决策过程。",
                    "follow_ups": [
                        "谁参与了决策？",
                        "决策时考虑了哪些因素？",
                        "如果重新做，你会改变什么？",
                    ],
                },
            ],
            "implementation": [
                {
                    "template": "这段代码 {snippet} 为什么要这样实现？",
                    "follow_ups": [
                        "有考虑过其他实现方式吗？",
                        "这个实现的优缺点是什么？",
                        "如果需求变化，这个设计如何应对？",
                    ],
                },
                {
                    "template": "你如何测试 {component} 的正确性？",
                    "follow_ups": [
                        "测试覆盖了哪些场景？",
                        "边界情况如何处理？",
                        "如果有bug，你会如何调试？",
                    ],
                },
            ],
            "production": [
                {
                    "template": "如果 {component} 在生产环境失败，你会如何处理？",
                    "follow_ups": [
                        "有什么监控和告警机制？",
                        "如何快速恢复服务？",
                        "事后会做什么改进？",
                    ],
                },
                {
                    "template": "描述 {component} 的性能特征。",
                    "follow_ups": [
                        "有什么性能测试数据？",
                        "瓶颈在哪里？",
                        "如何优化？",
                    ],
                },
            ],
            "experiments": [
                {
                    "template": "你做了哪些实验来验证 {component}？",
                    "follow_ups": [
                        "实验设计是怎样的？",
                        "如何确保实验结果可信？",
                        "有哪些意外发现？",
                    ],
                },
                {
                    "template": "为什么 {before} 改成了 {after}？",
                    "follow_ups": [
                        "如何量化改进效果？",
                        "改进有什么代价？",
                        "还有哪些可以改进的地方？",
                    ],
                },
            ],
            "evaluation": [
                {
                    "template": "你如何评估 {component} 的质量？",
                    "follow_ups": [
                        "使用了哪些指标？",
                        "指标如何定义的？",
                        "有什么局限性？",
                    ],
                },
                {
                    "template": "你的评测数据集是如何构建的？",
                    "follow_ups": [
                        "数据集覆盖了哪些场景？",
                        "如何避免数据泄露？",
                        "如何处理分布偏移？",
                    ],
                },
            ],
        }
    
    def conduct_interview(
        self,
        project_facts: dict[str, Any],
        execution_records: list[dict[str, Any]],
        architecture_decisions: list[dict[str, Any]],
        maturity_assessment: dict[str, Any],
        project_id: str,
    ) -> InterviewOutput:
        """
        Conduct an interview based on project history.
        
        Args:
            project_facts: Project facts from auditor
            execution_records: History of execution records
            architecture_decisions: Recorded architecture decisions
            maturity_assessment: Current maturity assessment
            project_id: Project identifier
        
        Returns:
            InterviewOutput with questions and gap analysis
        """
        # Create session
        session = InterviewSession(
            id=str(uuid.uuid4()),
            project_id=project_id,
            task_id=None,
            started_at="",  # Will be set by caller
            status="in_progress",
        )
        
        # Generate initial questions based on project
        questions = self._generate_questions(
            project_facts,
            execution_records,
            architecture_decisions,
            maturity_assessment,
            session.id,
        )
        
        # Analyze gaps
        gaps = self._analyze_gaps(
            project_facts,
            execution_records,
            architecture_decisions,
            questions,
        )
        
        return InterviewOutput(
            session=session,
            initial_questions=questions,
            gap_analysis=gaps,
        )
    
    def _generate_questions(
        self,
        facts: dict[str, Any],
        records: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        maturity: dict[str, Any],
        session_id: str,
    ) -> list[InterviewQuestion]:
        """Generate interview questions"""
        questions = []
        
        # Project introduction questions
        questions.extend(self._generate_intro_questions(facts, session_id))
        
        # Architecture questions based on decisions
        if decisions:
            questions.extend(self._generate_architecture_questions(decisions, session_id))
        
        # Implementation questions based on execution records
        if records:
            questions.extend(self._generate_implementation_questions(records, session_id))
        
        # Production questions based on maturity level
        questions.extend(self._generate_production_questions(maturity, session_id))
        
        # Evaluation questions if benchmarks exist
        questions.extend(self._generate_evaluation_questions(facts, session_id))
        
        return questions[:10]  # Limit to 10 initial questions
    
    def _generate_intro_questions(
        self,
        facts: dict[str, Any],
        session_id: str,
    ) -> list[InterviewQuestion]:
        """Generate project introduction questions"""
        questions = []
        
        # What is this project?
        questions.append(InterviewQuestion(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question="请介绍一下这个项目，解决了什么问题？",
            context=f"Project type: {facts.get('project_type', 'unknown')}",
            follow_ups=[
                "目标用户是谁？",
                "核心价值主张是什么？",
                "与现有解决方案有什么不同？",
            ],
            gap_type=None,
            status="pending",
        ))
        
        # Tech stack
        questions.append(InterviewQuestion(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question=f"为什么选择 {', '.join(facts.get('frameworks', [])[:2])} 作为技术栈？",
            context=f"Tech stack: {', '.join(facts.get('main_language', []))}",
            follow_ups=[
                "有考虑过其他技术吗？",
                "技术栈的优缺点是什么？",
                "团队对这个技术栈的熟悉程度如何？",
            ],
            gap_type="engineering",
            status="pending",
        ))
        
        return questions
    
    def _generate_architecture_questions(
        self,
        decisions: list[dict[str, Any]],
        session_id: str,
    ) -> list[InterviewQuestion]:
        """Generate architecture-related questions"""
        questions = []
        
        for decision in decisions[:3]:  # Limit to 3
            questions.append(InterviewQuestion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                question=f"关于 {decision.get('title', '架构决策')}，能详细说说吗？",
                context=decision.get("context", ""),
                follow_ups=[
                    f"为什么选择 {decision.get('decision', '这个方案')}？",
                    f"考虑过哪些替代方案？{', '.join(decision.get('alternatives_considered', ['无'])[:2])}",
                    "这个决策有什么代价或风险？",
                ],
                gap_type="engineering",
                status="pending",
            ))
        
        return questions
    
    def _generate_implementation_questions(
        self,
        records: list[dict[str, Any]],
        session_id: str,
    ) -> list[InterviewQuestion]:
        """Generate implementation-related questions"""
        questions = []
        
        for record in records[:3]:  # Limit to 3
            changes = record.get("changes", [])
            if changes:
                change = changes[0]
                questions.append(InterviewQuestion(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    question=f"为什么修改 {change.get('file_path', '这个文件')}？",
                    context=change.get("purpose", ""),
                    follow_ups=[
                        "修改的具体内容是什么？",
                        "这个修改有什么风险？",
                        "如何验证修改的正确性？",
                    ],
                    gap_type="evidence",
                    status="pending",
                ))
        
        return questions
    
    def _generate_production_questions(
        self,
        maturity: dict[str, Any],
        session_id: str,
    ) -> list[InterviewQuestion]:
        """Generate production-readiness questions"""
        questions = []
        
        level = maturity.get("overall_level", "unknown")
        
        if level in ["idea", "demo"]:
            questions.append(InterviewQuestion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                question="项目距离生产可用还差什么？",
                context=f"Current level: {level}",
                follow_ups=[
                    "最关键的三个缺失是什么？",
                    "为什么这些是优先的？",
                    "计划如何解决？",
                ],
                gap_type="knowledge",
                status="pending",
            ))
        
        if level in ["mvp", "pre_production"]:
            questions.append(InterviewQuestion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                question="如果现在要上线，你会最担心什么？",
                context=f"Current level: {level}",
                follow_ups=[
                    "有什么监控和告警机制？",
                    "出问题了如何快速响应？",
                    "有什么回滚计划？",
                ],
                gap_type="engineering",
                status="pending",
            ))
        
        return questions
    
    def _generate_evaluation_questions(
        self,
        facts: dict[str, Any],
        session_id: str,
    ) -> list[InterviewQuestion]:
        """Generate evaluation-related questions"""
        questions = []
        
        # Check if evaluation system exists
        impl_status = facts.get("implementation_status", {})
        eval_status = impl_status.get("evaluation", [])
        
        if any("benchmark" in str(item).lower() for item in eval_status):
            questions.append(InterviewQuestion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                question="你如何评估这个项目的质量？",
                context="Has benchmark/evaluation system",
                follow_ups=[
                    "使用哪些指标？",
                    "指标如何定义的？",
                    "有基准测试数据吗？",
                ],
                gap_type="evidence",
                status="pending",
            ))
        
        return questions
    
    def _analyze_gaps(
        self,
        facts: dict[str, Any],
        records: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        questions: list[InterviewQuestion],
    ) -> list[GapAnalysis]:
        """Analyze gaps based on project state"""
        gaps = []
        
        # Check for knowledge gaps
        level = facts.get("current_maturity", "unknown")
        if level in ["idea", "demo"]:
            gaps.append(GapAnalysis(
                gap_type="knowledge",
                description="对生产环境需求的理解不足",
                severity="high",
            ))
        
        # Check for evidence gaps
        if not records:
            gaps.append(GapAnalysis(
                gap_type="evidence",
                description="缺少工程实践记录",
                severity="medium",
            ))
        
        # Check for experiment gaps
        if not any(r.get("benchmark_results") for r in records):
            gaps.append(GapAnalysis(
                gap_type="experiment",
                description="缺少量化实验数据",
                severity="medium",
            ))
        
        # Check for engineering gaps
        impl_status = facts.get("implementation_status", {})
        if not impl_status.get("testing"):
            gaps.append(GapAnalysis(
                gap_type="engineering",
                description="缺少测试实践",
                severity="high",
            ))
        
        return gaps
    
    def generate_follow_up(
        self,
        question: InterviewQuestion,
        answer: str,
    ) -> str | None:
        """
        Generate a follow-up question based on the user's answer.
        
        Returns None if no more follow-ups are available.
        """
        if question.current_follow_up >= len(question.follow_ups):
            return None
        
        next_follow_up = question.follow_ups[question.current_follow_up]
        question.current_follow_up += 1
        
        return next_follow_up
    
    def evaluate_answer(
        self,
        question: InterviewQuestion,
        answer: str,
    ) -> dict[str, Any]:
        """
        Evaluate a user's answer.
        
        Returns assessment with gap type if knowledge gap detected.
        """
        # Simple heuristic evaluation
        # In production, this would use LLM
        
        short_answers = ["是", "否", "有", "没有", "不知道"]
        is_insufficient = len(answer.strip()) < 20 or answer.strip() in short_answers
        
        if is_insufficient:
            return {
                "quality": "insufficient",
                "gap_type": question.gap_type or "knowledge",
                "suggestion": "请提供更详细的回答，包含具体例子或数据。",
            }
        
        # Check for specific knowledge
        has_example = any(word in answer for word in ["例如", "比如", "具体", "实际"])
        has_reason = any(word in answer for word in ["因为", "所以", "由于", "导致"])
        has_quantitative = any(char in answer for char in ["%", "倍", "次", "个"])
        
        quality = "basic"
        if has_example and has_reason:
            quality = "good"
        if has_example and has_reason and has_quantitative:
            quality = "excellent"
        
        gap_type = None
        if quality == "basic":
            gap_type = question.gap_type
        
        return {
            "quality": quality,
            "gap_type": gap_type,
            "has_example": has_example,
            "has_reason": has_reason,
            "has_quantitative": has_quantitative,
            "suggestion": self._get_suggestion(quality, question.gap_type),
        }
    
    def _get_suggestion(self, quality: str, gap_type: str | None) -> str:
        """Get suggestion based on answer quality"""
        if quality == "excellent":
            return "回答非常详细，包含具体数据和例子。"
        elif quality == "good":
            return "回答不错，如果能加入一些具体数据会更好。"
        else:
            suggestions = {
                "knowledge": "建议补充相关概念和原理的解释。",
                "engineering": "建议说明具体的工程考量和技术选择。",
                "evidence": "建议提供具体的实验数据或代码引用。",
                "experiment": "建议说明实验设计和结果量化。",
            }
            return suggestions.get(gap_type, "请提供更详细的回答。")
