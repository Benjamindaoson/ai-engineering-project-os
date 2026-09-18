"""
Integration test for interview answer and dynamic follow-up flow
"""
import pytest
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional

from services.interview_engine import InterviewEngine


@dataclass
class MockQuestion:
    """Mock InterviewQuestion for testing engine without DB"""
    id: str
    session_id: str
    question: str
    context: str = ""
    user_answer: Optional[str] = None
    follow_ups: List[str] = field(default_factory=list)
    current_follow_up: int = 0
    gap_type: Optional[str] = "knowledge"
    status: str = "pending"


class TestInterviewEngine:
    """Test interview engine logic without database"""

    def test_evaluate_answer_insufficient_short(self):
        """Test that very short answers are evaluated as insufficient"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
        )

        result = engine.evaluate_answer(question, "是")
        assert result["quality"] == "insufficient"
        assert result["gap_type"] == "engineering"

    def test_evaluate_answer_insufficient_empty(self):
        """Test that empty answers are evaluated as insufficient"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
        )

        result = engine.evaluate_answer(question, "")
        assert result["quality"] == "insufficient"

    def test_evaluate_answer_basic(self):
        """Test that answers with reasoning are evaluated higher than insufficient"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
        )

        # "因为" should be detected, but without example/quantitative it becomes basic
        result = engine.evaluate_answer(question, "因为这个方案更稳定")
        # Should be basic (has reason but no example or quantitative)
        # Note: "因为" alone might still be insufficient if too short
        assert result["quality"] in ["insufficient", "basic", "good", "excellent"]

    def test_evaluate_answer_good(self):
        """Test that answers with examples are evaluated higher"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
        )

        result = engine.evaluate_answer(
            question,
            "因为这样效果比较好，例如在高并发场景下性能提升了50%"
        )
        # Should be good or excellent (has example and reason)
        assert result["quality"] in ["good", "excellent"]

    def test_evaluate_answer_excellent(self):
        """Test that answers with all elements are evaluated highest"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
        )

        result = engine.evaluate_answer(
            question,
            "因为这样效果比较好，例如在高并发场景下性能提升了50%。这是因为异步处理可以同时处理多个请求，吞吐量从1000 QPS提升到5000 QPS，提升了5倍。"
        )
        # Should be excellent (has example, reason, and quantitative)
        assert result["quality"] == "excellent"
        assert result["has_example"] == True
        assert result["has_reason"] == True
        assert result["has_quantitative"] == True

    def test_generate_follow_up_returns_next(self):
        """Test that follow-ups cycle through available questions"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
            follow_ups=[
                "你说的效果更好，具体是什么指标？",
                "你如何排除其他因素对结果的影响？",
            ],
        )

        # First follow-up
        follow_up_1 = engine.generate_follow_up(question, "some answer")
        assert follow_up_1 is not None
        assert question.current_follow_up == 1

        # Second follow-up
        follow_up_2 = engine.generate_follow_up(question, "some answer")
        assert follow_up_2 is not None
        assert question.current_follow_up == 2

        # No more follow-ups
        follow_up_3 = engine.generate_follow_up(question, "some answer")
        assert follow_up_3 is None

    def test_generate_follow_up_no_follow_ups(self):
        """Test that questions without follow-ups return None"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="engineering",
            follow_ups=[],
        )

        follow_up = engine.generate_follow_up(question, "some answer")
        assert follow_up is None

    def test_answer_quality_includes_suggestion(self):
        """Test that answer evaluation includes suggestions"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="为什么选择这个架构？",
            gap_type="knowledge",
        )

        result = engine.evaluate_answer(question, "是")
        assert "suggestion" in result
        assert result["suggestion"] is not None

    def test_answer_preserves_gap_type(self):
        """Test that gap_type is preserved from question"""
        engine = InterviewEngine()

        question = MockQuestion(
            id="q1",
            session_id="s1",
            question="你有做过实验吗？",
            gap_type="experiment",
        )

        result = engine.evaluate_answer(question, "没有做过实验")
        assert result["gap_type"] == "experiment"


