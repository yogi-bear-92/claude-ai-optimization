#!/usr/bin/env python3
"""
Sophisticated AI-Driven PR Analysis for Smart Auto-Merge
Analyzes multiple dimensions to calculate confidence and risk scores
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentPRAnalyzer:
    """Advanced PR analyzer with multi-dimensional risk assessment"""
    
    def __init__(self, pr_number: int, repository: str, github_token: str):
        self.pr_number = pr_number
        self.repository = repository
        self.github_token = github_token
        self.repo_owner, self.repo_name = repository.split('/')
        
        # Initialize analysis results
        self.analysis_data = {
            'pr_number': pr_number,
            'repository': repository,
            'analyzed_at': datetime.utcnow().isoformat(),
            'metrics': {},
            'risk_factors': {},
            'confidence_factors': {},
            'final_scores': {},
            'recommendation': {}
        }
    
    def analyze_pr(self) -> Dict[str, Any]:
        """Main analysis orchestrator"""
        logger.info(f"🧠 Starting intelligent analysis of PR #{self.pr_number}")
        
        try:
            # Get PR data from GitHub API
            pr_data = self._get_pr_data()
            files_changed = self._get_changed_files()
            author_data = self._get_author_data(pr_data['user']['login'])
            
            # Multi-dimensional analysis
            risk_score = self._calculate_risk_score(pr_data, files_changed)
            confidence_score = self._calculate_confidence_score(pr_data, files_changed, author_data)
            merge_strategy = self._determine_merge_strategy(risk_score, confidence_score, pr_data)
            
            # Final recommendation
            should_merge = self._make_merge_decision(confidence_score, risk_score, pr_data)
            
            # Store final results
            self.analysis_data['final_scores'] = {
                'ai_confidence': confidence_score,
                'risk_score': risk_score,
                'should_auto_merge': should_merge,
                'merge_strategy': merge_strategy
            }
            
            # Generate detailed explanation
            explanation = self._generate_explanation(pr_data, files_changed)
            self.analysis_data['recommendation']['explanation'] = explanation
            
            # Output for GitHub Actions
            self._output_github_actions_results()
            
            logger.info(f"✅ Analysis complete: {confidence_score}% confidence, {risk_score}/10 risk")
            return self.analysis_data
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            self._output_error_results()
            raise
    
    def _get_pr_data(self) -> Dict[str, Any]:
        """Fetch PR data from GitHub API"""
        import requests
        
        url = f"https://api.github.com/repos/{self.repository}/pulls/{self.pr_number}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _get_changed_files(self) -> List[Dict[str, Any]]:
        """Get list of changed files with details"""
        import requests
        
        url = f"https://api.github.com/repos/{self.repository}/pulls/{self.pr_number}/files"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _get_author_data(self, username: str) -> Dict[str, Any]:
        """Get author reputation and history data"""
        import requests
        
        # Get basic user data
        url = f"https://api.github.com/users/{username}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        
        # Get repository-specific commit history (simplified)
        commits_url = f"https://api.github.com/repos/{self.repository}/commits"
        params = {'author': username, 'per_page': 50}
        
        commits_response = requests.get(commits_url, headers=headers, params=params)
        commit_history = commits_response.json() if commits_response.status_code == 200 else []
        
        return {
            'user': user_data,
            'recent_commits': len(commit_history),
            'account_age_days': self._calculate_account_age(user_data.get('created_at', '')),
            'public_repos': user_data.get('public_repos', 0),
            'followers': user_data.get('followers', 0)
        }
    
    def _calculate_risk_score(self, pr_data: Dict, files_changed: List[Dict]) -> int:
        """Calculate comprehensive risk score (0-10, where 10 is highest risk)"""
        risk_factors = {}
        total_risk = 0
        
        # 1. Critical File Analysis (0-3 points)
        critical_risk = self._analyze_critical_files(files_changed)
        risk_factors['critical_files'] = critical_risk
        total_risk += critical_risk
        
        # 2. Change Size Analysis (0-2 points)
        size_risk = self._analyze_change_size(pr_data, files_changed)
        risk_factors['change_size'] = size_risk
        total_risk += size_risk
        
        # 3. Code Complexity Analysis (0-2 points)
        complexity_risk = self._analyze_code_complexity(files_changed)
        risk_factors['code_complexity'] = complexity_risk
        total_risk += complexity_risk
        
        # 4. Dependency Risk (0-2 points)
        dependency_risk = self._analyze_dependency_changes(files_changed)
        risk_factors['dependencies'] = dependency_risk
        total_risk += dependency_risk
        
        # 5. Timing Risk (0-1 point)
        timing_risk = self._analyze_timing_risk()
        risk_factors['timing'] = timing_risk
        total_risk += timing_risk
        
        self.analysis_data['risk_factors'] = risk_factors
        
        # Cap at 10
        final_risk = min(total_risk, 10)
        logger.info(f"🚨 Risk analysis: {final_risk}/10 total risk")
        return final_risk
    
    def _calculate_confidence_score(self, pr_data: Dict, files_changed: List[Dict], author_data: Dict) -> int:
        """Calculate AI confidence score (0-100%)"""
        confidence_factors = {}
        base_confidence = 70  # Start with moderate confidence
        
        # 1. Author Trust Score (-20 to +15 points)
        author_trust = self._analyze_author_trust(author_data)
        confidence_factors['author_trust'] = author_trust
        base_confidence += author_trust
        
        # 2. Code Quality Indicators (-15 to +10 points)
        code_quality = self._analyze_code_quality(files_changed)
        confidence_factors['code_quality'] = code_quality
        base_confidence += code_quality
        
        # 3. Test Coverage Analysis (-10 to +10 points)
        test_coverage = self._analyze_test_coverage(files_changed)
        confidence_factors['test_coverage'] = test_coverage
        base_confidence += test_coverage
        
        # 4. PR Description Quality (-5 to +5 points)
        description_quality = self._analyze_pr_description(pr_data)
        confidence_factors['description_quality'] = description_quality
        base_confidence += description_quality
        
        # 5. Change Pattern Analysis (-5 to +5 points)
        change_patterns = self._analyze_change_patterns(files_changed)
        confidence_factors['change_patterns'] = change_patterns
        base_confidence += change_patterns
        
        self.analysis_data['confidence_factors'] = confidence_factors
        
        # Ensure 0-100 range
        final_confidence = max(0, min(base_confidence, 100))
        logger.info(f"🎯 Confidence analysis: {final_confidence}% confidence")
        return final_confidence
    
    def _analyze_critical_files(self, files_changed: List[Dict]) -> int:
        """Analyze if critical files are being modified"""
        critical_patterns = [
            r'.*migrations?/.*',  # Database migrations
            r'.*requirements\.txt$',  # Dependencies
            r'.*package\.json$',  # Node dependencies
            r'.*Dockerfile$',  # Container config
            r'.*\.env.*',  # Environment config
            r'.*config/.*',  # Configuration files
            r'.*auth.*',  # Authentication code
            r'.*security.*',  # Security code
            r'.*deploy.*',  # Deployment scripts
            r'.*\.github/workflows/.*',  # CI/CD workflows
        ]
        
        critical_files = []
        for file in files_changed:
            filename = file['filename']
            for pattern in critical_patterns:
                if re.match(pattern, filename, re.IGNORECASE):
                    critical_files.append(filename)
                    break
        
        if len(critical_files) >= 3:
            return 3  # High risk
        elif len(critical_files) >= 1:
            return 2  # Medium risk
        return 0  # Low risk
    
    def _analyze_change_size(self, pr_data: Dict, files_changed: List[Dict]) -> int:
        """Analyze the size of changes"""
        additions = pr_data.get('additions', 0)
        deletions = pr_data.get('deletions', 0)
        files_count = len(files_changed)
        
        total_changes = additions + deletions
        
        # Risk scoring based on change size
        if total_changes > 1000 or files_count > 20:
            return 2  # High risk - large changes
        elif total_changes > 300 or files_count > 10:
            return 1  # Medium risk
        return 0  # Low risk
    
    def _analyze_code_complexity(self, files_changed: List[Dict]) -> int:
        """Analyze code complexity patterns"""
        complexity_indicators = 0
        
        for file in files_changed:
            if not file.get('patch'):
                continue
                
            patch = file['patch']
            
            # Look for complexity indicators in the patch
            complexity_patterns = [
                r'(\+.*if\s+.*and\s+.*and\s+)',  # Complex conditionals
                r'(\+.*for\s+.*in\s+.*for\s+)',  # Nested loops
                r'(\+.*except\s+.*except\s+)',  # Multiple exception handling
                r'(\+.*lambda\s+.*lambda\s+)',  # Nested lambdas
                r'(\+.*\[\s*.*\[\s*.*\]\s*.*\])',  # Nested data structures
            ]
            
            for pattern in complexity_patterns:
                if re.search(pattern, patch):
                    complexity_indicators += 1
        
        if complexity_indicators >= 5:
            return 2  # High complexity
        elif complexity_indicators >= 2:
            return 1  # Medium complexity
        return 0  # Low complexity
    
    def _analyze_dependency_changes(self, files_changed: List[Dict]) -> int:
        """Analyze dependency-related changes"""
        dependency_files = [
            'requirements.txt', 'requirements-dev.txt', 'pyproject.toml',
            'package.json', 'package-lock.json', 'yarn.lock',
            'Gemfile', 'Gemfile.lock', 'composer.json',
            'pom.xml', 'build.gradle', 'go.mod'
        ]
        
        for file in files_changed:
            filename = os.path.basename(file['filename'])
            if filename in dependency_files:
                # Check if it's adding new dependencies vs updating versions
                patch = file.get('patch', '')
                new_deps = len(re.findall(r'^\+[^+].*[=<>]', patch, re.MULTILINE))
                
                if new_deps >= 3:
                    return 2  # High risk - multiple new dependencies
                elif new_deps >= 1:
                    return 1  # Medium risk - some new dependencies
        
        return 0  # No dependency risk
    
    def _analyze_timing_risk(self) -> int:
        """Analyze timing-based risk (Friday deployments, etc.)"""
        now = datetime.utcnow()
        
        # Friday afternoon/evening UTC (risky deployment time)
        if now.weekday() == 4 and now.hour >= 16:  # Friday after 4 PM UTC
            return 1
        
        return 0
    
    def _analyze_author_trust(self, author_data: Dict) -> int:
        """Analyze author trustworthiness"""
        score = 0
        
        # Account age (older = more trusted)
        account_age = author_data['account_age_days']
        if account_age > 365:
            score += 5
        elif account_age > 90:
            score += 2
        elif account_age < 30:
            score -= 10
        
        # Repository activity
        recent_commits = author_data['recent_commits']
        if recent_commits > 20:
            score += 5
        elif recent_commits > 5:
            score += 2
        elif recent_commits == 0:
            score -= 15
        
        # Public profile indicators
        public_repos = author_data['public_repos']
        followers = author_data['followers']
        
        if public_repos > 10:
            score += 3
        if followers > 50:
            score += 2
        
        return max(-20, min(score, 15))
    
    def _analyze_code_quality(self, files_changed: List[Dict]) -> int:
        """Analyze code quality indicators"""
        score = 0
        
        for file in files_changed:
            if not file.get('patch'):
                continue
                
            patch = file['patch']
            
            # Positive indicators
            if 'test' in file['filename'].lower():
                score += 2  # Adding tests
            if re.search(r'\+.*def test_', patch):
                score += 3  # Adding test functions
            if re.search(r'\+.*# TODO|FIXME|XXX', patch):
                score -= 2  # Adding TODO comments (tech debt)
            if re.search(r'\+.*print\(|console\.log\(|echo ', patch):
                score -= 1  # Debug statements left in
            
            # Code structure indicators
            if re.search(r'\+.*class\s+\w+:', patch):
                score += 1  # Well-structured OOP
            if re.search(r'\+.*""".*"""', patch, re.DOTALL):
                score += 1  # Documentation strings
        
        return max(-15, min(score, 10))
    
    def _analyze_test_coverage(self, files_changed: List[Dict]) -> int:
        """Analyze test coverage changes"""
        test_files = 0
        code_files = 0
        
        for file in files_changed:
            filename = file['filename'].lower()
            if 'test' in filename or filename.endswith('_test.py') or filename.endswith('.test.js'):
                test_files += 1
            elif filename.endswith(('.py', '.js', '.ts', '.java', '.go', '.rb')):
                code_files += 1
        
        if code_files == 0:
            return 0  # No code changes
        
        test_ratio = test_files / code_files if code_files > 0 else 0
        
        if test_ratio >= 0.5:
            return 10  # Great test coverage
        elif test_ratio >= 0.2:
            return 5   # Good test coverage
        elif test_ratio > 0:
            return 2   # Some tests
        else:
            return -10  # No tests for code changes
    
    def _analyze_pr_description(self, pr_data: Dict) -> int:
        """Analyze PR description quality"""
        description = pr_data.get('body', '') or ''
        title = pr_data.get('title', '') or ''
        
        score = 0
        
        # Title quality
        if len(title) > 10 and not title.lower().startswith(('fix', 'update', 'change')):
            score += 1
        
        # Description length and content
        if len(description) > 50:
            score += 2
        if len(description) > 200:
            score += 1
        
        # Quality indicators
        quality_indicators = [
            r'## Summary|## What|## Changes|## Description',  # Structured description
            r'- \[x\]|- \[ \]',  # Checklists
            r'fixes #\d+|closes #\d+|resolves #\d+',  # Issue references
            r'@\w+',  # Mentions for review
        ]
        
        for indicator in quality_indicators:
            if re.search(indicator, description, re.IGNORECASE):
                score += 1
        
        return max(-5, min(score, 5))
    
    def _analyze_change_patterns(self, files_changed: List[Dict]) -> int:
        """Analyze patterns in the changes"""
        score = 0
        
        # File organization
        directories = set()
        for file in files_changed:
            directory = os.path.dirname(file['filename'])
            directories.add(directory)
        
        if len(directories) <= 3:
            score += 2  # Focused changes in few directories
        
        # Change types
        file_extensions = {}
        for file in files_changed:
            ext = os.path.splitext(file['filename'])[1]
            file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        if len(file_extensions) <= 2:
            score += 1  # Consistent file types
        
        return max(-5, min(score, 5))
    
    def _determine_merge_strategy(self, confidence: int, risk: int, pr_data: Dict) -> str:
        """Determine the best merge strategy"""
        if confidence >= 90 and risk <= 2:
            return 'merge'  # Standard merge for high confidence, low risk
        elif confidence >= 80 and risk <= 3:
            return 'squash'  # Squash merge for good confidence
        else:
            return 'rebase'  # Rebase for lower confidence (maintains history)
    
    def _make_merge_decision(self, confidence: int, risk: int, pr_data: Dict) -> bool:
        """Make final auto-merge decision"""
        # Conservative thresholds for safety
        min_confidence = 85
        max_risk = 3
        
        # Additional safety checks
        is_draft = pr_data.get('draft', False)
        has_conflicts = pr_data.get('mergeable', True) is False
        
        decision = (
            confidence >= min_confidence and 
            risk <= max_risk and 
            not is_draft and 
            not has_conflicts
        )
        
        logger.info(f"🤖 Merge decision: {'✅ APPROVE' if decision else '❌ REJECT'}")
        logger.info(f"   Confidence: {confidence}% (need ≥{min_confidence}%)")
        logger.info(f"   Risk: {risk}/10 (need ≤{max_risk}/10)")
        
        return decision
    
    def _generate_explanation(self, pr_data: Dict, files_changed: List[Dict]) -> str:
        """Generate human-readable explanation"""
        confidence = self.analysis_data['final_scores']['ai_confidence']
        risk = self.analysis_data['final_scores']['risk_score']
        should_merge = self.analysis_data['final_scores']['should_auto_merge']
        
        explanation = []
        
        if should_merge:
            explanation.append("🎯 **APPROVED FOR AUTO-MERGE**")
            explanation.append(f"The AI system has high confidence ({confidence}%) and low risk ({risk}/10) in these changes.")
        else:
            explanation.append("⚠️ **REQUIRES MANUAL REVIEW**")
            
            if confidence < 85:
                explanation.append(f"- Confidence too low: {confidence}% (need ≥85%)")
            if risk > 3:
                explanation.append(f"- Risk too high: {risk}/10 (need ≤3/10)")
        
        # Add key factors
        explanation.append("\n**Key Analysis Factors:**")
        
        risk_factors = self.analysis_data['risk_factors']
        if risk_factors.get('critical_files', 0) > 0:
            explanation.append(f"- 🚨 Critical files modified (risk +{risk_factors['critical_files']})")
        
        if risk_factors.get('change_size', 0) > 0:
            explanation.append(f"- 📏 Large change size (risk +{risk_factors['change_size']})")
        
        confidence_factors = self.analysis_data['confidence_factors']
        if confidence_factors.get('test_coverage', 0) > 5:
            explanation.append(f"- ✅ Good test coverage (confidence +{confidence_factors['test_coverage']})")
        
        if confidence_factors.get('author_trust', 0) > 0:
            explanation.append(f"- 👤 Trusted author (confidence +{confidence_factors['author_trust']})")
        
        return '\n'.join(explanation)
    
    def _calculate_account_age(self, created_at: str) -> int:
        """Calculate account age in days"""
        if not created_at:
            return 0
        
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age = datetime.now().astimezone() - created
            return age.days
        except:
            return 0
    
    def _output_github_actions_results(self):
        """Output results for GitHub Actions"""
        scores = self.analysis_data['final_scores']
        
        # Set GitHub Actions outputs
        print(f"::set-output name=should_auto_merge::{str(scores['should_auto_merge']).lower()}")
        print(f"::set-output name=ai_confidence::{scores['ai_confidence']}")
        print(f"::set-output name=risk_score::{scores['risk_score']}")
        print(f"::set-output name=merge_strategy::{scores['merge_strategy']}")
        print(f"::set-output name=analysis_summary::{self.analysis_data['recommendation']['explanation']}")
    
    def _output_error_results(self):
        """Output error results for GitHub Actions"""
        print("::set-output name=should_auto_merge::false")
        print("::set-output name=ai_confidence::0")
        print("::set-output name=risk_score::10")
        print("::set-output name=merge_strategy::manual")
        print("::set-output name=analysis_summary::Analysis failed - manual review required")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Intelligent PR Analysis for Smart Auto-Merge')
    parser.add_argument('--pr-number', type=int, required=True, help='Pull request number')
    parser.add_argument('--repository', required=True, help='Repository (owner/name)')
    parser.add_argument('--github-token', required=True, help='GitHub token')
    parser.add_argument('--output-file', help='Output JSON file path')
    
    args = parser.parse_args()
    
    try:
        analyzer = IntelligentPRAnalyzer(
            pr_number=args.pr_number,
            repository=args.repository,
            github_token=args.github_token
        )
        
        results = analyzer.analyze_pr()
        
        # Save detailed results if requested
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"📊 Detailed analysis saved to {args.output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())