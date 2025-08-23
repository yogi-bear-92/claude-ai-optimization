#!/usr/bin/env python3
"""
Analyze Pull Request for Smart Auto-Merge Eligibility
Integrates with the Azure Issue Automation Intelligence Engine
"""
import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
import subprocess
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PRAutoMergeAnalyzer:
    """Analyze PR for auto-merge eligibility using AI intelligence."""
    
    def __init__(self, pr_number: int, repository: str, github_token: str):
        self.pr_number = pr_number
        self.repository = repository
        self.github_token = github_token
        self.analysis_result = {
            "should_auto_merge": False,
            "ai_confidence": 0,
            "risk_score": 10,  # Start with highest risk
            "merge_strategy": "squash",
            "analysis_summary": "",
            "safety_checks": {},
            "decision_factors": {}
        }
        
        # Load intelligence engine if available
        try:
            sys.path.append('.')
            from issue_intelligence import IssueIntelligenceEngine
            self.intelligence_engine = IssueIntelligenceEngine()
            logger.info("✅ Intelligence engine loaded successfully")
        except ImportError:
            self.intelligence_engine = None
            logger.warning("⚠️ Intelligence engine not available, using rule-based analysis")
    
    def analyze_pr(self) -> Dict[str, Any]:
        """Perform comprehensive PR analysis for auto-merge decision."""
        logger.info(f"🔍 Analyzing PR #{self.pr_number} for auto-merge eligibility")
        
        # Get PR details
        pr_data = self._get_pr_details()
        if not pr_data:
            return self.analysis_result
        
        # Perform multi-dimensional analysis
        self._analyze_code_changes(pr_data)
        self._analyze_pr_metadata(pr_data)
        self._analyze_author_trust(pr_data)
        self._analyze_file_safety(pr_data)
        self._analyze_complexity(pr_data)
        self._analyze_testing_coverage(pr_data)
        
        # Use AI intelligence if available
        if self.intelligence_engine:
            self._analyze_with_intelligence(pr_data)
        
        # Make final decision
        self._make_merge_decision()
        
        # Output results for GitHub Actions
        self._output_results()
        
        return self.analysis_result
    
    def _get_pr_details(self) -> Dict[str, Any]:
        """Get PR details from GitHub API."""
        try:
            import requests
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get PR details
            pr_url = f"https://api.github.com/repos/{self.repository}/pulls/{self.pr_number}"
            response = requests.get(pr_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to get PR details: {response.status_code}")
                return {}
            
            pr_data = response.json()
            
            # Get PR files
            files_url = f"{pr_url}/files"
            files_response = requests.get(files_url, headers=headers)
            
            if files_response.status_code == 200:
                pr_data['files'] = files_response.json()
            else:
                pr_data['files'] = []
            
            # Get PR commits
            commits_url = f"{pr_url}/commits"
            commits_response = requests.get(commits_url, headers=headers)
            
            if commits_response.status_code == 200:
                pr_data['commits'] = commits_response.json()
            else:
                pr_data['commits'] = []
            
            return pr_data
            
        except Exception as e:
            logger.error(f"❌ Error getting PR details: {e}")
            return {}
    
    def _analyze_code_changes(self, pr_data: Dict[str, Any]) -> None:
        """Analyze the code changes for risk assessment."""
        files_changed = pr_data.get('files', [])
        
        analysis = {
            "files_changed": len(files_changed),
            "lines_added": 0,
            "lines_deleted": 0,
            "high_risk_files": [],
            "safe_files": [],
            "change_types": {
                "documentation": 0,
                "tests": 0,
                "configuration": 0,
                "source_code": 0,
                "dependencies": 0
            }
        }
        
        # Define risk patterns
        high_risk_patterns = [
            r'\.py$',  # Python source files
            r'Dockerfile',  # Container configurations
            r'requirements.*\.txt$',  # Dependencies
            r'\.yml$|\.yaml$',  # Workflow/config files
            r'app-simple\.py$',  # Main application file
            r'issue_intelligence\.py$',  # Intelligence engine
        ]
        
        safe_patterns = [
            r'README\.md$',
            r'\.md$',  # Documentation
            r'test_.*\.py$',  # Test files
            r'.*_test\.py$',
            r'tests/.*',
            r'docs/.*',
            r'\.gitignore$',
            r'LICENSE$'
        ]
        
        for file_info in files_changed:
            filename = file_info.get('filename', '')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            
            analysis["lines_added"] += additions
            analysis["lines_deleted"] += deletions
            
            # Categorize file changes
            if any(re.search(pattern, filename) for pattern in safe_patterns):
                analysis["safe_files"].append(filename)
                if filename.endswith('.md'):
                    analysis["change_types"]["documentation"] += 1
                elif 'test' in filename.lower():
                    analysis["change_types"]["tests"] += 1
            elif any(re.search(pattern, filename) for pattern in high_risk_patterns):
                analysis["high_risk_files"].append(filename)
                if filename.endswith('.py'):
                    analysis["change_types"]["source_code"] += 1
                elif 'requirements' in filename:
                    analysis["change_types"]["dependencies"] += 1
                elif filename.endswith(('.yml', '.yaml')):
                    analysis["change_types"]["configuration"] += 1
            else:
                # Unknown file type - treat as medium risk
                if filename.endswith('.py'):
                    analysis["change_types"]["source_code"] += 1
                else:
                    analysis["change_types"]["configuration"] += 1
        
        # Calculate risk based on changes
        risk_factors = []
        confidence_factors = []
        
        # Large changes are riskier
        total_changes = analysis["lines_added"] + analysis["lines_deleted"]
        if total_changes > 500:
            risk_factors.append(("Large changeset", 3))
        elif total_changes > 100:
            risk_factors.append(("Medium changeset", 1))
        else:
            confidence_factors.append(("Small changeset", 2))
        
        # High-risk files
        if analysis["high_risk_files"]:
            risk_factors.append((f"High-risk files: {len(analysis['high_risk_files'])}", 2))
        
        # Safe files boost confidence
        if analysis["safe_files"]:
            confidence_factors.append((f"Safe files: {len(analysis['safe_files'])}", 1))
        
        # Documentation-only changes are very safe
        if (analysis["change_types"]["documentation"] > 0 and
            analysis["change_types"]["source_code"] == 0 and
            analysis["change_types"]["configuration"] == 0):
            confidence_factors.append(("Documentation-only changes", 5))
        
        self.analysis_result["decision_factors"]["code_changes"] = analysis
        self.analysis_result["decision_factors"]["risk_factors"] = risk_factors
        self.analysis_result["decision_factors"]["confidence_factors"] = confidence_factors
    
    def _analyze_pr_metadata(self, pr_data: Dict[str, Any]) -> None:
        """Analyze PR metadata for trust indicators."""
        analysis = {
            "title": pr_data.get('title', ''),
            "body": pr_data.get('body', '') or '',
            "labels": [label['name'] for label in pr_data.get('labels', [])],
            "has_description": len(pr_data.get('body', '') or '') > 50,
            "follows_conventions": False,
            "automated_pr": False
        }
        
        # Check if this is an automated PR from the Azure automation
        title = analysis["title"].lower()
        body = analysis["body"].lower()
        
        automation_indicators = [
            "automated fix for issue",
            "azure automation",
            "🤖",  # Robot emoji
            "auto-generated",
            "fix: application crashes",  # Common patterns from our automation
            "feat: add new",
            "security: fix vulnerability"
        ]
        
        if any(indicator in title or indicator in body for indicator in automation_indicators):
            analysis["automated_pr"] = True
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("Automated PR from trusted system", 3)
            )
        
        # Check conventional commit format
        conventional_patterns = [
            r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+',
            r'^(build|ci|perf|revert)(\(.+\))?: .+'
        ]
        
        if any(re.match(pattern, title) for pattern in conventional_patterns):
            analysis["follows_conventions"] = True
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("Follows conventional commits", 1)
            )
        
        # Check for good description
        if analysis["has_description"]:
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("Has detailed description", 1)
            )
        else:
            self.analysis_result["decision_factors"]["risk_factors"].append(
                ("Missing description", 1)
            )
        
        # Check labels
        safe_labels = ["documentation", "enhancement", "bug", "automated"]
        risky_labels = ["security", "breaking-change", "major"]
        
        for label in analysis["labels"]:
            if label.lower() in safe_labels:
                self.analysis_result["decision_factors"]["confidence_factors"].append(
                    (f"Safe label: {label}", 1)
                )
            elif label.lower() in risky_labels:
                self.analysis_result["decision_factors"]["risk_factors"].append(
                    (f"Risky label: {label}", 2)
                )
        
        self.analysis_result["decision_factors"]["pr_metadata"] = analysis
    
    def _analyze_author_trust(self, pr_data: Dict[str, Any]) -> None:
        """Analyze author trust level."""
        author = pr_data.get('user', {})
        author_login = author.get('login', '')
        
        analysis = {
            "author": author_login,
            "is_collaborator": False,
            "is_automation": False,
            "trust_level": "unknown"
        }
        
        # Check if author is automation system
        automation_accounts = [
            "github-actions[bot]",
            "dependabot[bot]",
            "azure-automation[bot]",
            "renovate[bot]"
        ]
        
        if author_login.lower() in [acc.lower() for acc in automation_accounts]:
            analysis["is_automation"] = True
            analysis["trust_level"] = "automation"
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("Trusted automation account", 4)
            )
        elif author_login == "github-actions[bot]":
            # Special case for GitHub Actions
            analysis["is_automation"] = True
            analysis["trust_level"] = "github_actions"
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("GitHub Actions automation", 3)
            )
        else:
            # For human authors, we'd typically check:
            # - Collaborator status
            # - Contribution history
            # - Previous PR success rate
            # For now, treat as medium trust
            analysis["trust_level"] = "human"
            self.analysis_result["decision_factors"]["risk_factors"].append(
                ("Human author - needs verification", 1)
            )
        
        self.analysis_result["decision_factors"]["author_trust"] = analysis
    
    def _analyze_file_safety(self, pr_data: Dict[str, Any]) -> None:
        """Analyze safety of files being changed."""
        files_changed = pr_data.get('files', [])
        
        # Define critical files that should never be auto-merged
        critical_files = [
            'app-simple.py',  # Main application
            'issue_intelligence.py',  # AI engine
            '.github/workflows/ci-cd.yml',  # Main CI pipeline
            '.github/workflows/security.yml',  # Security pipeline
            'Dockerfile',  # Container config
            'requirements.txt'  # Core dependencies
        ]
        
        critical_dirs = [
            '.github/workflows/',  # All workflow files
            'scripts/',  # Automation scripts
        ]
        
        analysis = {
            "critical_files_changed": [],
            "safe_for_auto_merge": True,
            "requires_human_review": []
        }
        
        for file_info in files_changed:
            filename = file_info.get('filename', '')
            
            # Check if file is in critical list
            if filename in critical_files:
                analysis["critical_files_changed"].append(filename)
                analysis["safe_for_auto_merge"] = False
                self.analysis_result["decision_factors"]["risk_factors"].append(
                    (f"Critical file changed: {filename}", 5)
                )
            
            # Check if file is in critical directory
            for critical_dir in critical_dirs:
                if filename.startswith(critical_dir):
                    analysis["requires_human_review"].append(filename)
                    # Workflows are especially critical
                    if filename.startswith('.github/workflows/'):
                        analysis["safe_for_auto_merge"] = False
                        self.analysis_result["decision_factors"]["risk_factors"].append(
                            (f"Workflow file changed: {filename}", 4)
                        )
                    break
        
        self.analysis_result["safety_checks"]["file_safety"] = analysis
    
    def _analyze_complexity(self, pr_data: Dict[str, Any]) -> None:
        """Analyze code complexity of changes."""
        files_changed = pr_data.get('files', [])
        
        analysis = {
            "total_complexity": 0,
            "complex_changes": [],
            "simple_changes": []
        }
        
        complexity_indicators = {
            # High complexity patterns
            "class ": 3,
            "def ": 2,
            "if ": 1,
            "for ": 1,
            "while ": 1,
            "try:": 2,
            "except": 2,
            "import ": 1,
            "from ": 1,
            # Very high complexity
            "async def": 3,
            "await ": 2,
            "@": 1,  # Decorators
            "lambda": 2
        }
        
        for file_info in files_changed:
            filename = file_info.get('filename', '')
            patch = file_info.get('patch', '')
            
            if not filename.endswith('.py'):
                continue
            
            file_complexity = 0
            
            # Analyze added lines for complexity
            for line in patch.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    line_content = line[1:].strip().lower()
                    
                    for pattern, score in complexity_indicators.items():
                        if pattern in line_content:
                            file_complexity += score
            
            analysis["total_complexity"] += file_complexity
            
            if file_complexity > 20:
                analysis["complex_changes"].append({
                    "file": filename,
                    "complexity": file_complexity
                })
            else:
                analysis["simple_changes"].append({
                    "file": filename,
                    "complexity": file_complexity
                })
        
        # Risk assessment based on complexity
        if analysis["total_complexity"] > 100:
            self.analysis_result["decision_factors"]["risk_factors"].append(
                (f"High complexity: {analysis['total_complexity']}", 3)
            )
        elif analysis["total_complexity"] > 50:
            self.analysis_result["decision_factors"]["risk_factors"].append(
                (f"Medium complexity: {analysis['total_complexity']}", 2)
            )
        else:
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                (f"Low complexity: {analysis['total_complexity']}", 2)
            )
        
        self.analysis_result["decision_factors"]["complexity"] = analysis
    
    def _analyze_testing_coverage(self, pr_data: Dict[str, Any]) -> None:
        """Analyze if PR includes appropriate tests."""
        files_changed = pr_data.get('files', [])
        
        analysis = {
            "test_files_changed": [],
            "source_files_changed": [],
            "has_tests": False,
            "test_coverage_adequate": False
        }
        
        for file_info in files_changed:
            filename = file_info.get('filename', '')
            
            if 'test' in filename.lower() or filename.startswith('tests/'):
                analysis["test_files_changed"].append(filename)
                analysis["has_tests"] = True
            elif filename.endswith('.py') and not filename.endswith('_test.py'):
                analysis["source_files_changed"].append(filename)
        
        # Check if source changes have corresponding tests
        if analysis["source_files_changed"] and analysis["test_files_changed"]:
            analysis["test_coverage_adequate"] = True
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("Includes test changes", 3)
            )
        elif not analysis["source_files_changed"]:
            # No source changes, tests not required
            analysis["test_coverage_adequate"] = True
            self.analysis_result["decision_factors"]["confidence_factors"].append(
                ("No source changes, tests not required", 1)
            )
        else:
            # Source changes without tests
            self.analysis_result["decision_factors"]["risk_factors"].append(
                ("Source changes without tests", 2)
            )
        
        self.analysis_result["decision_factors"]["testing"] = analysis
    
    def _analyze_with_intelligence(self, pr_data: Dict[str, Any]) -> None:
        """Use AI intelligence engine for advanced analysis."""
        try:
            # Prepare data for intelligence analysis
            pr_context = {
                "title": pr_data.get('title', ''),
                "body": pr_data.get('body', '') or '',
                "files_changed": [f.get('filename', '') for f in pr_data.get('files', [])],
                "author": pr_data.get('user', {}).get('login', ''),
                "labels": [l['name'] for l in pr_data.get('labels', [])]
            }
            
            # Analyze PR pattern
            if hasattr(self.intelligence_engine, 'analyze_pr_pattern'):
                pr_analysis = self.intelligence_engine.analyze_pr_pattern(pr_context)
                
                ai_confidence = pr_analysis.get('confidence_score', 0) * 100
                self.analysis_result["decision_factors"]["ai_analysis"] = {
                    "confidence": ai_confidence,
                    "risk_assessment": pr_analysis.get('risk_level', 'unknown'),
                    "recommended_action": pr_analysis.get('recommendation', 'manual_review')
                }
                
                # Boost confidence based on AI analysis
                if ai_confidence > 90:
                    self.analysis_result["decision_factors"]["confidence_factors"].append(
                        (f"High AI confidence: {ai_confidence:.1f}%", 4)
                    )
                elif ai_confidence > 75:
                    self.analysis_result["decision_factors"]["confidence_factors"].append(
                        (f"Good AI confidence: {ai_confidence:.1f}%", 2)
                    )
                else:
                    self.analysis_result["decision_factors"]["risk_factors"].append(
                        (f"Low AI confidence: {ai_confidence:.1f}%", 2)
                    )
            
            # Check historical success of similar PRs
            if hasattr(self.intelligence_engine, 'get_similar_pr_success_rate'):
                success_rate = self.intelligence_engine.get_similar_pr_success_rate(pr_context)
                if success_rate > 0.85:
                    self.analysis_result["decision_factors"]["confidence_factors"].append(
                        (f"High historical success rate: {success_rate:.1%}", 3)
                    )
                elif success_rate < 0.6:
                    self.analysis_result["decision_factors"]["risk_factors"].append(
                        (f"Low historical success rate: {success_rate:.1%}", 2)
                    )
            
        except Exception as e:
            logger.warning(f"⚠️ Error in AI analysis: {e}")
            # Continue with rule-based analysis
    
    def _make_merge_decision(self) -> None:
        """Make the final auto-merge decision based on all factors."""
        # Calculate scores
        confidence_score = sum(factor[1] for factor in 
                              self.analysis_result["decision_factors"].get("confidence_factors", []))
        risk_score = sum(factor[1] for factor in 
                        self.analysis_result["decision_factors"].get("risk_factors", []))
        
        # Normalize to 0-100 scale
        ai_confidence = max(0, min(100, (confidence_score - risk_score) * 10 + 50))
        risk_assessment = max(0, min(10, risk_score))
        
        self.analysis_result["ai_confidence"] = round(ai_confidence, 1)
        self.analysis_result["risk_score"] = round(risk_assessment, 1)
        
        # Decision thresholds
        MIN_CONFIDENCE = 85  # Minimum AI confidence for auto-merge
        MAX_RISK = 3        # Maximum risk score for auto-merge
        
        # Safety checks
        file_safety = self.analysis_result["safety_checks"].get("file_safety", {})
        safe_for_auto_merge = file_safety.get("safe_for_auto_merge", False)
        
        # Make decision
        should_merge = (
            ai_confidence >= MIN_CONFIDENCE and
            risk_assessment <= MAX_RISK and
            safe_for_auto_merge
        )
        
        self.analysis_result["should_auto_merge"] = should_merge
        
        # Determine merge strategy
        files_changed = len(self.analysis_result["decision_factors"].get("code_changes", {}).get("files_changed", []))
        
        if files_changed == 1 and ai_confidence > 95:
            merge_strategy = "rebase"  # Clean history for simple, high-confidence changes
        elif ai_confidence > 90:
            merge_strategy = "squash"  # Squash for good confidence
        else:
            merge_strategy = "merge"   # Regular merge for complex changes
        
        self.analysis_result["merge_strategy"] = merge_strategy
        
        # Generate analysis summary
        self._generate_summary()
    
    def _generate_summary(self) -> None:
        """Generate human-readable analysis summary."""
        confidence = self.analysis_result["ai_confidence"]
        risk = self.analysis_result["risk_score"]
        should_merge = self.analysis_result["should_auto_merge"]
        
        summary_parts = []
        
        # Overall assessment
        if should_merge:
            summary_parts.append("✅ **APPROVED for auto-merge**")
        else:
            summary_parts.append("❌ **REJECTED for auto-merge**")
        
        # Key factors
        confidence_factors = self.analysis_result["decision_factors"].get("confidence_factors", [])
        risk_factors = self.analysis_result["decision_factors"].get("risk_factors", [])
        
        if confidence_factors:
            summary_parts.append("\n**Positive Factors:**")
            for factor, score in confidence_factors[:3]:  # Top 3
                summary_parts.append(f"• {factor} (+{score})")
        
        if risk_factors:
            summary_parts.append("\n**Risk Factors:**")
            for factor, score in risk_factors[:3]:  # Top 3
                summary_parts.append(f"• {factor} (+{score} risk)")
        
        # Decision reasoning
        if should_merge:
            summary_parts.append(f"\n**Decision:** High confidence ({confidence:.1f}%) and low risk ({risk:.1f}/10) enable safe auto-merge.")
        else:
            reasons = []
            if confidence < 85:
                reasons.append(f"confidence too low ({confidence:.1f}% < 85%)")
            if risk > 3:
                reasons.append(f"risk too high ({risk:.1f}/10 > 3)")
            
            file_safety = self.analysis_result["safety_checks"].get("file_safety", {})
            if not file_safety.get("safe_for_auto_merge", True):
                reasons.append("critical files changed")
            
            summary_parts.append(f"\n**Decision:** Manual review required due to {', '.join(reasons)}.")
        
        self.analysis_result["analysis_summary"] = " ".join(summary_parts)
    
    def _output_results(self) -> None:
        """Output results for GitHub Actions."""
        # Set GitHub Action outputs
        outputs = {
            "should_auto_merge": str(self.analysis_result["should_auto_merge"]).lower(),
            "ai_confidence": str(self.analysis_result["ai_confidence"]),
            "risk_score": str(self.analysis_result["risk_score"]),
            "merge_strategy": self.analysis_result["merge_strategy"],
            "analysis_summary": json.dumps(self.analysis_result["analysis_summary"])
        }
        
        # Write to GitHub Actions output
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                for key, value in outputs.items():
                    f.write(f"{key}={value}\n")
        else:
            # Fallback for local testing
            for key, value in outputs.items():
                print(f"::set-output name={key}::{value}")

def main():
    parser = argparse.ArgumentParser(description="Analyze PR for smart auto-merge")
    parser.add_argument("--pr-number", type=int, required=True, help="PR number to analyze")
    parser.add_argument("--repository", required=True, help="Repository in owner/repo format")
    parser.add_argument("--github-token", required=True, help="GitHub API token")
    
    args = parser.parse_args()
    
    try:
        analyzer = PRAutoMergeAnalyzer(args.pr_number, args.repository, args.github_token)
        result = analyzer.analyze_pr()
        
        logger.info(f"✅ Analysis completed for PR #{args.pr_number}")
        logger.info(f"Decision: {'AUTO-MERGE' if result['should_auto_merge'] else 'MANUAL REVIEW'}")
        logger.info(f"AI Confidence: {result['ai_confidence']}%")
        logger.info(f"Risk Score: {result['risk_score']}/10")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        # Set safe defaults for failure case
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("should_auto_merge=false\n")
                f.write("ai_confidence=0\n")
                f.write("risk_score=10\n")
                f.write("merge_strategy=merge\n")
                f.write("analysis_summary=\"Analysis failed - manual review required\"\n")
        sys.exit(1)

if __name__ == "__main__":
    main()