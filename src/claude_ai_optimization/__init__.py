"""
Claude AI Optimization - Intelligent GitHub Issue Automation

This package provides AI-powered automation for GitHub issue resolution
with smart agent selection and cross-repository intelligence.
"""

__version__ = "1.0.0"
__author__ = "Vlada AI Team"
__email__ = "ai@vlada.dev"

# Re-export main components
from .azure import AzureIssueAutomation

__all__ = ["AzureIssueAutomation", "__version__"]