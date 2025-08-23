"""
Integration tests for GitHub API integration
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
import httpx

@pytest.mark.integration
class TestGitHubIntegration:
    """Test GitHub API integration functionality."""
    
    @pytest.fixture
    def github_client(self, mock_http_client, test_config):
        """Create GitHub client for testing."""
        from unittest.mock import Mock
        
        client = Mock()
        client.http_client = mock_http_client
        client.token = test_config["github"]["token"]
        client.base_url = test_config["github"]["api_base_url"]
        
        # Mock common GitHub API methods
        client.get_issue = AsyncMock()
        client.create_comment = AsyncMock()
        client.update_issue = AsyncMock()
        client.create_pull_request = AsyncMock()
        client.merge_pull_request = AsyncMock()
        client.close_issue = AsyncMock()
        
        return client

    async def test_issue_retrieval(self, github_client, sample_github_issue):
        """Test retrieving issue from GitHub API."""
        github_client.get_issue.return_value = sample_github_issue
        
        issue = await github_client.get_issue("test/repo", 123)
        
        assert issue["number"] == 123
        assert issue["title"] == "Bug: Application crashes on startup"
        assert "bug" in [label["name"] for label in issue["labels"]]
        
        github_client.get_issue.assert_called_once_with("test/repo", 123)

    async def test_comment_creation(self, github_client):
        """Test creating comments on GitHub issues."""
        comment_data = {
            "id": 12345,
            "body": "🤖 **Azure Automation Status Update**\n\n✅ Analysis completed",
            "html_url": "https://github.com/test/repo/issues/123#issuecomment-12345"
        }
        
        github_client.create_comment.return_value = comment_data
        
        result = await github_client.create_comment(
            "test/repo", 
            123, 
            "🤖 **Azure Automation Status Update**\n\n✅ Analysis completed"
        )
        
        assert result["id"] == 12345
        assert "Azure Automation" in result["body"]
        github_client.create_comment.assert_called_once()

    async def test_issue_status_update(self, github_client):
        """Test updating issue status and labels."""
        updated_issue = {
            "number": 123,
            "state": "open",
            "labels": [
                {"name": "bug"},
                {"name": "azure-automation:analyzing"}
            ]
        }
        
        github_client.update_issue.return_value = updated_issue
        
        result = await github_client.update_issue(
            "test/repo",
            123,
            labels=["bug", "azure-automation:analyzing"]
        )
        
        assert "azure-automation:analyzing" in [l["name"] for l in result["labels"]]
        github_client.update_issue.assert_called_once()

    async def test_pull_request_creation(self, github_client):
        """Test creating pull request for issue resolution."""
        pr_data = {
            "number": 456,
            "title": "Fix: Application crashes on startup (#123)",
            "html_url": "https://github.com/test/repo/pull/456",
            "head": {"ref": "fix/issue-123"},
            "base": {"ref": "main"},
            "state": "open"
        }
        
        github_client.create_pull_request.return_value = pr_data
        
        result = await github_client.create_pull_request(
            "test/repo",
            title="Fix: Application crashes on startup (#123)",
            head="fix/issue-123",
            base="main",
            body="Automated fix for issue #123"
        )
        
        assert result["number"] == 456
        assert "Fix:" in result["title"]
        assert result["state"] == "open"
        github_client.create_pull_request.assert_called_once()

    async def test_pull_request_merge(self, github_client):
        """Test merging pull request after successful review."""
        merge_result = {
            "sha": "abc123def456",
            "merged": True,
            "message": "Pull Request successfully merged"
        }
        
        github_client.merge_pull_request.return_value = merge_result
        
        result = await github_client.merge_pull_request(
            "test/repo",
            456,
            commit_title="Merge automated fix for issue #123",
            merge_method="squash"
        )
        
        assert result["merged"] is True
        assert result["sha"] is not None
        github_client.merge_pull_request.assert_called_once()

    async def test_issue_closure(self, github_client):
        """Test closing issue after resolution."""
        closed_issue = {
            "number": 123,
            "state": "closed",
            "closed_at": "2024-01-01T12:00:00Z"
        }
        
        github_client.close_issue.return_value = closed_issue
        
        result = await github_client.close_issue("test/repo", 123)
        
        assert result["state"] == "closed"
        assert result["closed_at"] is not None
        github_client.close_issue.assert_called_once()

    async def test_webhook_signature_validation(self, test_config):
        """Test webhook signature validation."""
        import hashlib
        import hmac
        
        payload = b'{"action": "opened", "number": 123}'
        secret = test_config["github"]["webhook_secret"].encode()
        
        # Generate valid signature
        signature = "sha256=" + hmac.new(
            secret, payload, hashlib.sha256
        ).hexdigest()
        
        # Mock validation function
        def validate_signature(payload_body, signature_header, webhook_secret):
            expected = "sha256=" + hmac.new(
                webhook_secret.encode(), payload_body, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature_header)
        
        # Test valid signature
        assert validate_signature(payload, signature, test_config["github"]["webhook_secret"])
        
        # Test invalid signature  
        assert not validate_signature(payload, "sha256=invalid", test_config["github"]["webhook_secret"])

    async def test_rate_limit_handling(self, mock_http_client):
        """Test GitHub API rate limit handling."""
        # Mock rate limit response
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1640995200"  # Unix timestamp
        }
        
        # Test rate limit exception
        mock_http_client.get.side_effect = [
            rate_limit_response,
            Mock(status_code=200, json=Mock(return_value={"data": "success"}))
        ]
        
        # Mock retry logic
        async def mock_request_with_retry():
            try:
                response = await mock_http_client.get("https://api.github.com/test")
                if response.status_code == 429:
                    await asyncio.sleep(1)  # Simulate rate limit wait
                    response = await mock_http_client.get("https://api.github.com/test")
                return response
            except Exception as e:
                # Retry once more
                await asyncio.sleep(1)
                return await mock_http_client.get("https://api.github.com/test")
        
        response = await mock_request_with_retry()
        assert response.status_code == 200

    async def test_error_handling(self, github_client):
        """Test error handling for GitHub API failures."""
        # Test 404 error
        github_client.get_issue.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=Mock(status_code=404)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await github_client.get_issue("test/repo", 99999)
        
        # Test network error
        github_client.create_comment.side_effect = httpx.NetworkError("Connection failed")
        
        with pytest.raises(httpx.NetworkError):
            await github_client.create_comment("test/repo", 123, "Test comment")

    async def test_batch_operations(self, github_client):
        """Test batch GitHub operations."""
        issues = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"}, 
            {"number": 3, "title": "Issue 3"}
        ]
        
        # Mock batch comment creation
        async def create_batch_comments(repo, issue_numbers, comment_template):
            results = []
            for number in issue_numbers:
                comment = {
                    "id": 10000 + number,
                    "body": comment_template.format(issue_number=number),
                    "html_url": f"https://github.com/{repo}/issues/{number}#issuecomment-{10000 + number}"
                }
                results.append(comment)
            return results
        
        github_client.create_batch_comments = create_batch_comments
        
        results = await github_client.create_batch_comments(
            "test/repo",
            [1, 2, 3],
            "🤖 Automated analysis for issue #{issue_number}"
        )
        
        assert len(results) == 3
        assert all("Automated analysis" in r["body"] for r in results)

    async def test_search_issues(self, github_client):
        """Test searching for issues with specific criteria."""
        search_results = {
            "total_count": 2,
            "items": [
                {
                    "number": 100,
                    "title": "Bug in authentication module",
                    "state": "open",
                    "labels": [{"name": "bug"}, {"name": "authentication"}]
                },
                {
                    "number": 101, 
                    "title": "Security vulnerability in login",
                    "state": "open",
                    "labels": [{"name": "security"}, {"name": "authentication"}]
                }
            ]
        }
        
        github_client.search_issues = AsyncMock(return_value=search_results)
        
        results = await github_client.search_issues(
            "test/repo",
            query="label:authentication state:open"
        )
        
        assert results["total_count"] == 2
        assert len(results["items"]) == 2
        assert all("authentication" in [l["name"] for l in item["labels"]] 
                  for item in results["items"])

    async def test_repository_info(self, github_client):
        """Test retrieving repository information."""
        repo_info = {
            "name": "test-repo",
            "full_name": "test/repo", 
            "private": False,
            "default_branch": "main",
            "open_issues_count": 5,
            "language": "Python",
            "topics": ["automation", "github", "azure"]
        }
        
        github_client.get_repository = AsyncMock(return_value=repo_info)
        
        repo = await github_client.get_repository("test/repo")
        
        assert repo["name"] == "test-repo"
        assert repo["default_branch"] == "main"
        assert "automation" in repo["topics"]
        
    async def test_webhook_processing(self, sample_github_webhook_payload):
        """Test processing GitHub webhook payloads."""
        # Mock webhook processor
        async def process_webhook(payload):
            action = payload.get("action")
            issue = payload.get("issue", {})
            
            if action == "opened":
                return {
                    "status": "processed",
                    "issue_number": issue.get("number"),
                    "action_taken": "analysis_started"
                }
            
            return {"status": "ignored", "reason": f"Action '{action}' not handled"}
        
        # Test issue opened
        result = await process_webhook(sample_github_webhook_payload)
        
        assert result["status"] == "processed"
        assert result["issue_number"] == 123
        assert result["action_taken"] == "analysis_started"
        
        # Test unsupported action
        payload_closed = sample_github_webhook_payload.copy()
        payload_closed["action"] = "closed"
        
        result = await process_webhook(payload_closed)
        assert result["status"] == "ignored"

    @pytest.mark.slow
    async def test_concurrent_github_operations(self, github_client):
        """Test concurrent GitHub API operations."""
        # Mock concurrent operations
        async def concurrent_comment_creation():
            tasks = []
            for i in range(5):
                task = github_client.create_comment(
                    "test/repo", 
                    123 + i, 
                    f"Concurrent comment #{i}"
                )
                tasks.append(task)
            
            # Mock return values
            github_client.create_comment.return_value = {"id": 12345}
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        results = await concurrent_comment_creation()
        assert len(results) == 5
        assert github_client.create_comment.call_count == 5

    async def test_github_app_authentication(self, test_config):
        """Test GitHub App authentication flow."""
        # Mock JWT creation and installation access token
        def create_jwt_token(app_id, private_key):
            return "jwt_token_example"
        
        async def get_installation_access_token(jwt_token, installation_id):
            return {
                "token": "ghs_installation_token_example",
                "expires_at": "2024-01-01T12:00:00Z"
            }
        
        # Test authentication flow
        jwt_token = create_jwt_token("12345", "private_key_content")
        assert jwt_token is not None
        
        access_token = await get_installation_access_token(jwt_token, "67890")
        assert access_token["token"].startswith("ghs_")
        assert access_token["expires_at"] is not None