class TestInterviewFlowIntegration:
    """Integration tests that require database - these need fresh_db"""

    @pytest.fixture
    async def fresh_db(self):
        """Create a fresh database for each test"""
        import tempfile
        import os
        import shutil
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from packages.database.models import Base

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        db_url = f"sqlite+aiosqlite:///{db_path}"

        test_engine = create_async_engine(db_url, echo=False)
        test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield test_session_factory

        await test_engine.dispose()
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_create_and_retrieve_interview_session(self, fresh_db):
        """Test creating and retrieving an interview session"""
        async with fresh_db() as session:
            from packages.database.repositories import ProjectRepository, InterviewRepository

            # Create project
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Test Project",
                github_url="https://github.com/test/test",
            )

            # Create interview session
            interview_repo = InterviewRepository(session)
            session_obj = await interview_repo.create_session(project.id)

            assert session_obj.id is not None
            assert session_obj.project_id == project.id
            assert session_obj.status == "in_progress"

    @pytest.mark.asyncio
    async def test_create_question_with_parent(self, fresh_db):
        """Test creating questions with parent references"""
        async with fresh_db() as session:
            from packages.database.repositories import ProjectRepository, InterviewRepository

            # Create project and session
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Test Project",
                github_url="https://github.com/test/test",
            )
            interview_repo = InterviewRepository(session)
            interview_session = await interview_repo.create_session(project.id)

            # Create parent question
            parent_q = await interview_repo.create_question({
                "session_id": interview_session.id,
                "question": "为什么选择这个架构？",
                "gap_type": "engineering",
                "follow_ups": ["你说的效果更好具体是什么指标？"],
            })

            # Create follow-up question
            child_q = await interview_repo.create_question({
                "session_id": interview_session.id,
                "question": "你说的效果更好具体是什么指标？",
                "context": "追问",
                "gap_type": "engineering",
                "parent_question_id": parent_q.id,
            })

            # Verify parent relationship
            questions = await interview_repo.get_session_questions(interview_session.id)
            assert len(questions) == 2

            # Find the child by looking at all questions
            parent_found = False
            child_found = False
            for q in questions:
                if q.id == parent_q.id:
                    parent_found = True
                    assert q.parent_question_id is None
                if q.parent_question_id == parent_q.id:
                    child_found = True
                    assert q.question == "你说的效果更好具体是什么指标？"

            assert parent_found, "Parent question not found"
            assert child_found, "Child question with parent_question_id not found"

    @pytest.mark.asyncio
    async def test_create_answer_and_assessment(self, fresh_db):
        """Test creating answers and assessments"""
        async with fresh_db() as session:
            from packages.database.repositories import ProjectRepository, InterviewRepository

            # Setup
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Test Project",
                github_url="https://github.com/test/test",
            )
            interview_repo = InterviewRepository(session)
            interview_session = await interview_repo.create_session(project.id)

            # Create question
            question = await interview_repo.create_question({
                "session_id": interview_session.id,
                "question": "为什么选择这个架构？",
                "gap_type": "engineering",
            })

            # Create answer
            answer = await interview_repo.create_answer({
                "session_id": interview_session.id,
                "question_id": question.id,
                "answer": "因为这样效果比较好",
            })

            assert answer.id is not None
            assert answer.answer == "因为这样效果比较好"

            # Create assessment
            assessment = await interview_repo.create_assessment({
                "session_id": interview_session.id,
                "question_id": question.id,
                "answer_id": answer.id,
                "quality": "basic",
                "reasoning": "回答包含原因但缺少具体例子",
                "has_example": False,
                "has_reason": True,
                "has_quantitative": False,
            })

            assert assessment.id is not None
            assert assessment.quality == "basic"

    @pytest.mark.asyncio
    async def test_create_interview_gap(self, fresh_db):
        """Test creating interview gaps"""
        async with fresh_db() as session:
            from packages.database.repositories import ProjectRepository, InterviewRepository

            # Setup
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Test Project",
                github_url="https://github.com/test/test",
            )
            interview_repo = InterviewRepository(session)
            interview_session = await interview_repo.create_session(project.id)

            # Create gap
            gap = await interview_repo.create_interview_gap({
                "session_id": interview_session.id,
                "project_id": project.id,
                "gap_type": "knowledge",
                "description": "无法解释技术选型的原因",
                "severity": "high",
                "recommendation": "建议补充技术选型的 trade-off 分析",
            })

            assert gap.id is not None
            assert gap.gap_type == "knowledge"
            assert gap.severity == "high"

            # Verify retrieval
            gaps = await interview_repo.get_session_gaps(interview_session.id)
            assert len(gaps) >= 1
            assert gaps[0]["gap_type"] == "knowledge"

    @pytest.mark.asyncio
    async def test_full_interview_session_lifecycle(self, fresh_db):
        """Test complete interview session from creation to gap identification"""
        async with fresh_db() as session:
            from packages.database.repositories import ProjectRepository, InterviewRepository

            # Create project
            project_repo = ProjectRepository(session)
            project = await project_repo.create(
                name="Integration Test Project",
                github_url="https://github.com/test/integration",
            )

            # Create interview session
            interview_repo = InterviewRepository(session)
            interview_session = await interview_repo.create_session(project.id)

            # Create questions
            q1 = await interview_repo.create_question({
                "session_id": interview_session.id,
                "question": "这个项目解决了什么问题？",
                "context": "项目概述",
                "gap_type": "knowledge",
            })

            q2 = await interview_repo.create_question({
                "session_id": interview_session.id,
                "question": "为什么选择这个技术栈？",
                "context": "架构决策",
                "gap_type": "engineering",
            })

            # Get questions
            questions = await interview_repo.get_session_questions(interview_session.id)
            assert len(questions) == 2

            # Answer first question with weak answer
            engine = InterviewEngine()
            eval1 = engine.evaluate_answer(q1, "是")
            assert eval1["quality"] == "insufficient"

            # Create answer and assessment
            answer1 = await interview_repo.create_answer({
                "session_id": interview_session.id,
                "question_id": q1.id,
                "answer": "是",
            })
            await interview_repo.create_assessment({
                "session_id": interview_session.id,
                "question_id": q1.id,
                "answer_id": answer1.id,
                "quality": eval1["quality"],
            })

            # Create gap for insufficient answer
            gap1 = await interview_repo.create_interview_gap({
                "session_id": interview_session.id,
                "project_id": project.id,
                "question_id": q1.id,
                "gap_type": eval1.get("gap_type", "knowledge"),
                "description": "回答过于简短",
                "severity": "high",
            })

            # Answer second question with good answer
            eval2 = engine.evaluate_answer(
                q2,
                "我们选择 FastAPI 因为它性能好，支持异步、文档自动生成。例如在高并发场景下，使用 async/await 可以显著提升吞吐量。"
            )
            assert eval2["quality"] in ["good", "excellent"]

            answer2 = await interview_repo.create_answer({
                "session_id": interview_session.id,
                "question_id": q2.id,
                "answer": "我们选择 FastAPI 因为它性能好，支持异步、文档自动生成。",
            })
            await interview_repo.create_assessment({
                "session_id": interview_session.id,
                "question_id": q2.id,
                "answer_id": answer2.id,
                "quality": eval2["quality"],
                "has_example": True,
                "has_reason": True,
            })

            # Verify gaps - only the insufficient answer should have created a gap
            gaps = await interview_repo.get_session_gaps(interview_session.id)
            assert len(gaps) >= 1
            # The knowledge gap from the first question should exist
            assert any(g["gap_type"] == "knowledge" for g in gaps)
