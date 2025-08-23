#!/usr/bin/env python3
"""
GitHub Issue Status Management System
Tracks issue states and manages automated status transitions.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class IssueStatus(Enum):
    """Issue status states for automation workflow."""
    
    # Initial states
    NEW = "new"                           # Just created, awaiting analysis
    ANALYZING = "analyzing"               # AI is analyzing the issue
    ANALYZED = "analyzed"                 # Analysis complete, awaiting decision
    
    # Execution states  
    APPROVED = "approved"                 # Approved for automation
    IN_PROGRESS = "in_progress"          # Automation is working on it
    BLOCKED = "blocked"                   # Automation encountered issues
    REVIEW_NEEDED = "review_needed"       # Requires human review
    
    # Completion states
    COMPLETED = "completed"               # Automation finished successfully
    MERGED = "merged"                     # Pull request was merged
    CLOSED = "closed"                     # Issue closed without automation
    REJECTED = "rejected"                 # Not suitable for automation

@dataclass
class IssueState:
    """Represents the current state of an issue."""
    
    issue_number: int
    repository: str
    status: IssueStatus
    assigned_agent: Optional[str] = None
    confidence_score: float = 0.0
    estimated_cost: float = 0.0
    estimated_hours: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    error_message: Optional[str] = None
    status_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.status_history is None:
            self.status_history = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

class GitHubStatusManager:
    """Manages GitHub issue status updates and labels."""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.client = httpx.AsyncClient()
        
        # Status label mapping
        self.status_labels = {
            IssueStatus.NEW: "🆕 ai-new",
            IssueStatus.ANALYZING: "🔍 ai-analyzing", 
            IssueStatus.ANALYZED: "📊 ai-analyzed",
            IssueStatus.APPROVED: "✅ ai-approved",
            IssueStatus.IN_PROGRESS: "🚀 ai-in-progress",
            IssueStatus.BLOCKED: "🚫 ai-blocked",
            IssueStatus.REVIEW_NEEDED: "👥 ai-review-needed",
            IssueStatus.COMPLETED: "✨ ai-completed",
            IssueStatus.MERGED: "🎉 ai-merged",
            IssueStatus.CLOSED: "🔒 ai-closed",
            IssueStatus.REJECTED: "❌ ai-rejected"
        }
    
    async def update_issue_labels(self, repository: str, issue_number: int, new_status: IssueStatus):
        """Update GitHub issue labels to reflect current status."""
        try:
            # Remove existing AI status labels
            current_labels_response = await self.client.get(
                f"https://api.github.com/repos/{repository}/issues/{issue_number}/labels",
                headers={"Authorization": f"token {self.github_token}"}
            )
            
            if current_labels_response.status_code == 200:
                current_labels = current_labels_response.json()
                ai_labels_to_remove = [
                    label["name"] for label in current_labels 
                    if label["name"].startswith(("🆕 ai-", "🔍 ai-", "📊 ai-", "✅ ai-", "🚀 ai-", "🚫 ai-", "👥 ai-", "✨ ai-", "🎉 ai-", "🔒 ai-", "❌ ai-"))
                ]
                
                # Remove old AI status labels
                for label_name in ai_labels_to_remove:
                    await self.client.delete(
                        f"https://api.github.com/repos/{repository}/issues/{issue_number}/labels/{label_name}",
                        headers={"Authorization": f"token {self.github_token}"}
                    )
            
            # Add new status label
            new_label = self.status_labels[new_status]
            await self.client.post(
                f"https://api.github.com/repos/{repository}/issues/{issue_number}/labels",
                headers={"Authorization": f"token {self.github_token}"},
                json={"labels": [new_label]}
            )
            
            logger.info(f"Updated issue #{issue_number} label to: {new_label}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update labels for issue #{issue_number}: {e}")
            return False
    
    async def post_status_comment(self, repository: str, issue_number: int, issue_state: IssueState, message: str = ""):
        """Post status update comment to GitHub issue."""
        try:
            status_emojis = {
                IssueStatus.NEW: "🆕",
                IssueStatus.ANALYZING: "🔍", 
                IssueStatus.ANALYZED: "📊",
                IssueStatus.APPROVED: "✅",
                IssueStatus.IN_PROGRESS: "🚀",
                IssueStatus.BLOCKED: "🚫",
                IssueStatus.REVIEW_NEEDED: "👥",
                IssueStatus.COMPLETED: "✨",
                IssueStatus.MERGED: "🎉",
                IssueStatus.CLOSED: "🔒",
                IssueStatus.REJECTED: "❌"
            }
            
            emoji = status_emojis.get(issue_state.status, "📋")
            status_name = issue_state.status.value.replace("_", " ").title()
            
            comment_body = f"""## {emoji} Status Update: {status_name}

