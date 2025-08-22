#!/usr/bin/env python3
"""
Setup script for Claude AI Optimization Framework
Installs the complete system including GitHub issue automation.
"""

from setuptools import setup, find_packages

setup(
    name="claude-ai-optimization",
    version="1.1.0",
    description="Comprehensive Claude AI optimization framework with GitHub issue automation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=12.0.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.20.0",
        "pydantic>=1.10.0",
        "python-multipart>=0.0.5",
        "aiofiles>=22.0.0",
        "httpx>=0.24.0",
        "jinja2>=3.1.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.2.0",
        "textblob>=0.17.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "claude-optimize=scripts.setup_optimal_agents:main",
            "claude-cost-tracker=monitoring.cost_tracker:main",
            "claude-dashboard=monitoring.usage_dashboard:main",
            "claude-issue-automation=scripts.test_issue_automation:main",
            "claude-webhook-handler=integrations.github_webhook_handler:main",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)