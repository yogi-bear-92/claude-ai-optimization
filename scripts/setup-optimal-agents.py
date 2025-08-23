#!/usr/bin/env python3
"""
Claude AI Optimization Setup Script

This script configures the optimal Claude AI agent setup based on comprehensive
analysis of 600+ agents across multiple collections.
"""

import os
import shutil
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

console = Console()

class AgentOptimizer:
    """Handles the optimization and setup of Claude AI agents."""
    
    def __init__(self, claude_agents_dir: str = "/Users/yogi/.claude/agents"):
        self.claude_agents_dir = Path(claude_agents_dir)
        self.project_dir = Path(__file__).parent.parent
        self.config_file = self.project_dir / "configs" / "optimal-agent-config.yaml"
        
    def load_config(self) -> Dict:
        """Load the optimal agent configuration."""
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def verify_claude_directory(self) -> bool:
        """Verify that the Claude agents directory exists."""
        if not self.claude_agents_dir.exists():
            console.print(f"❌ Claude agents directory not found: {self.claude_agents_dir}", style="red")
            return False
        
        # Check for major collections
        collections = ["comprehensive", "mega-pack", "ai-team", "wh-production"]
        found_collections = []
        
        for collection in collections:
            if (self.claude_agents_dir / collection).exists():
                found_collections.append(collection)
        
        console.print(f"✅ Found collections: {', '.join(found_collections)}", style="green")
        return len(found_collections) >= 2  # Need at least 2 collections
    
    def find_agent_file(self, agent_name: str, collection: str) -> Optional[Path]:
        """Find the agent file in the specified collection."""
        # Common locations for agents
        possible_paths = [
            self.claude_agents_dir / f"{agent_name}.md",
            self.claude_agents_dir / collection / f"{agent_name}.md",
            self.claude_agents_dir / collection / "agents" / f"{agent_name}.md",
            self.claude_agents_dir / collection / "subagents" / f"{agent_name}.md",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def backup_current_setup(self) -> Path:
        """Create a backup of the current agent setup."""
        backup_dir = self.project_dir / "backups" / f"claude-agents-backup-{os.getpid()}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup individual agent files from root
        for agent_file in self.claude_agents_dir.glob("*.md"):
            if agent_file.is_file():
                shutil.copy2(agent_file, backup_dir)
        
        console.print(f"✅ Backup created: {backup_dir}", style="green")
        return backup_dir
    
    def install_agent(self, agent_name: str, collection: str, model: str) -> bool:
        """Install a specific agent to the Claude directory."""
        source_path = self.find_agent_file(agent_name, collection)
        
        if not source_path:
            console.print(f"❌ Agent not found: {agent_name} in {collection}", style="red")
            return False
        
        # Destination is always root level for simplicity
        dest_path = self.claude_agents_dir / f"{agent_name}.md"
        
        # Check if source and destination are the same (agent already in root)
        if source_path.resolve() == dest_path.resolve():
            console.print(f"✅ Agent already in optimal location: {agent_name}", style="yellow")
            # Just update the model assignment
            self.update_agent_model(dest_path, model)
            return True
        
        # Copy the agent file only if different locations
        shutil.copy2(source_path, dest_path)
        
        # Update model assignment if needed
        self.update_agent_model(dest_path, model)
        
        return True
    
    def update_agent_model(self, agent_path: Path, model: str) -> bool:
        """Update the model assignment in an agent file."""
        try:
            content = agent_path.read_text()
            lines = content.split('\n')
            
            # Find and update model in frontmatter
            in_frontmatter = False
            model_updated = False
            
            for i, line in enumerate(lines):
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    continue
                
                if in_frontmatter and line.startswith('model:'):
                    lines[i] = f"model: {model}"
                    model_updated = True
                    break
            
            # If no model field found, add it
            if not model_updated and in_frontmatter:
                for i, line in enumerate(lines):
                    if line.strip() == '---' and i > 0:  # Second ---
                        lines.insert(i, f"model: {model}")
                        break
            
            agent_path.write_text('\n'.join(lines))
            return True
            
        except Exception as e:
            console.print(f"❌ Failed to update model for {agent_path.name}: {e}", style="red")
            return False
    
    def install_optimal_agents(self) -> Dict[str, int]:
        """Install all agents from the optimal configuration."""
        config = self.load_config()
        stats = {"installed": 0, "failed": 0, "total": 0}
        
        all_agents = []
        
        # Collect all agents from config
        for category in ["foundation_agents", "technology_specialists", "orchestration_agents", "utility_agents"]:
            if category in config:
                all_agents.extend(config[category])
        
        stats["total"] = len(all_agents)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Installing agents...", total=len(all_agents))
            
            for agent in all_agents:
                agent_name = agent["name"]
                collection = agent["collection"]
                model = agent["model"]
                
                progress.update(task, description=f"Installing {agent_name}...")
                
                if self.install_agent(agent_name, collection, model):
                    stats["installed"] += 1
                    console.print(f"✅ Installed: {agent_name} ({model})", style="green")
                else:
                    stats["failed"] += 1
                    console.print(f"❌ Failed: {agent_name}", style="red")
                
                progress.advance(task)
        
        return stats
    
    def generate_summary_report(self, stats: Dict[str, int]) -> None:
        """Generate a summary report of the installation."""
        config = self.load_config()
        
        table = Table(title="Claude AI Optimization Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Details", style="green")
        
        # Installation stats
        table.add_row("Total Agents", str(stats["total"]), "Optimal selection from 600+ available")
        table.add_row("Successfully Installed", str(stats["installed"]), "Ready for use")
        table.add_row("Failed", str(stats["failed"]), "Check logs for details")
        
        # Model distribution
        model_counts = {}
        for category in ["foundation_agents", "technology_specialists", "orchestration_agents", "utility_agents"]:
            if category in config:
                for agent in config[category]:
                    model = agent["model"]
                    model_counts[model] = model_counts.get(model, 0) + 1
        
        table.add_row("", "", "")  # Separator
        table.add_row("Model Distribution", "", "Cost optimization strategy")
        
        for model, count in model_counts.items():
            cost_level = config["model_assignment_strategy"][model]["estimated_cost"]
            table.add_row(f"  {model}", str(count), f"{cost_level} cost")
        
        console.print(table)
        
        # Next steps
        console.print("\n🚀 Next Steps:", style="bold blue")
        console.print("1. Run 'claude doctor' to verify installation")
        console.print("2. Test core agents with simple tasks")
        console.print("3. Configure project-specific workflows")
        console.print("4. Set up monitoring and feedback loops")
        console.print(f"5. Review documentation in {self.project_dir / 'docs'}")


@click.command()
@click.option("--claude-dir", default="/Users/yogi/.claude/agents", 
              help="Path to Claude agents directory")
@click.option("--backup/--no-backup", default=True, 
              help="Create backup before installation")
@click.option("--dry-run", is_flag=True, 
              help="Show what would be installed without actually doing it")
@click.option("--validate", is_flag=True,
              help="Validate configuration and agent files without installation")
def main(claude_dir: str, backup: bool, dry_run: bool, validate: bool):
    """Install optimal Claude AI agent configuration."""
    
    console.print("🤖 Claude AI Optimization Setup", style="bold blue")
    console.print("Based on analysis of 600+ agents across 4 collections\n")
    
    optimizer = AgentOptimizer(claude_dir)
    
    # Verify environment
    if not optimizer.verify_claude_directory():
        raise click.ClickException("Claude agents directory not found or invalid")
    
    # Show configuration summary
    config = optimizer.load_config()
    console.print(f"📋 Configuration: {config['description']}")
    console.print(f"📅 Version: {config['version']} (Created: {config['created']})\n")
    
    if validate:
        console.print("✅ VALIDATION MODE - Checking configuration and agents\n", style="green")
        # Run validation using the existing validator
        import subprocess
        result = subprocess.run([sys.executable, "scripts/validate-agents.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ All agents validated successfully", style="green")
        else:
            console.print("❌ Agent validation failed", style="red")
            console.print(result.stdout)
        return

    if dry_run:
        console.print("🔍 DRY RUN MODE - No changes will be made\n", style="yellow")
        # TODO: Implement dry run logic
        return
    
    # Create backup
    if backup:
        optimizer.backup_current_setup()
    
    # Install agents
    console.print("🚀 Installing optimal agent configuration...\n")
    stats = optimizer.install_optimal_agents()
    
    # Generate report
    console.print("\n" + "="*60)
    optimizer.generate_summary_report(stats)


if __name__ == "__main__":
    main()