**Timestamp:** {issue_state.updated_at}
**Assigned Agent:** {issue_state.assigned_agent or 'None'}
**Confidence Score:** {issue_state.confidence_score:.1%}
**Estimated Cost:** ${issue_state.estimated_cost:.2f}
**Estimated Hours:** {issue_state.estimated_hours:.1f}h

{f"**Branch:** {issue_state.branch_name}" if issue_state.branch_name else ""}
{f"**Pull Request:** #{issue_state.pr_number}" if issue_state.pr_number else ""}
{f"**Error:** {issue_state.error_message}" if issue_state.error_message else ""}

{message}

---
*Automated status update from Claude AI Issue Management*"""

            response = await self.client.post(
                f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments",
                headers={"Authorization": f"token {self.github_token}"},
                json={"body": comment_body}
            )
            
            if response.status_code == 201:
                logger.info(f"Posted status comment for issue #{issue_number}")
                return True
            else:
                logger.error(f"Failed to post comment: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to post status comment: {e}")
            return False

class IssueStateManager:
    """Manages issue state persistence and transitions."""
    
    def __init__(self, storage_path: str = "/tmp/issue_states"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def _get_state_file(self, repository: str, issue_number: int) -> str:
        """Get file path for issue state storage."""
        safe_repo = repository.replace("/", "_")
        return f"{self.storage_path}/{safe_repo}_issue_{issue_number}.json"
    
    async def save_state(self, issue_state: IssueState):
        """Save issue state to persistent storage."""
        try:
            state_file = self._get_state_file(issue_state.repository, issue_state.issue_number)
            state_data = asdict(issue_state)
            state_data['status'] = issue_state.status.value  # Convert enum to string
            
            async with aiofiles.open(state_file, 'w') as f:
                await f.write(json.dumps(state_data, indent=2))
            
            logger.info(f"Saved state for issue #{issue_state.issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    async def load_state(self, repository: str, issue_number: int) -> Optional[IssueState]:
        """Load issue state from persistent storage."""
        try:
            state_file = self._get_state_file(repository, issue_number)
            
            if not os.path.exists(state_file):
                return None
            
            async with aiofiles.open(state_file, 'r') as f:
                state_data = json.loads(await f.read())
            
            # Convert status string back to enum
            state_data['status'] = IssueStatus(state_data['status'])
            
            return IssueState(**state_data)
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    async def transition_status(self, repository: str, issue_number: int, new_status: IssueStatus, **kwargs) -> Optional[IssueState]:
        """Transition issue to new status with validation."""
        try:
            # Load current state
            current_state = await self.load_state(repository, issue_number)
            
            if not current_state:
                # Create new state if none exists
                current_state = IssueState(
                    issue_number=issue_number,
                    repository=repository,
                    status=IssueStatus.NEW
                )
            
            # Validate transition
            if not self._is_valid_transition(current_state.status, new_status):
                logger.warning(f"Invalid status transition: {current_state.status} -> {new_status}")
                return None
            
            # Update state
            old_status = current_state.status
            current_state.status = new_status
            current_state.updated_at = datetime.utcnow().isoformat()
            
            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(current_state, key):
                    setattr(current_state, key, value)
            
            # Add to history
            current_state.status_history.append({
                "from_status": old_status.value,
                "to_status": new_status.value,
                "timestamp": current_state.updated_at,
                "details": kwargs
            })
            
            # Save updated state
            await self.save_state(current_state)
            
            logger.info(f"Transitioned issue #{issue_number}: {old_status.value} -> {new_status.value}")
            return current_state
            
        except Exception as e:
            logger.error(f"Failed to transition status: {e}")
            return None
    
    def _is_valid_transition(self, from_status: IssueStatus, to_status: IssueStatus) -> bool:
        """Validate if status transition is allowed."""
        
        # Define valid transitions
        valid_transitions = {
            IssueStatus.NEW: [IssueStatus.ANALYZING, IssueStatus.REJECTED],
            IssueStatus.ANALYZING: [IssueStatus.ANALYZED, IssueStatus.REJECTED],
            IssueStatus.ANALYZED: [IssueStatus.APPROVED, IssueStatus.REVIEW_NEEDED, IssueStatus.REJECTED],
            IssueStatus.APPROVED: [IssueStatus.IN_PROGRESS, IssueStatus.BLOCKED],
            IssueStatus.IN_PROGRESS: [IssueStatus.COMPLETED, IssueStatus.BLOCKED, IssueStatus.REVIEW_NEEDED],
            IssueStatus.BLOCKED: [IssueStatus.IN_PROGRESS, IssueStatus.REVIEW_NEEDED, IssueStatus.REJECTED],
            IssueStatus.REVIEW_NEEDED: [IssueStatus.APPROVED, IssueStatus.REJECTED, IssueStatus.IN_PROGRESS],
            IssueStatus.COMPLETED: [IssueStatus.MERGED, IssueStatus.CLOSED],
            IssueStatus.MERGED: [],  # Terminal state
            IssueStatus.CLOSED: [],  # Terminal state
            IssueStatus.REJECTED: []  # Terminal state
        }
        
        return to_status in valid_transitions.get(from_status, [])

# Global managers
state_manager = IssueStateManager()
github_manager = None

def initialize_github_manager(github_token: str):
    """Initialize GitHub manager with token."""
    global github_manager
    github_manager = GitHubStatusManager(github_token)

async def update_issue_status(repository: str, issue_number: int, new_status: IssueStatus, message: str = "", **kwargs):
    """Update issue status with GitHub integration."""
    try:
        # Transition status
        updated_state = await state_manager.transition_status(
            repository, issue_number, new_status, **kwargs
        )
        
        if not updated_state:
            logger.error(f"Failed to transition status for issue #{issue_number}")
            return False
        
        if github_manager:
            # Update GitHub labels
            await github_manager.update_issue_labels(repository, issue_number, new_status)
            
            # Post status comment
            await github_manager.post_status_comment(repository, issue_number, updated_state, message)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update issue status: {e}")
        return False

# FastAPI endpoints for status management
status_app = FastAPI(title="Issue Status Manager")

@status_app.post("/status/update")
async def update_status_endpoint(request: Request):
    """API endpoint to update issue status."""
    try:
        data = await request.json()
        
        repository = data.get("repository")
        issue_number = data.get("issue_number")
        status = data.get("status")
        message = data.get("message", "")
        
        if not all([repository, issue_number, status]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        try:
            new_status = IssueStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        success = await update_issue_status(
            repository, issue_number, new_status, message, **data.get("extra", {})
        )
        
        if success:
            return {"status": "updated", "issue_number": issue_number, "new_status": status}
        else:
            raise HTTPException(status_code=500, detail="Failed to update status")
            
    except Exception as e:
        logger.error(f"Status update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@status_app.get("/status/{repository}/{issue_number}")
async def get_status_endpoint(repository: str, issue_number: int):
    """Get current status of an issue."""
    try:
        issue_state = await state_manager.load_state(repository, issue_number)
        
        if not issue_state:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return {
            "issue_number": issue_state.issue_number,
            "repository": issue_state.repository,
            "status": issue_state.status.value,
            "assigned_agent": issue_state.assigned_agent,
            "confidence_score": issue_state.confidence_score,
            "estimated_cost": issue_state.estimated_cost,
            "estimated_hours": issue_state.estimated_hours,
            "created_at": issue_state.created_at,
            "updated_at": issue_state.updated_at,
            "pr_number": issue_state.pr_number,
            "branch_name": issue_state.branch_name,
            "error_message": issue_state.error_message,
            "status_history": issue_state.status_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Initialize for testing
    github_token = os.getenv("GITHUB_TOKEN", "")
    if github_token:
        initialize_github_manager(github_token)
    
    import uvicorn
    uvicorn.run(status_app, host="0.0.0.0", port=8001)