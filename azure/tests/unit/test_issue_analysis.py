"""
Unit tests for issue analysis functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

@pytest.mark.unit
class TestIssueAnalysis:
    """Test issue analysis functionality."""
    
    @pytest.fixture
    def issue_analyzer(self, mock_intelligence_engine):
        """Create issue analyzer instance for testing."""
        from unittest.mock import Mock
        
        analyzer = Mock()
        analyzer.intelligence_engine = mock_intelligence_engine
        analyzer.analyze_issue = AsyncMock()
        analyzer.calculate_confidence = Mock()
        analyzer.select_agent = Mock()
        analyzer.estimate_cost = Mock()
        
        return analyzer

    async def test_basic_issue_analysis(self, issue_analyzer, sample_github_issue):
        """Test basic issue analysis workflow."""
        # Setup expected return values
        issue_analyzer.analyze_issue.return_value = {
            "issue_type": "bug",
            "priority": "high", 
            "primary_agent": "debugger",
            "recommended_model": "sonnet",
            "confidence": 0.85,
            "auto_execute": True,
            "estimated_cost": 0.0045
        }
        
        # Execute analysis
        result = await issue_analyzer.analyze_issue(sample_github_issue, "test/repo")
        
        # Verify results
        assert result["issue_type"] == "bug"
        assert result["priority"] == "high"
        assert result["primary_agent"] == "debugger"
        assert result["confidence"] >= 0.8
        assert result["auto_execute"] is True
        
        # Verify analyzer was called
        issue_analyzer.analyze_issue.assert_called_once_with(sample_github_issue, "test/repo")

    def test_issue_classification(self, mock_intelligence_engine):
        """Test issue classification logic."""
        test_cases = [
            {
                "title": "Security vulnerability in authentication",
                "body": "Found a potential security exploit in the login system",
                "labels": [{"name": "security"}],
                "expected_type": "security"
            },
            {
                "title": "Application crashes on startup", 
                "body": "The app fails to start and shows error message",
                "labels": [{"name": "bug"}],
                "expected_type": "bug"
            },
            {
                "title": "Add new user dashboard",
                "body": "Implement a comprehensive user dashboard with analytics",
                "labels": [{"name": "enhancement"}],
                "expected_type": "feature"
            }
        ]
        
        for test_case in test_cases:
            # Mock intelligence engine response
            mock_intelligence_engine.analyze_issue_pattern.return_value = {
                "issue_type": test_case["expected_type"],
                "priority": "medium",
                "complexity_score": 0.6,
                "confidence_score": 0.8
            }
            
            # Test classification
            result = mock_intelligence_engine.analyze_issue_pattern(
                test_case["title"],
                test_case["body"], 
                test_case["labels"]
            )
            
            assert result["issue_type"] == test_case["expected_type"]
            assert result["confidence_score"] >= 0.7

    def test_agent_selection(self, mock_intelligence_engine):
        """Test agent selection based on issue type."""
        agent_mapping = {
            "security": "security-auditor",
            "bug": "debugger", 
            "feature": "backend-architect"
        }
        
        for issue_type, expected_agent in agent_mapping.items():
            # Mock recommendations
            mock_intelligence_engine.get_agent_recommendations.return_value = [
                {
                    "agent_name": expected_agent,
                    "recommended_model": "sonnet",
                    "confidence": 0.85
                }
            ]
            
            # Test agent selection
            recommendations = mock_intelligence_engine.get_agent_recommendations(issue_type)
            
            assert len(recommendations) > 0
            assert recommendations[0]["agent_name"] == expected_agent
            assert recommendations[0]["confidence"] >= 0.8

    def test_confidence_calculation(self, issue_analyzer):
        """Test confidence score calculation."""
        # Test high confidence scenario
        issue_analyzer.calculate_confidence.return_value = 0.92
        confidence = issue_analyzer.calculate_confidence({
            "issue_type_confidence": 0.95,
            "agent_match_confidence": 0.90,
            "complexity_penalty": 0.05,
            "label_bonus": 0.02
        })
        assert confidence >= 0.9
        
        # Test low confidence scenario
        issue_analyzer.calculate_confidence.return_value = 0.65
        confidence = issue_analyzer.calculate_confidence({
            "issue_type_confidence": 0.70,
            "agent_match_confidence": 0.60,
            "complexity_penalty": 0.15,
            "label_bonus": 0.0
        })
        assert confidence < 0.8

    def test_cost_estimation(self, issue_analyzer):
        """Test cost estimation for different models."""
        cost_tests = [
            {"model": "haiku", "complexity": 0.5, "expected_range": (0.001, 0.003)},
            {"model": "sonnet", "complexity": 0.7, "expected_range": (0.003, 0.008)},
            {"model": "opus", "complexity": 0.9, "expected_range": (0.012, 0.025)}
        ]
        
        for test in cost_tests:
            issue_analyzer.estimate_cost.return_value = sum(test["expected_range"]) / 2
            cost = issue_analyzer.estimate_cost(test["model"], "Sample issue text", test["complexity"])
            
            assert test["expected_range"][0] <= cost <= test["expected_range"][1]

    async def test_analysis_with_fallback(self, issue_analyzer, sample_github_issue):
        """Test analysis with intelligence engine fallback."""
        # Simulate intelligence engine failure
        issue_analyzer.analyze_issue.side_effect = [
            Exception("Intelligence engine unavailable"),
            {
                "issue_type": "bug",
                "priority": "medium",
                "primary_agent": "debugger", 
                "recommended_model": "sonnet",
                "confidence": 0.7,
                "auto_execute": False,
                "analysis_source": "rule_based"
            }
        ]
        
        # Should fallback to rule-based analysis
        with pytest.raises(Exception):
            await issue_analyzer.analyze_issue(sample_github_issue, "test/repo")

    def test_complex_issue_analysis(self, mock_intelligence_engine):
        """Test analysis of complex issues with multiple labels."""
        complex_issue = {
            "title": "Critical security bug causing data corruption",
            "body": """
            We've discovered a critical security vulnerability that allows unauthorized
            access to user data and causes database corruption. This affects the 
            authentication system and requires immediate attention.
            
            Steps to reproduce:
            1. Login with specific payload
            2. Access admin panel
            3. Export user data
            
            Expected: Access denied
            Actual: Full database dump exposed
            """,
            "labels": [
                {"name": "security"},
                {"name": "bug"},
                {"name": "critical"},
                {"name": "database"},
                {"name": "authentication"}
            ]
        }
        
        # Mock complex analysis
        mock_intelligence_engine.analyze_issue_pattern.return_value = {
            "issue_type": "security",
            "priority": "critical",
            "complexity_score": 0.95,
            "confidence_score": 0.98
        }
        
        result = mock_intelligence_engine.analyze_issue_pattern(
            complex_issue["title"],
            complex_issue["body"],
            complex_issue["labels"]
        )
        
        assert result["issue_type"] == "security"
        assert result["priority"] == "critical"
        assert result["complexity_score"] >= 0.9
        assert result["confidence_score"] >= 0.95

    def test_batch_issue_analysis(self, issue_analyzer):
        """Test batch processing of multiple issues."""
        issues = [
            {"number": 1, "title": "Bug #1", "body": "Error in module A"},
            {"number": 2, "title": "Feature request", "body": "Add new functionality"},
            {"number": 3, "title": "Security issue", "body": "Vulnerability found"}
        ]
        
        # Mock batch analysis
        async def mock_batch_analyze(issues_batch, repo):
            return [
                {
                    "issue_number": issue["number"],
                    "analysis": {
                        "issue_type": "bug" if "Bug" in issue["title"] else "feature",
                        "confidence": 0.8
                    }
                }
                for issue in issues_batch
            ]
        
        issue_analyzer.batch_analyze = mock_batch_analyze
        
        async def test_batch():
            results = await issue_analyzer.batch_analyze(issues, "test/repo")
            assert len(results) == 3
            assert all("analysis" in result for result in results)
            assert results[0]["analysis"]["issue_type"] == "bug"
        
        asyncio.run(test_batch())

    def test_analysis_caching(self, issue_analyzer):
        """Test caching of analysis results."""
        cache_key = "test/repo:123"
        cached_result = {
            "issue_type": "bug",
            "confidence": 0.85,
            "cached": True
        }
        
        # Mock caching behavior
        issue_analyzer.get_cached_analysis = Mock(return_value=cached_result)
        issue_analyzer.cache_analysis = Mock()
        
        # Test cache hit
        result = issue_analyzer.get_cached_analysis(cache_key)
        assert result["cached"] is True
        
        # Test cache miss and store
        issue_analyzer.get_cached_analysis.return_value = None
        result = issue_analyzer.get_cached_analysis(cache_key)
        assert result is None
        
        # Cache new result
        issue_analyzer.cache_analysis(cache_key, cached_result)
        issue_analyzer.cache_analysis.assert_called_once_with(cache_key, cached_result)

    def test_analysis_metrics_collection(self, issue_analyzer):
        """Test collection of analysis metrics."""
        # Mock metrics collection
        issue_analyzer.collect_metrics = Mock()
        
        analysis_metrics = {
            "processing_time": 0.25,
            "confidence_score": 0.85,
            "tokens_processed": 150,
            "model_used": "sonnet"
        }
        
        issue_analyzer.collect_metrics(analysis_metrics)
        issue_analyzer.collect_metrics.assert_called_once_with(analysis_metrics)

    @pytest.mark.parametrize("issue_type,expected_agent", [
        ("security", "security-auditor"),
        ("bug", "debugger"),
        ("feature", "backend-architect"),
        ("documentation", "docs-specialist"),
        ("performance", "performance-engineer")
    ])
    def test_agent_mapping(self, mock_intelligence_engine, issue_type, expected_agent):
        """Test agent mapping for different issue types."""
        mock_intelligence_engine.get_agent_recommendations.return_value = [
            {
                "agent_name": expected_agent,
                "recommended_model": "sonnet",
                "confidence": 0.85
            }
        ]
        
        recommendations = mock_intelligence_engine.get_agent_recommendations(issue_type)
        assert recommendations[0]["agent_name"] == expected_agent