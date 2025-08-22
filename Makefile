# Claude AI Optimization Framework Makefile

.PHONY: install test setup monitoring github-automation clean help

# Default target
help:
	@echo "Claude AI Optimization Framework"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@echo "  install              Install dependencies and setup environment"
	@echo "  setup                Configure agents and optimization settings"
	@echo "  test                 Run all tests and validations"
	@echo "  monitoring           Start monitoring dashboard"
	@echo "  github-automation    Test GitHub issue automation"
	@echo "  deploy-webhook       Deploy GitHub webhook handler"
	@echo "  cost-report          Generate cost optimization report"
	@echo "  clean                Clean temporary files and caches"

# Installation and setup
install:
	pip install -r requirements.txt
	pip install -e .

setup: install
	@echo "Setting up optimal agent configuration..."
	python scripts/setup-optimal-agents.py --install
	@echo "Testing cost tracking integration..."
	python monitoring/cost-tracker.py --test-mode
	@echo "Setup complete! ✅"

# Testing and validation
test:
	@echo "Running comprehensive test suite..."
	python scripts/test-issue-automation.py --test-mode
	python monitoring/cost-tracker.py --test-mode
	@echo "All tests passed! ✅"

# Monitoring and dashboards
monitoring:
	@echo "Starting monitoring dashboard..."
	python monitoring/usage-dashboard.py --start --port 8080

cost-report:
	@echo "Generating cost optimization report..."
	python monitoring/cost-tracker.py --report

# GitHub automation
github-automation:
	@echo "Testing GitHub issue automation..."
	python scripts/test-issue-automation.py --comprehensive

deploy-webhook:
	@echo "Starting GitHub webhook handler..."
	python integrations/github-webhook-handler.py --port 8000 --production

# Maintenance
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/

# Development shortcuts
dev-install: install
	pip install -e ".[dev]"

format:
	black .
	flake8 .

type-check:
	mypy .