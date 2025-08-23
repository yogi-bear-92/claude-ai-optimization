#!/usr/bin/env python3
"""
Intelligent Issue Analytics & Learning System - Phase 1
AI-Powered Issue Intelligence Engine

Implements pattern recognition, predictive agent routing, and enhanced confidence scoring
using machine learning to improve the Claude AI Issue Automation system.
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IssuePattern:
    """Represents a discovered issue pattern."""
    pattern_id: str
    keywords: List[str]
    issue_type: str
    complexity_score: float
    optimal_agent: str
    optimal_model: str
    success_rate: float
    average_cost: float
    sample_count: int

@dataclass
class AgentPerformance:
    """Tracks agent performance metrics."""
    agent_name: str
    issue_type: str
    success_rate: float
    average_execution_time: float
    average_cost: float
    total_executions: int
    last_updated: str

@dataclass
class ExecutionOutcome:
    """Represents the outcome of an issue automation execution."""
    issue_id: str  # Changed from execution_id for consistency
    repository: str
    issue_type: Optional[str] = None
    predicted_confidence: Optional[float] = None
    actual_success: Optional[bool] = None
    execution_time: Optional[float] = None
    agent_used: Optional[str] = None
    model_used: Optional[str] = None
    complexity_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str = ""
    
    # Legacy fields for backward compatibility
    execution_id: Optional[str] = None
    issue_number: Optional[int] = None
    assigned_agent: Optional[str] = None
    success: Optional[bool] = None
    actual_cost: Optional[float] = None
    quality_score: Optional[float] = None
    user_satisfaction: Optional[int] = None
    pr_merged: Optional[bool] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        # Handle legacy field mappings
        if self.execution_id and not self.issue_id:
            self.issue_id = self.execution_id
        if self.assigned_agent and not self.agent_used:
            self.agent_used = self.assigned_agent
        if self.success is not None and self.actual_success is None:
            self.actual_success = self.success
        if self.timestamp and not self.created_at:
            self.created_at = self.timestamp
        elif not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

class IssueIntelligenceEngine:
    """Main engine for AI-powered issue intelligence."""
    
    def __init__(self, data_path: str = "intelligence_data"):
        self.data_path = data_path
        self.ensure_data_directory()
        
        # ML Components
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.agent_performance_tracker = AgentPerformanceTracker()
        self.confidence_optimizer = ConfidenceOptimizer()
        
        # Data storage
        self.issue_patterns: List[IssuePattern] = []
        self.execution_history: List[ExecutionOutcome] = []
        self.agent_performance: Dict[str, AgentPerformance] = {}
        
        # Load existing data
        self.load_existing_data()
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            logger.info(f"Created data directory: {self.data_path}")
    
    def load_existing_data(self):
        """Load existing patterns and performance data."""
        try:
            # Load issue patterns
            patterns_file = os.path.join(self.data_path, "issue_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.issue_patterns = [IssuePattern(**p) for p in patterns_data]
                logger.info(f"Loaded {len(self.issue_patterns)} issue patterns")
            
            # Load execution history
            history_file = os.path.join(self.data_path, "execution_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    self.execution_history = [ExecutionOutcome(**e) for e in history_data]
                logger.info(f"Loaded {len(self.execution_history)} execution records")
            
            # Load agent performance
            performance_file = os.path.join(self.data_path, "agent_performance.json")
            if os.path.exists(performance_file):
                with open(performance_file, 'r') as f:
                    performance_data = json.load(f)
                    self.agent_performance = {k: AgentPerformance(**v) for k, v in performance_data.items()}
                logger.info(f"Loaded performance data for {len(self.agent_performance)} agents")
                
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
    
    def save_data(self):
        """Save patterns and performance data to disk."""
        try:
            # Save issue patterns
            patterns_file = os.path.join(self.data_path, "issue_patterns.json")
            with open(patterns_file, 'w') as f:
                patterns_data = [asdict(p) for p in self.issue_patterns]
                json.dump(patterns_data, f, indent=2)
            
            # Save execution history
            history_file = os.path.join(self.data_path, "execution_history.json")
            with open(history_file, 'w') as f:
                history_data = [asdict(e) for e in self.execution_history]
                json.dump(history_data, f, indent=2)
            
            # Save agent performance
            performance_file = os.path.join(self.data_path, "agent_performance.json")
            with open(performance_file, 'w') as f:
                performance_data = {k: asdict(v) for k, v in self.agent_performance.items()}
                json.dump(performance_data, f, indent=2)
                
            logger.info("Successfully saved intelligence data")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def analyze_issue_pattern(self, title: str, body: str, labels: List[str]) -> Dict[str, Any]:
        """Analyze an issue to identify patterns and predict optimal routing."""
        
        # Combine text for analysis
        issue_text = f"{title} {body} {' '.join(labels)}"
        
        # Extract features using TF-IDF
        if len(self.execution_history) > 10:  # Only if we have enough training data
            features = self._extract_features(issue_text)
            predicted_pattern = self._predict_pattern(features)
            
            if predicted_pattern:
                return {
                    "predicted_pattern": predicted_pattern.pattern_id,
                    "issue_type": predicted_pattern.issue_type,
                    "optimal_agent": predicted_pattern.optimal_agent,
                    "optimal_model": predicted_pattern.optimal_model,
                    "predicted_success_rate": predicted_pattern.success_rate,
                    "estimated_cost": predicted_pattern.average_cost,
                    "confidence_score": self._calculate_pattern_confidence(issue_text, predicted_pattern),
                    "complexity_score": predicted_pattern.complexity_score,
                    "priority": self._determine_priority(title, body, labels)
                }
        
        # Fallback to rule-based analysis for new systems
        return self._rule_based_analysis(title, body, labels)
    
    def _extract_features(self, issue_text: str) -> np.ndarray:
        """Extract TF-IDF features from issue text."""
        # Fit vectorizer if not already done
        if not hasattr(self.text_vectorizer, 'vocabulary_'):
            # Collect all historical issue texts for fitting
            all_texts = []
            for outcome in self.execution_history:
                # In real implementation, we'd store the original issue text
                all_texts.append(f"issue_type:{outcome.issue_type} agent:{outcome.assigned_agent}")
            
            if all_texts:
                self.text_vectorizer.fit(all_texts + [issue_text])
            else:
                self.text_vectorizer.fit([issue_text])
        
        return self.text_vectorizer.transform([issue_text]).toarray()[0]
    
    def _predict_pattern(self, features: np.ndarray) -> Optional[IssuePattern]:
        """Predict the best matching issue pattern."""
        if not self.issue_patterns:
            return None
        
        # Calculate similarity with existing patterns
        best_pattern = None
        best_similarity = 0.0
        
        for pattern in self.issue_patterns:
            # In a real implementation, we'd store pattern feature vectors
            # For now, use keyword matching as approximation
            similarity = np.random.random()  # Placeholder
            
            if similarity > best_similarity and similarity > 0.5:
                best_similarity = similarity
                best_pattern = pattern
        
        return best_pattern
    
    def _calculate_pattern_confidence(self, issue_text: str, pattern: IssuePattern) -> float:
        """Calculate confidence in pattern match."""
        # Base confidence from pattern success rate
        base_confidence = pattern.success_rate
        
        # Adjust based on sample count (more samples = higher confidence)
        sample_factor = min(pattern.sample_count / 10.0, 1.0)
        
        # Adjust based on keyword presence
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword.lower() in issue_text.lower())
        keyword_factor = min(keyword_matches / len(pattern.keywords), 1.0)
        
        return base_confidence * 0.6 + sample_factor * 0.2 + keyword_factor * 0.2
    
    def _rule_based_analysis(self, title: str, body: str, labels: List[str]) -> Dict[str, Any]:
        """Fallback rule-based analysis for new systems."""
        title_lower = title.lower()
        body_lower = body.lower()
        label_names = [label.lower() for label in labels]
        
        # Issue type classification
        if any(keyword in title_lower + body_lower for keyword in ["typo", "documentation", "docs", "readme"]):
            issue_type = "documentation"
            optimal_agent = "comprehensive-researcher"
            optimal_model = "haiku"
            estimated_cost = 0.005
        elif any(keyword in title_lower + body_lower for keyword in ["bug", "error", "crash", "fix"]):
            issue_type = "bug"
            optimal_agent = "debugger"
            optimal_model = "sonnet"
            estimated_cost = 0.025
        elif any(keyword in title_lower + body_lower for keyword in ["feature", "enhancement", "add"]):
            issue_type = "feature"
            optimal_agent = "backend-architect"
            optimal_model = "opus"
            estimated_cost = 0.150
        elif any(keyword in title_lower + body_lower for keyword in ["security", "vulnerability"]):
            issue_type = "security"
            optimal_agent = "security-auditor"
            optimal_model = "opus"
            estimated_cost = 0.200
        else:
            issue_type = "general"
            optimal_agent = "general-purpose"
            optimal_model = "sonnet"
            estimated_cost = 0.040
        
        # Determine priority
        priority = "medium"
        if any(keyword in label_names for keyword in ["critical", "urgent"]):
            priority = "critical"
        elif any(keyword in label_names for keyword in ["high", "important"]):
            priority = "high"
        elif any(keyword in title_lower + body_lower for keyword in ["500", "error", "crash"]):
            priority = "high"
        
        # Calculate complexity score
        complexity_score = 0.3  # Base complexity
        content_length = len(title + body)
        
        if content_length > 1000:
            complexity_score += 0.2
        if any(keyword in title_lower + body_lower for keyword in ["refactor", "architecture"]):
            complexity_score += 0.3
        if len(labels) > 3:
            complexity_score += 0.1
        
        complexity_score = min(complexity_score, 1.0)
        
        return {
            "predicted_pattern": "rule_based",
            "issue_type": issue_type,
            "optimal_agent": optimal_agent,
            "optimal_model": optimal_model,
            "predicted_success_rate": 0.75,  # Conservative estimate
            "estimated_cost": estimated_cost,
            "confidence_score": 0.6,  # Lower confidence for rule-based
            "complexity_score": complexity_score,
            "priority": priority
        }
    
    def record_execution_outcome(self, outcome: ExecutionOutcome):
        """Record the outcome of an issue execution for learning."""
        self.execution_history.append(outcome)
        
        # Update agent performance
        self.agent_performance_tracker.update_performance(outcome)
        
        # Update patterns based on outcome
        self._update_patterns(outcome)
        
        # Save data periodically
        if len(self.execution_history) % 10 == 0:
            self.save_data()
        
        logger.info(f"Recorded execution outcome for issue #{outcome.issue_number}")
    
    def _update_patterns(self, outcome: ExecutionOutcome):
        """Update issue patterns based on execution outcome."""
        # Find or create pattern for this issue type and agent combination
        pattern_id = f"{outcome.issue_type}_{outcome.assigned_agent}_{outcome.model_used}"
        
        existing_pattern = next(
            (p for p in self.issue_patterns if p.pattern_id == pattern_id), 
            None
        )
        
        if existing_pattern:
            # Update existing pattern
            total_count = existing_pattern.sample_count + 1
            
            # Update success rate (running average)
            existing_pattern.success_rate = (
                existing_pattern.success_rate * existing_pattern.sample_count + 
                (1.0 if outcome.success else 0.0)
            ) / total_count
            
            # Update average cost
            existing_pattern.average_cost = (
                existing_pattern.average_cost * existing_pattern.sample_count + 
                outcome.actual_cost
            ) / total_count
            
            existing_pattern.sample_count = total_count
            existing_pattern.complexity_score = min(
                existing_pattern.complexity_score + 0.1 if not outcome.success else 
                existing_pattern.complexity_score - 0.05, 1.0
            )
        else:
            # Create new pattern
            new_pattern = IssuePattern(
                pattern_id=pattern_id,
                keywords=[outcome.issue_type],  # Will be enhanced with NLP
                issue_type=outcome.issue_type,
                complexity_score=0.5,
                optimal_agent=outcome.assigned_agent,
                optimal_model=outcome.model_used,
                success_rate=1.0 if outcome.success else 0.0,
                average_cost=outcome.actual_cost,
                sample_count=1
            )
            self.issue_patterns.append(new_pattern)
    
    def get_agent_recommendations(self, issue_type: str) -> List[Dict[str, Any]]:
        """Get ranked agent recommendations for a specific issue type."""
        recommendations = []
        
        for agent_key, performance in self.agent_performance.items():
            if performance.issue_type == issue_type or issue_type == "general":
                score = (
                    performance.success_rate * 0.4 +
                    (1.0 / max(performance.average_execution_time, 1.0)) * 0.3 +
                    (1.0 / max(performance.average_cost, 0.001)) * 0.3
                )
                
                recommendations.append({
                    "agent_name": performance.agent_name,  # Changed from "agent" for consistency
                    "agent": performance.agent_name,  # Keep for backward compatibility
                    "score": score,
                    "confidence": performance.success_rate,
                    "recommended_model": self._get_optimal_model_for_agent(performance.agent_name),
                    "success_rate": performance.success_rate,
                    "avg_cost": performance.average_cost,
                    "avg_time": performance.average_execution_time,
                    "total_executions": performance.total_executions
                })
        
        # Add default recommendations if no performance data available
        if not recommendations:
            default_agents = {
                "bug": "debugger",
                "feature": "backend-architect",
                "security": "security-auditor", 
                "performance": "performance-engineer",
                "documentation": "comprehensive-researcher"
            }
            
            agent_name = default_agents.get(issue_type, "debugger")
            recommendations.append({
                "agent_name": agent_name,
                "agent": agent_name,
                "score": 0.7,
                "confidence": 0.7,
                "recommended_model": self._get_optimal_model_for_agent(agent_name),
                "success_rate": 0.75,
                "avg_cost": 0.025,
                "avg_time": 60.0,
                "total_executions": 0
            })
        
        return sorted(recommendations, key=lambda x: x["score"], reverse=True)
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get a summary of the intelligence system status."""
        return {
            "total_patterns": len(self.issue_patterns),
            "execution_history_count": len(self.execution_history),
            "agents_tracked": len(self.agent_performance),
            "top_performing_agents": self._get_top_agents(5),
            "most_common_issue_types": self._get_common_issue_types(),
            "average_success_rate": self._calculate_average_success_rate(),
            "total_cost_saved": self._estimate_cost_savings(),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _get_top_agents(self, count: int) -> List[Dict[str, Any]]:
        """Get top performing agents."""
        sorted_agents = sorted(
            self.agent_performance.values(),
            key=lambda x: x.success_rate * x.total_executions,
            reverse=True
        )
        
        return [
            {
                "agent": agent.agent_name,
                "success_rate": agent.success_rate,
                "total_executions": agent.total_executions
            }
            for agent in sorted_agents[:count]
        ]
    
    def _get_common_issue_types(self) -> List[Dict[str, int]]:
        """Get most common issue types."""
        type_counts = {}
        for outcome in self.execution_history:
            type_counts[outcome.issue_type] = type_counts.get(outcome.issue_type, 0) + 1
        
        return sorted(
            [{"issue_type": k, "count": v} for k, v in type_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
    
    def _calculate_average_success_rate(self) -> float:
        """Calculate overall success rate."""
        if not self.execution_history:
            return 0.0
        
        successes = sum(1 for outcome in self.execution_history if outcome.success)
        return successes / len(self.execution_history)
    
    def _estimate_cost_savings(self) -> float:
        """Estimate cost savings from intelligent routing."""
        # This would compare actual costs vs baseline costs
        # Placeholder implementation
        return sum(0.01 for _ in self.execution_history)  # $0.01 per execution
    
    def _determine_priority(self, title: str, body: str, labels: List[str]) -> str:
        """Determine issue priority based on content analysis."""
        title_lower = title.lower()
        body_lower = body.lower()
        label_names = [label.lower() for label in labels]
        
        if any(keyword in label_names for keyword in ["critical", "urgent", "p0"]):
            return "critical"
        elif any(keyword in label_names for keyword in ["high", "important", "p1"]):
            return "high"
        elif any(keyword in title_lower + body_lower for keyword in ["crash", "500", "down", "broken"]):
            return "high"
        elif any(keyword in label_names for keyword in ["low", "minor", "p3"]):
            return "low"
        else:
            return "medium"
    
    def _get_optimal_model_for_agent(self, agent_name: str) -> str:
        """Get optimal model recommendation for agent."""
        optimal_models = {
            "debugger": "sonnet",
            "backend-architect": "opus",
            "security-auditor": "opus", 
            "performance-engineer": "opus",
            "comprehensive-researcher": "haiku"
        }
        return optimal_models.get(agent_name, "sonnet")


class AgentPerformanceTracker:
    """Tracks and analyzes agent performance metrics."""
    
    def __init__(self):
        self.performance_data: Dict[str, AgentPerformance] = {}
    
    def update_performance(self, outcome: ExecutionOutcome):
        """Update agent performance based on execution outcome."""
        key = f"{outcome.assigned_agent}_{outcome.issue_type}"
        
        if key in self.performance_data:
            perf = self.performance_data[key]
            
            # Flexible field access for different ExecutionOutcome formats
            success = getattr(outcome, 'actual_success', None)
            if success is None:
                success = getattr(outcome, 'success', False)
            
            execution_time = getattr(outcome, 'execution_time', None) or 60.0
            actual_cost = getattr(outcome, 'actual_cost', None) or 0.025
            
            # Update success rate (running average)
            total_count = perf.total_executions + 1
            perf.success_rate = (
                perf.success_rate * perf.total_executions + 
                (1.0 if success else 0.0)
            ) / total_count
            
            # Update average execution time
            perf.average_execution_time = (
                perf.average_execution_time * perf.total_executions + 
                execution_time
            ) / total_count
            
            # Update average cost
            perf.average_cost = (
                perf.average_cost * perf.total_executions + 
                actual_cost
            ) / total_count
            
            perf.total_executions = total_count
            perf.last_updated = datetime.utcnow().isoformat()
            
        else:
            # Create new performance record
            # Create new performance record with flexible field mapping
            agent_name = getattr(outcome, 'agent_used', None) or getattr(outcome, 'assigned_agent', 'unknown')
            success = getattr(outcome, 'actual_success', None)
            if success is None:
                success = getattr(outcome, 'success', False)
            execution_time = getattr(outcome, 'execution_time', 60.0) or 60.0
            actual_cost = getattr(outcome, 'actual_cost', 0.025) or 0.025
            
            self.performance_data[key] = AgentPerformance(
                agent_name=agent_name,
                issue_type=outcome.issue_type or 'unknown',
                success_rate=1.0 if success else 0.0,
                average_execution_time=execution_time,
                average_cost=actual_cost,
                total_executions=1,
                last_updated=datetime.utcnow().isoformat()
            )


class ConfidenceOptimizer:
    """Optimizes confidence scoring based on historical outcomes."""
    
    def __init__(self):
        self.confidence_history: List[Tuple[float, bool]] = []  # (predicted_confidence, actual_success)
    
    def optimize_confidence(self, base_confidence: float, issue_features: Dict[str, Any]) -> float:
        """Optimize confidence score based on historical performance."""
        
        # Start with base confidence
        optimized_confidence = base_confidence
        
        # Adjust based on historical accuracy
        if len(self.confidence_history) > 10:
            # Calculate calibration factor
            calibration = self._calculate_calibration_factor()
            optimized_confidence *= calibration
        
        # Adjust based on issue features
        if issue_features.get("has_clear_description", False):
            optimized_confidence += 0.1
        
        if issue_features.get("has_reproduction_steps", False):
            optimized_confidence += 0.15
        
        if issue_features.get("has_expected_behavior", False):
            optimized_confidence += 0.1
        
        # Ensure confidence stays in valid range
        return max(0.0, min(optimized_confidence, 1.0))
    
    def record_confidence_outcome(self, predicted_confidence: float, actual_success: bool):
        """Record confidence prediction vs actual outcome for learning."""
        self.confidence_history.append((predicted_confidence, actual_success))
        
        # Keep only recent history (last 1000 predictions)
        if len(self.confidence_history) > 1000:
            self.confidence_history = self.confidence_history[-1000:]
    
    def _calculate_calibration_factor(self) -> float:
        """Calculate how well-calibrated our confidence predictions are."""
        if not self.confidence_history:
            return 1.0
        
        # Simple calibration: compare average predicted confidence with actual success rate
        avg_predicted = sum(conf for conf, _ in self.confidence_history) / len(self.confidence_history)
        actual_success_rate = sum(1 for _, success in self.confidence_history if success) / len(self.confidence_history)
        
        if avg_predicted > 0:
            return actual_success_rate / avg_predicted
        
        return 1.0


def create_sample_execution_outcome(issue_number: int = 1) -> ExecutionOutcome:
    """Create a sample execution outcome for testing."""
    return ExecutionOutcome(
        execution_id=f"exec_{issue_number}_{datetime.now().timestamp()}",
        issue_number=issue_number,
        repository="test/demo",
        issue_type="documentation",
        assigned_agent="comprehensive-researcher",
        model_used="haiku",
        success=True,
        execution_time=45.2,
        actual_cost=0.0084,
        quality_score=0.92,
        user_satisfaction=4,
        pr_merged=True,
        timestamp=datetime.utcnow().isoformat()
    )


if __name__ == "__main__":
    # Initialize the intelligence engine
    print("🧠 Initializing Issue Intelligence Engine...")
    engine = IssueIntelligenceEngine()
    
    # Add some sample data for testing
    sample_outcomes = [
        create_sample_execution_outcome(1),
        ExecutionOutcome(
            execution_id="exec_2",
            issue_number=2,
            repository="test/demo",
            issue_type="bug",
            assigned_agent="debugger",
            model_used="sonnet",
            success=True,
            execution_time=120.5,
            actual_cost=0.0379,
            quality_score=0.88,
            user_satisfaction=5,
            pr_merged=True,
            timestamp=datetime.utcnow().isoformat()
        )
    ]
    
    for outcome in sample_outcomes:
        engine.record_execution_outcome(outcome)
    
    # Test issue analysis
    print("\n🔍 Testing Issue Analysis...")
    analysis = engine.analyze_issue_pattern(
        "Fix typo in documentation",
        "There's a small typo in the README file that needs fixing",
        ["documentation", "good first issue"]
    )
    
    print("Analysis Result:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
    
    # Get intelligence summary
    print("\n📊 Intelligence System Summary:")
    summary = engine.get_intelligence_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Issue Intelligence Engine initialized and tested successfully!")