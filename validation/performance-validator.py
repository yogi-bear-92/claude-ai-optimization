#!/usr/bin/env python3
"""
Performance Validation for Claude AI Optimization
Tracks and validates success metrics including development time, cost savings, and team adoption.
"""

import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

class PerformanceValidator:
    """Validates optimization performance against success criteria."""
    
    def __init__(self):
        self.optimization_start_date = datetime(2025, 1, 21)  # When optimization began
        self.target_dev_time_reduction = 0.5  # 50% minimum target
        self.target_cost_reduction = 0.6     # 60% minimum target
        self.target_team_adoption = 0.8      # 80% minimum target
        
    def validate_agent_installation(self) -> Tuple[bool, Dict]:
        """Validate that optimal agents are properly installed."""
        expected_agents = [
            "comprehensive-researcher",
            "code-reviewer", 
            "backend-architect",
            "python-expert",
            "ai-engineer",
            "devops-troubleshooter"
        ]
        
        installed_agents = []
        missing_agents = []
        
        for agent in expected_agents:
            agent_file = Path(f"~/.claude/agents/{agent}.md").expanduser()
            if agent_file.exists():
                installed_agents.append(agent)
            else:
                missing_agents.append(agent)
        
        success = len(missing_agents) == 0
        result = {
            "total_expected": len(expected_agents),
            "installed": len(installed_agents),
            "missing": missing_agents,
            "installed_agents": installed_agents,
            "success_rate": len(installed_agents) / len(expected_agents)
        }
        
        return success, result
    
    def validate_monitoring_tools(self) -> Tuple[bool, Dict]:
        """Validate that monitoring tools are operational."""
        tools_status = {}
        
        # Test ccflare
        try:
            result = subprocess.run(
                ["ccflare", "--stats"],
                capture_output=True,
                text=True,
                timeout=10
            )
            tools_status["ccflare"] = {
                "installed": True,
                "operational": result.returncode == 0,
                "error": None if result.returncode == 0 else result.stderr
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            tools_status["ccflare"] = {
                "installed": False,
                "operational": False,
                "error": str(e)
            }
        
        # Test ccusage
        try:
            result = subprocess.run(
                ["ccusage", "daily", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            tools_status["ccusage"] = {
                "installed": True,
                "operational": result.returncode == 0,
                "error": None if result.returncode == 0 else result.stderr
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            tools_status["ccusage"] = {
                "installed": False,
                "operational": False,
                "error": str(e)
            }
        
        all_operational = all(
            tool["installed"] and tool["operational"] 
            for tool in tools_status.values()
        )
        
        return all_operational, tools_status
    
    def estimate_cost_savings(self) -> Tuple[float, Dict]:
        """Estimate cost savings from optimized model usage."""
        # This would integrate with actual usage data
        # For now, provide estimates based on model distribution
        
        model_costs = {
            "haiku": 0.25,    # Relative cost (haiku = 1x)
            "sonnet": 3.0,    # 3x more expensive than haiku
            "opus": 15.0,     # 15x more expensive than haiku
            "sonnet-4": 5.0   # 5x more expensive than haiku
        }
        
        # Estimated usage distribution with optimization
        optimized_usage = {
            "haiku": 0.3,     # 30% of tasks (documentation, formatting)
            "sonnet": 0.5,    # 50% of tasks (development work)
            "opus": 0.15,     # 15% of tasks (architecture, security)
            "sonnet-4": 0.05  # 5% of tasks (latest features)
        }
        
        # Without optimization (everything on sonnet/opus)
        unoptimized_usage = {
            "haiku": 0.0,
            "sonnet": 0.7,    # 70% on sonnet
            "opus": 0.3,      # 30% on opus
            "sonnet-4": 0.0
        }
        
        optimized_cost = sum(
            model_costs[model] * usage 
            for model, usage in optimized_usage.items()
        )
        
        unoptimized_cost = sum(
            model_costs[model] * usage 
            for model, usage in unoptimized_usage.items()
        )
        
        savings_percent = (unoptimized_cost - optimized_cost) / unoptimized_cost
        
        return savings_percent, {
            "optimized_cost": optimized_cost,
            "unoptimized_cost": unoptimized_cost,
            "savings_percent": savings_percent,
            "model_distribution": optimized_usage
        }
    
    def validate_team_adoption(self) -> Tuple[float, Dict]:
        """Estimate team adoption based on project integration."""
        vlada_projects = [
            "/Users/yogi/Projects/vlada/Ai/agent-factory",
            "/Users/yogi/Projects/vlada/Ai/PRPs-agentic-eng", 
            "/Users/yogi/Projects/vlada/Ai/claude-hub",
            "/Users/yogi/Projects/vlada/Ai/data-for-seo"
        ]
        
        projects_with_optimization = 0
        project_status = {}
        
        for project_path in vlada_projects:
            project_name = Path(project_path).name
            optimization_file = Path(project_path) / "CLAUDE.optimization.md"
            
            if optimization_file.exists():
                projects_with_optimization += 1
                project_status[project_name] = "✅ Optimized"
            else:
                project_status[project_name] = "❌ Not optimized"
        
        adoption_rate = projects_with_optimization / len(vlada_projects)
        
        return adoption_rate, {
            "total_projects": len(vlada_projects),
            "optimized_projects": projects_with_optimization,
            "adoption_rate": adoption_rate,
            "project_status": project_status
        }
    
    def generate_success_report(self) -> None:
        """Generate comprehensive success validation report."""
        console.print("🎯 Claude AI Optimization Success Validation", style="bold blue")
        console.print("="*60)
        
        # Agent Installation Validation
        agents_ok, agent_data = self.validate_agent_installation()
        
        # Monitoring Tools Validation
        monitoring_ok, monitoring_data = self.validate_monitoring_tools()
        
        # Cost Savings Estimation
        cost_savings, cost_data = self.estimate_cost_savings()
        
        # Team Adoption Validation
        adoption_rate, adoption_data = self.validate_team_adoption()
        
        # Success Criteria Table
        criteria_table = Table(title="Success Criteria Validation")
        criteria_table.add_column("Metric", style="cyan")
        criteria_table.add_column("Target", style="yellow")
        criteria_table.add_column("Actual", style="green")
        criteria_table.add_column("Status", style="magenta")
        
        # Agent Installation
        agent_status = "✅ PASS" if agents_ok else "❌ FAIL"
        criteria_table.add_row(
            "Agent Installation",
            "100% optimal agents",
            f"{agent_data['success_rate']:.1%} ({agent_data['installed']}/{agent_data['total_expected']})",
            agent_status
        )
        
        # Monitoring Tools
        monitoring_status = "✅ PASS" if monitoring_ok else "❌ FAIL"
        criteria_table.add_row(
            "Monitoring Tools",
            "All operational",
            "ccflare + ccusage" if monitoring_ok else "Issues detected",
            monitoring_status
        )
        
        # Cost Savings
        cost_target_met = cost_savings >= self.target_cost_reduction
        cost_status = "✅ PASS" if cost_target_met else "⚠️ REVIEW"
        criteria_table.add_row(
            "Cost Reduction",
            f">{self.target_cost_reduction:.0%}",
            f"{cost_savings:.1%} estimated",
            cost_status
        )
        
        # Team Adoption
        adoption_target_met = adoption_rate >= self.target_team_adoption
        adoption_status = "✅ PASS" if adoption_target_met else "🔄 IN PROGRESS"
        criteria_table.add_row(
            "Team Adoption",
            f">{self.target_team_adoption:.0%}",
            f"{adoption_rate:.1%} ({adoption_data['optimized_projects']}/{adoption_data['total_projects']} projects)",
            adoption_status
        )
        
        console.print(criteria_table)
        
        # Detailed Status
        console.print("\n📊 Detailed Status", style="bold")
        
        if not agents_ok and agent_data['missing']:
            console.print(f"❌ Missing agents: {', '.join(agent_data['missing'])}", style="red")
        
        if not monitoring_ok:
            for tool, status in monitoring_data.items():
                if not status['operational']:
                    console.print(f"❌ {tool}: {status['error']}", style="red")
        
        # Project Status
        console.print("\n🏗️ Project Integration Status", style="bold")
        for project, status in adoption_data['project_status'].items():
            console.print(f"  {project}: {status}")
        
        # Overall Assessment
        console.print("\n🎯 Overall Assessment", style="bold green")
        
        total_criteria = 4
        passed_criteria = sum([
            agents_ok,
            monitoring_ok,
            cost_target_met,
            adoption_target_met
        ])
        
        overall_success = passed_criteria / total_criteria
        
        if overall_success >= 0.75:
            console.print(f"✅ OPTIMIZATION SUCCESSFUL ({passed_criteria}/{total_criteria} criteria met)", style="green")
            console.print("Ready for full team deployment and continued optimization")
        elif overall_success >= 0.5:
            console.print(f"⚠️ PARTIAL SUCCESS ({passed_criteria}/{total_criteria} criteria met)", style="yellow")
            console.print("Address remaining issues before full deployment")
        else:
            console.print(f"❌ OPTIMIZATION INCOMPLETE ({passed_criteria}/{total_criteria} criteria met)", style="red")
            console.print("Significant issues need resolution")

@click.command()
@click.option("--development-time", is_flag=True, help="Validate development time improvements")
@click.option("--team-adoption-rate", is_flag=True, help="Check team adoption metrics")
@click.option("--baseline-comparison", is_flag=True, help="Compare against baseline metrics")
@click.option("--all-metrics", is_flag=True, help="Run comprehensive validation")
def main(development_time: bool, team_adoption_rate: bool, baseline_comparison: bool, all_metrics: bool):
    """Claude AI Optimization Performance Validation."""
    
    validator = PerformanceValidator()
    
    if all_metrics or not any([development_time, team_adoption_rate, baseline_comparison]):
        validator.generate_success_report()
    
    elif team_adoption_rate:
        adoption_rate, data = validator.validate_team_adoption()
        console.print(f"Team adoption rate: {adoption_rate:.1%}")
        for project, status in data['project_status'].items():
            console.print(f"  {project}: {status}")
    
    elif development_time:
        console.print("📊 Development time analysis requires usage data collection over time")
        console.print("Current optimization setup enables 50-70% improvement tracking")
    
    elif baseline_comparison:
        cost_savings, data = validator.estimate_cost_savings()
        console.print(f"Estimated cost savings: {cost_savings:.1%}")
        console.print(f"Optimized cost factor: {data['optimized_cost']:.2f}")
        console.print(f"Unoptimized cost factor: {data['unoptimized_cost']:.2f}")

if __name__ == "__main__":
    main()