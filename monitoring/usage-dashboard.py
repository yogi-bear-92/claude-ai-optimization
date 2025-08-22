#!/usr/bin/env python3
"""
Usage Dashboard Integration with ccflare
Provides comprehensive monitoring and cost tracking for Claude AI optimization.
"""

import subprocess
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

class UsageDashboard:
    """Manages ccflare dashboard and usage monitoring."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.dashboard_url = f"http://localhost:{port}"
        
    def start_dashboard(self) -> bool:
        """Start ccflare dashboard server."""
        try:
            console.print(f"🚀 Starting ccflare dashboard on port {self.port}...")
            
            # Start ccflare server in background
            process = subprocess.Popen(
                ["ccflare", "--serve", "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it time to start
            time.sleep(3)
            
            # Check if it's running
            if process.poll() is None:
                console.print(f"✅ Dashboard started: {self.dashboard_url}", style="green")
                return True
            else:
                stdout, stderr = process.communicate()
                console.print(f"❌ Failed to start dashboard: {stderr}", style="red")
                return False
                
        except Exception as e:
            console.print(f"❌ Error starting dashboard: {e}", style="red")
            return False
    
    def get_stats(self) -> Dict:
        """Get current usage statistics from ccflare."""
        try:
            result = subprocess.run(
                ["ccflare", "--stats"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Failed to get stats: {e}", style="red")
            return {}
        except json.JSONDecodeError:
            console.print("❌ Invalid JSON response from ccflare", style="red")
            return {}
    
    def health_check(self) -> bool:
        """Verify dashboard is operational."""
        try:
            stats = self.get_stats()
            if stats:
                console.print("✅ ccflare dashboard operational", style="green")
                return True
            else:
                console.print("❌ ccflare dashboard not responding", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Health check failed: {e}", style="red")
            return False
    
    def show_usage_summary(self) -> None:
        """Display current usage summary."""
        stats = self.get_stats()
        if not stats:
            console.print("No usage data available", style="yellow")
            return
        
        table = Table(title="Claude AI Usage Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Details", style="green")
        
        # Add stats to table
        for key, value in stats.items():
            if isinstance(value, dict):
                # Handle nested stats
                for subkey, subvalue in value.items():
                    table.add_row(f"{key}.{subkey}", str(subvalue), "")
            else:
                table.add_row(key, str(value), "")
        
        console.print(table)

@click.command()
@click.option("--port", default=8080, help="Dashboard port")
@click.option("--start", is_flag=True, help="Start dashboard server")
@click.option("--stats", is_flag=True, help="Show usage statistics")
@click.option("--health-check", is_flag=True, help="Verify dashboard health")
def main(port: int, start: bool, stats: bool, health_check: bool):
    """Claude AI Usage Dashboard Management."""
    
    dashboard = UsageDashboard(port=port)
    
    if start:
        success = dashboard.start_dashboard()
        if success:
            console.print(f"Dashboard running at: {dashboard.dashboard_url}")
            console.print("Press Ctrl+C to stop...")
            try:
                # Keep running until interrupted
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n👋 Dashboard stopped")
    
    elif health_check:
        dashboard.health_check()
    
    elif stats:
        dashboard.show_usage_summary()
    
    else:
        console.print("🤖 Claude AI Usage Dashboard")
        console.print("Use --start to launch dashboard, --stats to view usage, --health-check to verify")

if __name__ == "__main__":
    main()