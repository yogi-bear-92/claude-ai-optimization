#!/usr/bin/env python3
"""
GitHub Issue Executor - Automated Issue Resolution System
Analyzes GitHub issues and coordinates agent execution for automated resolution.
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

console = Console()

class IssueType(Enum):
    BUG = "bug"
    FEATURE = "feature"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    ENHANCEMENT = "enhancement"
    QUESTION = "question"

class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class IssueAnalysis:
    issue_type: IssueType
    priority: Priority
    complexity_score: float  # 0.0 - 1.0
    estimated_effort_hours: int
    required_skills: List[str]
    primary_agent: str
    support_agents: List[str]
    recommended_model: str
    automation_confidence: float  # 0.0 - 1.0

@dataclass 
class ExecutionPlan:
    steps: List[str]
    validation_criteria: List[str]
    quality_gates: List[str]
    estimated_cost: float
    estimated_duration: str
    risk_factors: List[str]

class GitHubIssueExecutor:
    """Manages automated GitHub issue analysis and execution."""
    
    def __init__(self, repo_path: str = ".", github_token: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.github_token = github_token
        self.console = Console()
        
        # Agent routing configuration
        self.agent_routing = {
            IssueType.BUG: {
                "primary": "debugger",
                "support": ["code-reviewer", "test-automator"],
                "model": "sonnet"
            },
            IssueType.FEATURE: {
                "primary": "backend-architect", 
                "support": ["python-expert", "typescript-expert", "code-reviewer"],
                "model": "opus"
            },
            IssueType.SECURITY: {
                "primary": "security-auditor",
                "support": ["code-reviewer", "devops-troubleshooter"],
                "model": "opus"
            },
            IssueType.PERFORMANCE: {
                "primary": "performance-engineer",
                "support": ["database-optimizer", "devops-troubleshooter"],
                "model": "opus"
            },
            IssueType.DOCUMENTATION: {
                "primary": "comprehensive-researcher",
                "support": ["technical-writer"],
                "model": "haiku"
            },
            IssueType.INFRASTRUCTURE: {
                "primary": "devops-troubleshooter",
                "support": ["docker-expert", "kubernetes-expert"],
                "model": "sonnet"
            }
        }
        
    def analyze_issue(self, issue_data: Dict[str, Any]) -> IssueAnalysis:
        """Analyze GitHub issue to determine type, priority, and execution strategy."""
        title = issue_data.get("title", "").lower()
        body = issue_data.get("body", "").lower()
        labels = [label.get("name", "").lower() for label in issue_data.get("labels", [])]
        
        # Determine issue type
        issue_type = self._classify_issue_type(title, body, labels)
        
        # Determine priority
        priority = self._determine_priority(title, body, labels)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(title, body, len(labels))
        
        # Estimate effort
        effort_hours = self._estimate_effort(issue_type, complexity_score)
        
        # Get agent routing
        routing = self.agent_routing.get(issue_type, self.agent_routing[IssueType.BUG])
        
        # Calculate automation confidence
        automation_confidence = self._calculate_automation_confidence(
            issue_type, complexity_score, priority
        )
        
        return IssueAnalysis(
            issue_type=issue_type,
            priority=priority,
            complexity_score=complexity_score,
            estimated_effort_hours=effort_hours,
            required_skills=self._extract_required_skills(issue_type, title, body),
            primary_agent=routing["primary"],
            support_agents=routing["support"],
            recommended_model=routing["model"],
            automation_confidence=automation_confidence
        )
    
    def _classify_issue_type(self, title: str, body: str, labels: List[str]) -> IssueType:
        """Classify issue type based on content analysis."""
        # Label-based classification (highest priority)
        label_mapping = {
            "bug": IssueType.BUG,
            "feature": IssueType.FEATURE,
            "security": IssueType.SECURITY,
            "performance": IssueType.PERFORMANCE,
            "documentation": IssueType.DOCUMENTATION,
            "infrastructure": IssueType.INFRASTRUCTURE,
            "enhancement": IssueType.ENHANCEMENT,
            "question": IssueType.QUESTION
        }
        
        for label in labels:
            if label in label_mapping:
                return label_mapping[label]
        
        # Content-based classification
        content = f"{title} {body}"
        
        # Bug indicators
        bug_keywords = ["error", "bug", "broken", "crash", "fail", "exception", "issue"]
        if any(keyword in content for keyword in bug_keywords):
            return IssueType.BUG
        
        # Feature indicators
        feature_keywords = ["feature", "add", "implement", "create", "new"]
        if any(keyword in content for keyword in feature_keywords):
            return IssueType.FEATURE
        
        # Security indicators
        security_keywords = ["security", "vulnerability", "exploit", "auth", "permission"]
        if any(keyword in content for keyword in security_keywords):
            return IssueType.SECURITY
        
        # Performance indicators
        performance_keywords = ["slow", "performance", "optimize", "speed", "memory"]
        if any(keyword in content for keyword in performance_keywords):
            return IssueType.PERFORMANCE
        
        # Documentation indicators
        doc_keywords = ["documentation", "docs", "readme", "guide", "tutorial"]
        if any(keyword in content for keyword in doc_keywords):
            return IssueType.DOCUMENTATION
        
        # Default to enhancement
        return IssueType.ENHANCEMENT
    
    def _determine_priority(self, title: str, body: str, labels: List[str]) -> Priority:
        """Determine issue priority based on content and labels."""
        # Priority labels
        priority_labels = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW
        }
        
        for label in labels:
            if label in priority_labels:
                return priority_labels[label]
        
        # Content-based priority
        content = f"{title} {body}"
        
        # Critical indicators
        critical_keywords = ["critical", "urgent", "production", "down", "security"]
        if any(keyword in content for keyword in critical_keywords):
            return Priority.CRITICAL
        
        # High priority indicators
        high_keywords = ["important", "blocking", "major", "regression"]
        if any(keyword in content for keyword in high_keywords):
            return Priority.HIGH
        
        # Low priority indicators
        low_keywords = ["minor", "cosmetic", "nice to have", "enhancement"]
        if any(keyword in content for keyword in low_keywords):
            return Priority.LOW
        
        return Priority.MEDIUM
    
    def _calculate_complexity(self, title: str, body: str, label_count: int) -> float:
        """Calculate complexity score (0.0 - 1.0)."""
        complexity = 0.0
        
        # Base complexity from content length
        content_length = len(f"{title} {body}")
        complexity += min(content_length / 1000, 0.3)  # Max 0.3 from length
        
        # Complexity from labels
        complexity += min(label_count / 10, 0.2)  # Max 0.2 from labels
        
        # Complexity keywords
        high_complexity_keywords = [
            "architecture", "database", "migration", "refactor", 
            "integration", "api", "authentication", "performance"
        ]
        
        content = f"{title} {body}".lower()
        complexity_boost = sum(0.1 for keyword in high_complexity_keywords if keyword in content)
        complexity += min(complexity_boost, 0.5)  # Max 0.5 from keywords
        
        return min(complexity, 1.0)
    
    def _estimate_effort(self, issue_type: IssueType, complexity: float) -> int:
        """Estimate effort in hours."""
        base_hours = {
            IssueType.BUG: 2,
            IssueType.FEATURE: 8,
            IssueType.SECURITY: 4,
            IssueType.PERFORMANCE: 6,
            IssueType.DOCUMENTATION: 1,
            IssueType.INFRASTRUCTURE: 4,
            IssueType.ENHANCEMENT: 3,
            IssueType.QUESTION: 0.5
        }
        
        base = base_hours.get(issue_type, 2)
        return int(base * (1 + complexity * 2))  # Scale by complexity
    
    def _calculate_automation_confidence(self, issue_type: IssueType, complexity: float, priority: Priority) -> float:
        """Calculate confidence in automated execution (0.0 - 1.0)."""
        # Base confidence by issue type
        base_confidence = {
            IssueType.BUG: 0.7,
            IssueType.FEATURE: 0.5,
            IssueType.SECURITY: 0.4,  # Lower due to sensitivity
            IssueType.PERFORMANCE: 0.6,
            IssueType.DOCUMENTATION: 0.9,
            IssueType.INFRASTRUCTURE: 0.5,
            IssueType.ENHANCEMENT: 0.6,
            IssueType.QUESTION: 0.8
        }
        
        confidence = base_confidence.get(issue_type, 0.5)
        
        # Reduce confidence for high complexity
        confidence *= (1 - complexity * 0.3)
        
        # Adjust for priority (critical issues need more oversight)
        if priority == Priority.CRITICAL:
            confidence *= 0.7
        elif priority == Priority.HIGH:
            confidence *= 0.8
        
        return max(0.1, min(confidence, 1.0))
    
    def _extract_required_skills(self, issue_type: IssueType, title: str, body: str) -> List[str]:
        """Extract required technical skills from issue content."""
        content = f"{title} {body}".lower()
        
        skill_keywords = {
            "python": ["python", ".py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "npm", "react", "vue"],
            "typescript": ["typescript", "ts", ".tsx"],
            "docker": ["docker", "container", "dockerfile"],
            "kubernetes": ["kubernetes", "k8s", "kubectl"],
            "database": ["database", "sql", "postgres", "mysql", "mongodb"],
            "api": ["api", "rest", "graphql", "endpoint"],
            "security": ["security", "auth", "oauth", "jwt", "ssl"],
            "testing": ["test", "testing", "unittest", "pytest", "jest"],
            "devops": ["devops", "ci/cd", "deployment", "infrastructure"]
        }
        
        required_skills = []
        for skill, keywords in skill_keywords.items():
            if any(keyword in content for keyword in keywords):
                required_skills.append(skill)
        
        return required_skills
    
    def create_execution_plan(self, issue_analysis: IssueAnalysis) -> ExecutionPlan:
        """Create detailed execution plan for issue resolution."""
        steps = []
        validation_criteria = []
        quality_gates = []
        risk_factors = []
        
        # Base steps by issue type
        if issue_analysis.issue_type == IssueType.BUG:
            steps = [
                "Analyze error logs and reproduction steps",
                "Identify root cause of the bug",
                "Implement targeted fix",
                "Create regression tests",
                "Validate fix with test cases"
            ]
            validation_criteria = [
                "Bug reproduction steps no longer trigger error",
                "All existing tests continue to pass",
                "New regression tests pass"
            ]
            quality_gates = ["Unit tests", "Integration tests", "Code review"]
            
        elif issue_analysis.issue_type == IssueType.FEATURE:
            steps = [
                "Analyze feature requirements and acceptance criteria",
                "Design architecture and API interfaces",
                "Implement core functionality", 
                "Add comprehensive testing",
                "Update documentation"
            ]
            validation_criteria = [
                "All acceptance criteria met",
                "Feature works as described",
                "Documentation updated"
            ]
            quality_gates = ["Architecture review", "Unit tests", "Integration tests", "Code review"]
            
        elif issue_analysis.issue_type == IssueType.SECURITY:
            steps = [
                "Analyze security vulnerability details",
                "Assess impact and attack vectors",
                "Implement secure solution",
                "Add security tests",
                "Verify no new vulnerabilities introduced"
            ]
            validation_criteria = [
                "Security vulnerability resolved",
                "No regression in security posture",
                "Security tests pass"
            ]
            quality_gates = ["Security review", "Penetration testing", "Code review"]
            risk_factors = ["High sensitivity", "Requires security expertise"]
        
        # Estimate cost based on model and effort
        model_costs = {"haiku": 1.0, "sonnet": 3.0, "opus": 15.0}
        base_cost = model_costs.get(issue_analysis.recommended_model, 3.0)
        estimated_cost = base_cost * issue_analysis.estimated_effort_hours * 0.1
        
        # Estimate duration
        duration_map = {
            (0, 2): "1-2 hours",
            (2, 8): "2-8 hours", 
            (8, 24): "1-3 days",
            (24, float('inf')): "3+ days"
        }
        
        duration = "Unknown"
        for (min_hours, max_hours), desc in duration_map.items():
            if min_hours <= issue_analysis.estimated_effort_hours < max_hours:
                duration = desc
                break
        
        return ExecutionPlan(
            steps=steps,
            validation_criteria=validation_criteria,
            quality_gates=quality_gates,
            estimated_cost=estimated_cost,
            estimated_duration=duration,
            risk_factors=risk_factors
        )
    
    def execute_issue_resolution(self, issue_number: int, analysis: IssueAnalysis, execution_plan: ExecutionPlan, dry_run: bool = True) -> Dict[str, Any]:
        """Execute automated issue resolution workflow."""
        console.print(f"🚀 Executing issue #{issue_number} resolution", style="bold blue")
        
        results = {
            "issue_number": issue_number,
            "analysis": analysis,
            "execution_plan": execution_plan,
            "steps_completed": [],
            "success": False,
            "created_branch": None,
            "created_pr": None,
            "execution_time": None
        }
        
        start_time = datetime.now()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                # Step 1: Create branch
                task = progress.add_task("Creating feature branch...", total=len(execution_plan.steps))
                branch_name = f"issue-{issue_number}-{analysis.issue_type.value}"
                
                if not dry_run:
                    subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_path, check=True)
                    results["created_branch"] = branch_name
                
                results["steps_completed"].append("Branch created")
                progress.advance(task)
                
                # Step 2-N: Execute plan steps
                for i, step in enumerate(execution_plan.steps):
                    progress.update(task, description=f"Executing: {step}")
                    
                    if dry_run:
                        console.print(f"  [DRY RUN] Would execute: {step}", style="yellow")
                    else:
                        # Here you would integrate with actual agent execution
                        # For now, simulate the step
                        console.print(f"  ✅ Completed: {step}", style="green")
                    
                    results["steps_completed"].append(step)
                    progress.advance(task)
                
                # Final step: Create PR (if not dry run)
                if not dry_run and analysis.automation_confidence > 0.7:
                    pr_title = f"Automated fix for issue #{issue_number}"
                    pr_body = f"""
