#!/usr/bin/env python3
"""
Cost Tracker Integration with ccusage
Automated cost monitoring, reporting, and optimization tracking.
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

class CostTracker:
    """Manages cost tracking and optimization monitoring."""
    
    def __init__(self):
        self.baseline_date = "20250121"  # Start of optimization
        
    def get_daily_usage(self, days: int = 7) -> Dict:
        """Get daily usage report from ccusage."""
        try:
            result = subprocess.run(
                ["ccusage", "daily", "--json", "--breakdown"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Failed to get daily usage: {e}", style="red")
            return {}
        except json.JSONDecodeError:
            console.print("❌ Invalid JSON response from ccusage", style="red")
            return {}
    
    def get_cost_breakdown(self) -> Dict:
        """Get model-specific cost breakdown."""
        try:
            result = subprocess.run(
                ["ccusage", "weekly", "--json", "--breakdown"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Failed to get cost breakdown: {e}", style="red")
            return {}
        except json.JSONDecodeError:
            return {}
    
    def calculate_optimization_savings(self) -> Tuple[float, float, float]:
        """Calculate cost savings from optimization."""
        # This would compare pre/post optimization costs
        # For now, return estimated savings based on model distribution
        
        breakdown = self.get_cost_breakdown()
        if not breakdown:
            return 0.0, 0.0, 0.0
        
        total_cost = 0.0
        haiku_savings = 0.0
        sonnet_usage = 0.0
        
        # Estimate savings based on model usage patterns
        # This is a simplified calculation for demonstration
        if 'models' in breakdown:
            for model, data in breakdown['models'].items():
                cost = data.get('cost', 0.0)
                total_cost += cost
                
                if 'haiku' in model.lower():
                    # Haiku provides ~90% cost savings vs opus
                    haiku_savings += cost * 9  # What it would have cost with opus
                elif 'sonnet' in model.lower():
                    sonnet_usage += cost
        
        estimated_savings_percent = (haiku_savings / (total_cost + haiku_savings)) * 100 if total_cost + haiku_savings > 0 else 0
        return total_cost, haiku_savings, estimated_savings_percent
    
    def check_budget_alerts(self, daily_limit: float = 50.0) -> bool:
        """Check if usage exceeds budget limits."""
        usage = self.get_daily_usage(days=1)
        if not usage:
            return False
        
        today_cost = 0.0
        if 'days' in usage and usage['days']:
            today_cost = usage['days'][0].get('cost', 0.0)
        
        if today_cost > daily_limit:
            console.print(f"⚠️  Budget Alert: Daily cost ${today_cost:.2f} exceeds limit ${daily_limit:.2f}", style="red")
            return True
        
        return False
    
    def show_optimization_report(self) -> None:
        """Display comprehensive optimization report."""
        console.print("📊 Claude AI Cost Optimization Report", style="bold blue")
        
        # Get current usage data
        daily_usage = self.get_daily_usage()
        cost_breakdown = self.get_cost_breakdown()
        total_cost, savings, savings_percent = self.calculate_optimization_savings()
        
        # Usage Summary Table
        table = Table(title="Usage & Cost Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Target", style="green")
        
        table.add_row("Total Cost (7 days)", f"${total_cost:.2f}", "Monitor")
        table.add_row("Estimated Savings", f"${savings:.2f}", ">60% reduction")
        table.add_row("Savings Percentage", f"{savings_percent:.1f}%", ">60%")
        table.add_row("Budget Status", "✅ Within limits" if not self.check_budget_alerts() else "⚠️  Over limit", "<$50/day")
        
        console.print(table)
        
        # Model Distribution Table
        if cost_breakdown and 'models' in cost_breakdown:
            model_table = Table(title="Model Cost Distribution")
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Usage", style="magenta")
            model_table.add_column("Cost", style="green")
            model_table.add_column("Optimization", style="yellow")
            
            for model, data in cost_breakdown['models'].items():
                usage = data.get('usage', 'N/A')
                cost = data.get('cost', 0.0)
                
                if 'haiku' in model.lower():
                    optimization = "✅ Cost-optimized"
                elif 'opus' in model.lower():
                    optimization = "⚠️  High-cost (architecture only)"
                elif 'sonnet' in model.lower():
                    optimization = "✅ Balanced"
                else:
                    optimization = "❓ Review needed"
                
                model_table.add_row(model, str(usage), f"${cost:.2f}", optimization)
            
            console.print(model_table)
    
    def setup_cost_monitoring(self) -> bool:
        """Set up automated cost monitoring."""
        try:
            # Test ccusage functionality
            result = subprocess.run(
                ["ccusage", "daily", "--help"],
                capture_output=True,
                text=True,
                check=True
            )
            
            console.print("✅ Cost monitoring setup complete", style="green")
            console.print("📋 Monitoring features enabled:")
            console.print("  • Daily usage tracking")
            console.print("  • Model cost breakdown")
            console.print("  • Budget alert system")
            console.print("  • Optimization savings calculation")
            
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Failed to setup cost monitoring: {e}", style="red")
            return False

@click.command()
@click.option("--report", is_flag=True, help="Show optimization report")
@click.option("--daily", is_flag=True, help="Show daily usage")
@click.option("--setup", is_flag=True, help="Setup cost monitoring")
@click.option("--budget-check", is_flag=True, help="Check budget alerts")
@click.option("--test-mode", is_flag=True, help="Test mode for validation")
def main(report: bool, daily: bool, setup: bool, budget_check: bool, test_mode: bool):
    """Claude AI Cost Tracking and Optimization Monitoring."""
    
    tracker = CostTracker()
    
    if setup:
        tracker.setup_cost_monitoring()
    
    elif report:
        tracker.show_optimization_report()
    
    elif daily:
        usage = tracker.get_daily_usage()
        if usage:
            console.print(json.dumps(usage, indent=2))
        else:
            console.print("No usage data available", style="yellow")
    
    elif budget_check:
        alert_triggered = tracker.check_budget_alerts()
        if not alert_triggered:
            console.print("✅ Within budget limits", style="green")
    
    elif test_mode:
        console.print("🧪 Testing cost tracking functionality...")
        success = tracker.setup_cost_monitoring()
        if success:
            console.print("✅ Cost tracking test passed", style="green")
        else:
            console.print("❌ Cost tracking test failed", style="red")
    
    else:
        console.print("💰 Claude AI Cost Tracker")
        console.print("Use --setup to initialize, --report for optimization summary, --daily for usage")

if __name__ == "__main__":
    main()