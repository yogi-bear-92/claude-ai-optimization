# 🔗 GitHub Webhook Configuration Guide

## 🎯 Setup GitHub Webhook for Automatic Issue Processing

To enable automatic processing of issues when they're created, you need to configure a GitHub webhook pointing to your deployed automation service.

## 📋 Webhook Configuration Steps

### 1. **Deploy the Automation Service**

First, ensure the automation service is deployed and accessible:

```bash
# Build and deploy the container
docker build -t github-automation-real-cost .
docker run -d -p 8000:8000 --name github-automation \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e CLAUDE_API_KEY=$CLAUDE_API_KEY \
  github-automation-real-cost

# Verify it's running
curl http://localhost:8000/health
```

### 2. **Configure GitHub Repository Webhook**

1. Go to your GitHub repository
2. Navigate to **Settings → Webhooks**
3. Click **Add webhook**
4. Configure:

| Setting | Value |
|---------|-------|
| **Payload URL** | `https://your-domain.com/webhook/github` |
| **Content type** | `application/json` |
| **Secret** | (Optional) Set WEBHOOK_SECRET env var |
| **Events** | Select "Issues" |
| **Active** | ✅ Checked |

### 3. **Required Events**

Enable these webhook events:
- ✅ **Issues** - For automatic issue processing
- ✅ **Pull requests** (optional) - For PR status updates

### 4. **Public Deployment Options**

For production use, deploy to a publicly accessible service:

#### **Option A: Azure Container Instances**
```bash
# Use the existing Azure deployment scripts
./deploy-simple.sh
```

#### **Option B: Railway/Render/Fly.io**
- Deploy the Docker container to any cloud platform
- Set environment variables for GITHUB_TOKEN and CLAUDE_API_KEY
- Get the public URL and use it for the webhook

#### **Option C: ngrok for Testing**
```bash
# For local testing only
ngrok http 8000
# Use the ngrok URL: https://abc123.ngrok.io/webhook/github
```

## 🧪 Testing the Webhook

### **Test Webhook Delivery**
1. Create a test issue in your repository
2. Check GitHub webhook delivery logs in Settings → Webhooks
3. Verify automation service logs:
   ```bash
   docker logs github-automation --tail 20
   ```

### **Expected Workflow**
```
Issue Created → Webhook Triggered → Automation Processes → Status Updates → PR Created → PR Merged → Issue Closed
```

## 🔒 Security Considerations

### **Webhook Security**
- Set `WEBHOOK_SECRET` environment variable
- Use HTTPS for production deployments
- Verify webhook payloads in production

### **GitHub Token Permissions**
Required permissions:
- ✅ **Issues** (read/write)
- ✅ **Pull requests** (read/write)
- ✅ **Contents** (read/write) - for creating commits
- ✅ **Metadata** (read) - for repository info

## 📊 Monitoring & Debugging

### **Service Endpoints**
- **Health Check**: `GET /health`
- **Statistics**: `GET /stats` 
- **Active Issues**: `GET /status/{repo}/{issue_number}`

### **Log Monitoring**
```bash
# Real-time logs
docker logs -f github-automation

# Check for webhook processing
docker logs github-automation | grep "📥 Received"

# Check for errors
docker logs github-automation | grep "ERROR"
```

## 🚀 Production Checklist

- [ ] Service deployed and accessible via HTTPS
- [ ] GitHub webhook configured with correct URL
- [ ] GITHUB_TOKEN with proper permissions set
- [ ] CLAUDE_API_KEY configured (optional)
- [ ] Webhook secret configured for security
- [ ] Test issue processed successfully
- [ ] Monitoring and logging set up

---

## ⚡ **Once webhook is configured, issues will be automatically processed!**

The system will:
1. **Analyze new issues** automatically
2. **Create PRs** for high-confidence fixes  
3. **Post status updates** with real cost information
4. **Close issues** when PRs are merged

**Ready for hands-free GitHub issue automation!** 🎉