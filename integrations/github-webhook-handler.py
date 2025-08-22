#!/usr/bin/env python3
"""
GitHub Webhook Handler for Automated Issue Management
Receives GitHub webhooks and triggers automated issue processing workflows.
"""

import json
import hmac
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import click
from rich.console import Console
from rich import print as rprint

console = Console()

app = FastAPI(title="GitHub Issue Automation Webhook", version="1.0.0")

class GitHubWebhookHandler:
    """Handles GitHub webhook events for automated issue processing."""
    
    def __init__(self, webhook_secret: Optional[str] = None, repo_path: str = "."):
        self.webhook_secret = webhook_secret
        self.repo_path = Path(repo_path)
        self.console = Console()
        
        # Import the issue executor
        self.executor_path = Path(__file__).parent.parent / "agents" / "issue-executor.py"
        
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def process_issue_event(self, event_type: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process GitHub issue events."""
        issue_number = issue_data.get("number")
        action = issue_data.get("action")
        
        console.print(f"📥 Received issue event: #{issue_number} - {action}", style="blue")
        
        # Only process opened issues for automation
        if action != "opened":
            return {"status": "ignored", "reason": f"Action '{action}' not processed"}
        
        # Extract issue details
        issue_info = {
            "number": issue_number,
            "title": issue_data.get("title", ""),
            "body": issue_data.get("body", ""),
            "labels": issue_data.get("labels", []),
            "created_at": issue_data.get("created_at"),
            "user": issue_data.get("user", {}).get("login"),
            "repository": issue_data.get("repository", {}).get("full_name")
        }
        
        # Start automated processing
        try:
            result = await self.execute_issue_automation(issue_info)
            
            # Post status comment to GitHub issue
            await self.post_status_comment(issue_info, result)
            
            return {
                "status": "processed",
                "issue_number": issue_number,
                "automation_result": result
            }
            
        except Exception as e:
            console.print(f"❌ Error processing issue #{issue_number}: {e}", style="red")
            return {"status": "error", "error": str(e)}
    
    async def execute_issue_automation(self, issue_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automated issue resolution."""
        console.print(f"🤖 Starting automation for issue #{issue_info['number']}", style="green")
        
        # Run the issue executor
        cmd = [
            "python3",
            str(self.executor_path),
            "--issue-number", str(issue_info["number"]),
            "--repo-path", str(self.repo_path)
        ]
        
        # For now, run in analysis mode to avoid actual changes
        cmd.extend(["--analyze-only"])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Automation timed out after 5 minutes",
                "execution_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
    
    async def post_status_comment(self, issue_info: Dict[str, Any], automation_result: Dict[str, Any]):
        """Post automation status as comment on GitHub issue."""
        # This would integrate with GitHub API to post comments
        # For now, just log the status
        
        issue_number = issue_info["number"]
        success = automation_result.get("success", False)
        
        if success:
            console.print(f"✅ Would post success comment to issue #{issue_number}", style="green")
            comment = f"""## 🤖 Automated Analysis Complete

**Status:** ✅ Analysis completed successfully
**Timestamp:** {automation_result.get('execution_time')}

The issue has been automatically analyzed and classified. An execution plan has been generated for automated resolution.

**Next Steps:**
- Review the analysis results
- Approve automated execution if confidence is high
- Manual intervention may be required for complex issues

*This comment was generated by the Claude AI optimization framework.*
"""
        else:
            console.print(f"❌ Would post error comment to issue #{issue_number}", style="red")
            comment = f"""## 🤖 Automated Analysis Failed

**Status:** ❌ Analysis encountered errors
**Timestamp:** {automation_result.get('execution_time')}
**Error:** {automation_result.get('error', 'Unknown error')}

Manual review and intervention required.

*This comment was generated by the Claude AI optimization framework.*
"""
        
        # Log what the comment would be
        console.print(f"Comment content: {comment[:100]}...", style="dim")

# FastAPI webhook endpoints
webhook_handler = GitHubWebhookHandler()

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events."""
    try:
        # Get request data
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        event_type = request.headers.get("X-GitHub-Event", "")
        
        # Verify signature
        if not webhook_handler.verify_signature(payload, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse JSON payload
        try:
            data = json.loads(payload.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process based on event type
        if event_type == "issues":
            # Process in background to avoid timeout
            background_tasks.add_task(
                webhook_handler.process_issue_event,
                event_type,
                data
            )
            
            return JSONResponse({
                "status": "accepted",
                "event_type": event_type,
                "issue_number": data.get("number"),
                "action": data.get("action")
            })
        
        elif event_type == "ping":
            return JSONResponse({"message": "pong", "zen": data.get("zen")})
        
        else:
            return JSONResponse({
                "status": "ignored",
                "event_type": event_type,
                "message": "Event type not processed"
            })
    
    except HTTPException:
        raise
    except Exception as e:
        console.print(f"❌ Webhook processing error: {e}", style="red")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "GitHub Issue Automation",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/stats")
async def get_stats():
    """Get automation statistics."""
    return JSONResponse({
        "status": "operational",
        "features": [
            "GitHub webhook processing",
            "Automated issue analysis",
            "Intelligent agent routing",
            "Cost-optimized execution"
        ],
        "integrations": [
            "claude-ai-optimization framework",
            "ccflare monitoring",
            "ccusage cost tracking"
        ]
    })

@click.command()
@click.option("--port", default=8000, help="Server port")
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--webhook-secret", help="GitHub webhook secret")
@click.option("--repo-path", default=".", help="Repository path")
@click.option("--dev", is_flag=True, help="Development mode with auto-reload")
def main(port: int, host: str, webhook_secret: Optional[str], repo_path: str, dev: bool):
    """Start GitHub webhook handler for issue automation."""
    
    # Configure the webhook handler
    global webhook_handler
    webhook_handler = GitHubWebhookHandler(
        webhook_secret=webhook_secret,
        repo_path=repo_path
    )
    
    console.print("🚀 Starting GitHub Issue Automation Webhook Server", style="bold blue")
    console.print(f"📡 Listening on {host}:{port}")
    console.print(f"📁 Repository path: {repo_path}")
    console.print(f"🔐 Webhook secret: {'configured' if webhook_secret else 'not configured'}")
    
    console.print("\n📋 Webhook Endpoints:")
    console.print(f"  • POST {host}:{port}/webhook/github - GitHub webhook receiver")
    console.print(f"  • GET  {host}:{port}/health - Health check")
    console.print(f"  • GET  {host}:{port}/stats - Service statistics")
    
    console.print("\n🔧 To configure GitHub webhook:")
    console.print(f"  1. Go to repository Settings > Webhooks")
    console.print(f"  2. Add webhook URL: http://{host}:{port}/webhook/github")
    console.print(f"  3. Select 'Issues' events")
    console.print(f"  4. Set content type to 'application/json'")
    if webhook_secret:
        console.print(f"  5. Configure secret for security")
    
    # Start the server
    uvicorn.run(
        "github-webhook-handler:app",
        host=host,
        port=port,
        reload=dev,
        log_level="info"
    )

if __name__ == "__main__":
    main()