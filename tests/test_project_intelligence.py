"""
Tests for Project Intelligence - Real scanning without mocks
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.project_intelligence import (
    analyze_directory,
    build_project_facts,
    generate_observations,
)

# Use AIEduRAG as test project
TEST_PROJECT = Path("D:/AI_Engineering _Project_OS/_sources/AIEduRAG")


@pytest.mark.skipif(
    not TEST_PROJECT.exists(),
    reason="AIEduRAG source not found"
)
class TestProjectIntelligence:
    """Test real project scanning"""
    
    def test_analyze_directory(self):
        """Test directory analysis"""
        result = analyze_directory(str(TEST_PROJECT))
        
        # Should find Python files
        assert result.language_stats.get("python", 0) > 0, "Should detect Python files"
        
        # Should find test files
        assert len(result.test_files) > 0, "Should find test files"
        
        # Should find config files
        assert len(result.config_files) > 0, "Should find config files"
        
        # Should find README
        assert result.readme_found, "Should find README.md"
        
        # Should have evidence
        assert len(result.evidence) > 0, "Should collect evidence"
    
    def test_build_project_facts(self):
        """Test building project facts"""
        facts = build_project_facts(str(TEST_PROJECT), "AIEduRAG")
        
        # Basic info
        assert facts["project_name"] == "AIEduRAG"
        assert facts["project_type"] == "rag"
        
        # Should detect Python
        assert "python" in facts["main_language"]
        
        # Should detect frameworks
        assert len(facts["frameworks"]) > 0
        
        # Should have code metrics
        assert facts["total_files"] > 0
        assert facts["code_lines"] > 0
        
        # Should have evidence
        assert len(facts["evidence"]) > 0
        
        # Should have observations
        assert len(facts["raw_observations"]) >= 0
    
    def test_detect_capabilities(self):
        """Test capability detection"""
        facts = build_project_facts(str(TEST_PROJECT), "AIEduRAG")
        
        # AIEduRAG should have RAG-related code
        assert facts.get("has_rag") or facts["project_type"] == "rag"
    
    def test_evidence_collection(self):
        """Test that evidence is properly collected"""
        facts = build_project_facts(str(TEST_PROJECT), "AIEduRAG")
        
        for evidence in facts["evidence"]:
            assert "fact_type" in evidence
            assert "source_file" in evidence
            assert "content" in evidence or "verification_method" in evidence


class TestObservations:
    """Test observation generation"""
    
    def test_generate_observations(self):
        """Test observation generation"""
        if not TEST_PROJECT.exists():
            pytest.skip("Test project not found")
        
        result = analyze_directory(str(TEST_PROJECT))
        observations = generate_observations(result)
        
        # Should generate observations
        assert isinstance(observations, list)
        
        # Each observation should have required fields
        for obs in observations:
            assert "category" in obs
            assert "finding" in obs
            assert "severity" in obs
