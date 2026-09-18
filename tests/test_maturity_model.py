"""
Tests for Maturity Model
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from packages.maturity_model import MaturityEvaluator, MaturityLevel


class TestMaturityEvaluator:
    """Test maturity evaluation"""
    
    def test_evaluate_idea_level(self):
        """Test evaluation of idea-level project"""
        evaluator = MaturityEvaluator()
        
        facts = {
            "idea_problem": True,
            "idea_users": True,
            "idea_io": True,
            "idea_data_source": True,
            "idea_tech": True,
        }
        
        assessment = evaluator.evaluate(facts)
        
        assert assessment.overall_level == MaturityLevel.IDEA
    
    def test_get_upgrade_path(self):
        """Test upgrade path generation"""
        evaluator = MaturityEvaluator()
        
        path = evaluator.get_upgrade_path(MaturityLevel.DEMO)
        
        assert MaturityLevel.MVP in path
        assert MaturityLevel.PRE_PRODUCTION in path
        assert MaturityLevel.PRODUCTION in path
        assert len(path) == 3


class TestMaturityLevel:
    """Test maturity level enum"""
    
    def test_next_level(self):
        """Test next level calculation"""
        assert MaturityLevel.IDEA.next() == MaturityLevel.DEMO
        assert MaturityLevel.DEMO.next() == MaturityLevel.MVP
        assert MaturityLevel.MVP.next() == MaturityLevel.PRE_PRODUCTION
        assert MaturityLevel.PRE_PRODUCTION.next() == MaturityLevel.PRODUCTION
        assert MaturityLevel.PRODUCTION.next() is None
    
    def test_display_name(self):
        """Test display name"""
        assert MaturityLevel.IDEA.display_name() == "想法"
        assert MaturityLevel.DEMO.display_name() == "演示版"
        assert MaturityLevel.MVP.display_name() == "最小可用版本"
        assert MaturityLevel.PRE_PRODUCTION.display_name() == "准生产级"
        assert MaturityLevel.PRODUCTION.display_name() == "生产级"
    
    def test_from_string(self):
        """Test string parsing"""
        assert MaturityLevel.from_string("idea") == MaturityLevel.IDEA
        assert MaturityLevel.from_string("DEMO") == MaturityLevel.DEMO
        assert MaturityLevel.from_string("mvp") == MaturityLevel.MVP
        assert MaturityLevel.from_string("unknown") == MaturityLevel.IDEA  # Default
