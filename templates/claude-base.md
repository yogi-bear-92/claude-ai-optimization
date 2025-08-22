# Claude AI Optimization Configuration

## Project Context
This project uses optimized Claude AI agent configuration for maximum development efficiency and cost effectiveness. Based on analysis of 600+ agents with 50-70% development time reduction targets.

## Key Instructions for Claude

### Optimal Agent Selection
Use these carefully selected agents for specific tasks:

**Foundation Agents (High Priority)**:
- `comprehensive-researcher` - Deep analysis and research synthesis
- `code-reviewer` - Universal quality assurance and security review
- `backend-architect` - System design and API architecture (opus model)
- `security-auditor` - Vulnerability assessment and compliance (opus model)
- `performance-engineer` - Optimization and scaling analysis (opus model)

**Development Specialists**:
- `python-expert` - Python development and data science (sonnet-4)
- `typescript-expert` - TypeScript and frontend development (sonnet-4)
- `docker-expert` - Containerization and deployment (sonnet)
- `ai-engineer` - LLM integration and AI workflows (opus)

**Utility Agents**:
- `devops-troubleshooter` - Infrastructure debugging and deployment
- `test-automator` - Test creation and quality assurance

### Cost Optimization Strategy
**Model Assignment for Cost Efficiency**:
- **haiku**: Documentation, formatting, basic analysis (90% cost savings)
- **sonnet**: Standard development work, code review (balanced cost/performance)
- **opus**: Architecture, security, complex reasoning (maximum capability)
- **sonnet-4**: Latest features and cutting-edge capabilities (premium)

### Context Management
- **Auto-clear**: Sessions automatically clear after 40 minutes to prevent degradation
- **Preload**: Project context loads automatically for efficiency
- **Caching**: Response caching enabled for faster iterations

### Team Collaboration
- **Shared Config**: This CLAUDE.md is synchronized across vlada/Ai projects
- **Cost Tracking**: Usage monitored through ccflare dashboard and ccusage reports
- **Performance Metrics**: Development time and success rates tracked

### Integration Points
This project integrates with:
- **agent-factory**: Autonomous development patterns
- **PRPs-agentic-eng**: Process-driven engineering workflows
- **claude-hub**: GitHub integration and webhook automation
- **data-for-seo**: SEO optimization and content strategies
- **github-issue-automation**: Automated GitHub issue management and execution

### Monitoring & Alerts
- **Dashboard**: ccflare running at http://localhost:8080
- **Cost Tracking**: ccusage daily reports and budget alerts
- **Performance**: Development time and quality metrics
- **Budget Limits**: $50/day, $300/week with automated alerts

### Quick Commands
```bash
# View usage and costs
ccusage daily --breakdown

# Start monitoring dashboard  
ccflare --serve --port 8080

# Check optimization status
python monitoring/cost-tracker.py --report

# View agent configuration
python scripts/setup-optimal-agents.py --dry-run

# Test GitHub issue automation
python scripts/test-issue-automation.py --test-mode

# Start GitHub webhook handler
python integrations/github-webhook-handler.py --port 8000
```

### Expected Outcomes
Based on comprehensive optimization:
- **50-70% reduction** in development time
- **60-80% cost savings** through intelligent model routing
- **90% fewer context issues** through automatic management
- **Improved code quality** through specialized agent coordination

## Special Instructions
- Prefer efficient model usage (haiku for docs, sonnet for dev, opus for architecture)
- Use context management to maintain performance over long sessions
- Leverage specialized agents for domain-specific tasks
- Monitor costs and performance through integrated dashboards