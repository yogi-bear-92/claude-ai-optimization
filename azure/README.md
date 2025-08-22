# 🚀 Claude AI Issue Automation - Production Ready

## 🎯 **STATUS: LIVE PRODUCTION SYSTEM**

This repository now uses **automatic issue resolution** with real-time GitHub integration and accurate AI cost calculation.

> **Next issue created will be automatically processed!** 🤖

See [PRODUCTION.md](PRODUCTION.md) for full system documentation.

---

# Azure Deployment Guide

## Update Credentials

### Option 1: Interactive Script (Recommended)
```bash
cd azure
./update-credentials.sh
```
This will prompt you for:
- GitHub Personal Access Token
- Claude API Key  
- Webhook Secret (optional - auto-generated if not provided)

### Option 2: Quick Update (Provide values directly)
```bash
cd azure
./quick-update.sh 'your_github_token' 'your_claude_api_key' 'your_webhook_secret'
```

### Option 3: Manual Azure CLI
```bash
# Delete existing container
az container delete --resource-group claude-ai-rg --name claude-ai-issue-automation --yes

# Create new one with updated credentials
az container create \
    --resource-group claude-ai-rg \
    --name claude-ai-issue-automation \
    --image claudeaioptimization.azurecr.io/issue-automation:latest \
    --registry-login-server claudeaioptimization.azurecr.io \
    --registry-username claudeaioptimization \
    --registry-password $(az acr credential show --name claudeaioptimization --query 'passwords[0].value' --output tsv) \
    --dns-name-label claude-ai-issue-automation \
    --ports 8000 \
    --os-type Linux \
    --environment-variables \
        PORT=8000 \
        HOST=0.0.0.0 \
        GITHUB_TOKEN='your_actual_github_token' \
        CLAUDE_API_KEY='your_actual_claude_api_key' \
        WEBHOOK_SECRET='your_actual_webhook_secret' \
    --cpu 0.5 \
    --memory 1 \
    --restart-policy Always
```

### Option 4: Azure Portal (GUI)
1. Go to [portal.azure.com](https://portal.azure.com)
2. Navigate to **Resource Groups** → **claude-ai-rg**  
3. Click **claude-ai-issue-automation**
4. Go to **Settings** → **Containers**
5. Edit environment variables
6. Click **Save** and restart

## Required Credentials

### GitHub Personal Access Token
- Go to: https://github.com/settings/personal-access-tokens
- Required scopes: `repo`, `issues`, `contents`
- Format: `ghp_xxxxxxxxxxxx`

### Claude API Key  
- Go to: https://console.anthropic.com/
- Create API key
- Format: `sk-ant-xxxxxxxxxxxx`

### Webhook Secret
- Any secure random string
- Used to verify webhook authenticity
- Generate with: `openssl rand -hex 32`

## Verification

After updating credentials, test the deployment:

```bash
# Check health
curl http://claude-ai-issue-automation.eastus.azurecontainer.io:8000/health

# Check credential status
curl http://claude-ai-issue-automation.eastus.azurecontainer.io:8000/stats

# Create test issue to trigger automation
gh issue create --title "Test automation" --body "Testing updated credentials"
```

## Troubleshooting

### Check container logs
```bash
az container logs --resource-group claude-ai-rg --name claude-ai-issue-automation
```

### Restart container
```bash
az container restart --resource-group claude-ai-rg --name claude-ai-issue-automation
```

### Delete and redeploy
```bash
cd azure
./deploy-simple.sh
```

## Current Deployment Info

- **Webhook URL**: `http://claude-ai-issue-automation.eastus.azurecontainer.io:8000/webhook/github`
- **Health Check**: `http://claude-ai-issue-automation.eastus.azurecontainer.io:8000/health`
- **Resource Group**: `claude-ai-rg`
- **Container Registry**: `claudeaioptimization.azurecr.io`
- **GitHub Webhook ID**: `565478283`