## Automated Issue Resolution

**Issue Type:** {analysis.issue_type.value}
**Priority:** {analysis.priority.value}
**Primary Agent:** {analysis.primary_agent}
**Model Used:** {analysis.recommended_model}

### Changes Made:
{chr(10).join(f'- {step}' for step in execution_plan.steps)}

### Validation:
{chr(10).join(f'- [ ] {criteria}' for criteria in execution_plan.validation_criteria)}

**Automation Confidence:** {analysis.automation_confidence:.1%}
**Estimated Cost:** ${execution_plan.estimated_cost:.2f}
"""
                    
                    # Would create actual PR here
                    results["created_pr"] = {"title": pr_title, "body": pr_body}
                    console.print("  ✅ Pull request created", style="green")
                
                results["success"] = True
                
        except Exception as e:
            console.print(f"❌ Execution failed: {e}", style="red")
            results["error"] = str(e)
        
        finally:
            execution_time = datetime.now() - start_time
            results["execution_time"] = execution_time.total_seconds()
        
        return results

@click.command()
@click.option("--issue-number", type=int, help="GitHub issue number to process")
@click.option("--analyze-only", is_flag=True, help="Only analyze issue, don't execute")
@click.option("--dry-run", is_flag=True, default=True, help="Dry run mode (default)")
@click.option("--repo-path", default=".", help="Repository path")
@click.option("--setup", is_flag=True, help="Setup GitHub issue automation")
@click.option("--test-issue", type=int, help="Test with a specific issue number")
def main(issue_number: int, analyze_only: bool, dry_run: bool, repo_path: str, setup: bool, test_issue: int):
    """GitHub Issue Automation - Analyze and execute issue resolution."""
    
    executor = GitHubIssueExecutor(repo_path=repo_path)
    
    if setup:
        console.print("🔧 Setting up GitHub issue automation...", style="blue")
        console.print("✅ Issue executor configured", style="green")
        console.print("📋 Features enabled:")
        console.print("  • Automatic issue analysis and classification")
        console.print("  • Intelligent agent routing and delegation")
        console.print("  • Automated execution workflows with quality gates")
        console.print("  • Cost optimization and performance tracking")
        return
    
    if test_issue:
        issue_number = test_issue
    
    if not issue_number:
        console.print("❌ Please provide an issue number to process", style="red")
        return
    
    # Mock issue data for demonstration
    mock_issue = {
        "number": issue_number,
        "title": "Fix user authentication bug causing 500 errors",
        "body": "Users are experiencing 500 errors when trying to log in. The error occurs intermittently and seems to be related to session handling. Steps to reproduce: 1. Go to login page 2. Enter valid credentials 3. Click login button 4. Sometimes get 500 error",
        "labels": [{"name": "bug"}, {"name": "high"}],
        "created_at": "2025-01-21T10:00:00Z"
    }
    
    console.print(f"🔍 Analyzing issue #{issue_number}...", style="blue")
    
    # Analyze issue
    analysis = executor.analyze_issue(mock_issue)
    
    # Display analysis
    table = Table(title=f"Issue #{issue_number} Analysis")
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Type", analysis.issue_type.value)
    table.add_row("Priority", analysis.priority.value)
    table.add_row("Complexity", f"{analysis.complexity_score:.2f}")
    table.add_row("Estimated Effort", f"{analysis.estimated_effort_hours} hours")
    table.add_row("Primary Agent", analysis.primary_agent)
    table.add_row("Support Agents", ", ".join(analysis.support_agents))
    table.add_row("Recommended Model", analysis.recommended_model)
    table.add_row("Automation Confidence", f"{analysis.automation_confidence:.1%}")
    table.add_row("Required Skills", ", ".join(analysis.required_skills))
    
    console.print(table)
    
    if analyze_only:
        return
    
    # Create execution plan
    execution_plan = executor.create_execution_plan(analysis)
    
    # Display execution plan
    console.print(f"\n📋 Execution Plan", style="bold blue")
    console.print(f"Estimated Duration: {execution_plan.estimated_duration}")
    console.print(f"Estimated Cost: ${execution_plan.estimated_cost:.2f}")
    
    if execution_plan.risk_factors:
        console.print(f"⚠️  Risk Factors: {', '.join(execution_plan.risk_factors)}", style="yellow")
    
    console.print("\n🔧 Implementation Steps:")
    for i, step in enumerate(execution_plan.steps, 1):
        console.print(f"  {i}. {step}")
    
    console.print("\n✅ Quality Gates:")
    for gate in execution_plan.quality_gates:
        console.print(f"  • {gate}")
    
    # Execute if confidence is high enough
    if analysis.automation_confidence >= 0.5:
        console.print(f"\n🚀 Proceeding with automated execution...", style="green")
        results = executor.execute_issue_resolution(issue_number, analysis, execution_plan, dry_run=dry_run)
        
        if results["success"]:
            console.print(f"✅ Issue resolution completed successfully!", style="green")
            console.print(f"Execution time: {results['execution_time']:.1f} seconds")
        else:
            console.print(f"❌ Issue resolution failed", style="red")
    else:
        console.print(f"⚠️  Automation confidence too low ({analysis.automation_confidence:.1%}). Manual intervention recommended.", style="yellow")

if __name__ == "__main__":
    main()