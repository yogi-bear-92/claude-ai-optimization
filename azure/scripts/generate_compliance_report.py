#!/usr/bin/env python3
"""
Generate compliance and security reports from scan results
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceReportGenerator:
    """Generate comprehensive compliance reports from security scan results."""
    
    def __init__(self, scan_results_dir: str, output_file: str, format_type: str = "html"):
        self.scan_results_dir = Path(scan_results_dir)
        self.output_file = Path(output_file)
        self.format_type = format_type
        self.report_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repository": os.environ.get("GITHUB_REPOSITORY", "unknown"),
            "commit_sha": os.environ.get("GITHUB_SHA", "unknown"),
            "branch": os.environ.get("GITHUB_REF_NAME", "unknown"),
            "scans": {}
        }
    
    def collect_scan_results(self) -> None:
        """Collect all scan results from artifacts."""
        logger.info(f"Collecting scan results from {self.scan_results_dir}")
        
        # SAST Results
        self._collect_sast_results()
        
        # Dependency Scan Results
        self._collect_dependency_results()
        
        # Container Scan Results
        self._collect_container_results()
        
        # Secret Scan Results
        self._collect_secret_results()
        
        # License Scan Results
        self._collect_license_results()
    
    def _collect_sast_results(self) -> None:
        """Collect SAST scan results."""
        sast_dir = self.scan_results_dir / "sast-results"
        if not sast_dir.exists():
            logger.warning("SAST results directory not found")
            return
        
        sast_data = {"status": "completed", "findings": [], "tools": []}
        
        # Bandit results
        bandit_file = sast_dir / "bandit-results.json"
        if bandit_file.exists():
            try:
                with open(bandit_file) as f:
                    bandit_data = json.load(f)
                    sast_data["tools"].append("bandit")
                    
                    for result in bandit_data.get("results", []):
                        sast_data["findings"].append({
                            "tool": "bandit",
                            "severity": result.get("issue_severity", "unknown").lower(),
                            "file": result.get("filename", "unknown"),
                            "line": result.get("line_number", 0),
                            "description": result.get("issue_text", ""),
                            "rule_id": result.get("test_id", "")
                        })
            except json.JSONDecodeError:
                logger.error("Failed to parse Bandit results")
        
        # Semgrep SARIF results
        semgrep_file = sast_dir / "semgrep.sarif"
        if semgrep_file.exists():
            try:
                with open(semgrep_file) as f:
                    semgrep_data = json.load(f)
                    sast_data["tools"].append("semgrep")
                    
                    for run in semgrep_data.get("runs", []):
                        for result in run.get("results", []):
                            severity_map = {"error": "high", "warning": "medium", "info": "low"}
                            severity = severity_map.get(result.get("level", "info"), "low")
                            
                            location = result.get("locations", [{}])[0]
                            physical_location = location.get("physicalLocation", {})
                            artifact_location = physical_location.get("artifactLocation", {})
                            
                            sast_data["findings"].append({
                                "tool": "semgrep",
                                "severity": severity,
                                "file": artifact_location.get("uri", "unknown"),
                                "line": physical_location.get("region", {}).get("startLine", 0),
                                "description": result.get("message", {}).get("text", ""),
                                "rule_id": result.get("ruleId", "")
                            })
            except json.JSONDecodeError:
                logger.error("Failed to parse Semgrep SARIF results")
        
        self.report_data["scans"]["sast"] = sast_data
    
    def _collect_dependency_results(self) -> None:
        """Collect dependency scan results."""
        dep_dir = self.scan_results_dir / "dependency-scan-results"
        if not dep_dir.exists():
            logger.warning("Dependency scan results directory not found")
            return
        
        dep_data = {"status": "completed", "vulnerabilities": [], "tools": []}
        
        # Safety results
        safety_file = dep_dir / "safety-results.json"
        if safety_file.exists():
            try:
                with open(safety_file) as f:
                    safety_data = json.load(f)
                    dep_data["tools"].append("safety")
                    
                    for vuln in safety_data:
                        dep_data["vulnerabilities"].append({
                            "tool": "safety",
                            "package": vuln.get("package", "unknown"),
                            "version": vuln.get("installed_version", "unknown"),
                            "vulnerability_id": vuln.get("vulnerability_id", ""),
                            "description": vuln.get("advisory", ""),
                            "severity": "high"  # Safety typically reports high-severity issues
                        })
            except json.JSONDecodeError:
                logger.error("Failed to parse Safety results")
        
        # Snyk results
        snyk_file = dep_dir / "snyk-results.json"
        if snyk_file.exists():
            try:
                with open(snyk_file) as f:
                    snyk_data = json.load(f)
                    dep_data["tools"].append("snyk")
                    
                    for vuln in snyk_data.get("vulnerabilities", []):
                        dep_data["vulnerabilities"].append({
                            "tool": "snyk",
                            "package": vuln.get("packageName", "unknown"),
                            "version": vuln.get("version", "unknown"),
                            "vulnerability_id": vuln.get("id", ""),
                            "description": vuln.get("title", ""),
                            "severity": vuln.get("severity", "unknown").lower()
                        })
            except json.JSONDecodeError:
                logger.error("Failed to parse Snyk results")
        
        self.report_data["scans"]["dependencies"] = dep_data
    
    def _collect_container_results(self) -> None:
        """Collect container scan results."""
        container_dir = self.scan_results_dir / "container-scan-results"
        if not container_dir.exists():
            logger.warning("Container scan results directory not found")
            return
        
        container_data = {"status": "completed", "vulnerabilities": [], "tools": []}
        
        # Trivy results
        trivy_file = container_dir / "trivy-fs-results.json"
        if trivy_file.exists():
            try:
                with open(trivy_file) as f:
                    trivy_data = json.load(f)
                    container_data["tools"].append("trivy")
                    
                    for result in trivy_data.get("Results", []):
                        for vuln in result.get("Vulnerabilities", []):
                            container_data["vulnerabilities"].append({
                                "tool": "trivy",
                                "package": vuln.get("PkgName", "unknown"),
                                "version": vuln.get("InstalledVersion", "unknown"),
                                "vulnerability_id": vuln.get("VulnerabilityID", ""),
                                "description": vuln.get("Title", ""),
                                "severity": vuln.get("Severity", "unknown").lower()
                            })
            except json.JSONDecodeError:
                logger.error("Failed to parse Trivy results")
        
        self.report_data["scans"]["containers"] = container_data
    
    def _collect_secret_results(self) -> None:
        """Collect secret scan results."""
        secret_dir = self.scan_results_dir / "secret-scan-results"
        if not secret_dir.exists():
            logger.warning("Secret scan results directory not found")
            return
        
        secret_data = {"status": "completed", "secrets_found": 0, "files_scanned": 0}
        
        # detect-secrets results
        secrets_file = secret_dir / "secrets-baseline.json"
        if secrets_file.exists():
            try:
                with open(secrets_file) as f:
                    secrets_data = json.load(f)
                    secret_data["files_scanned"] = len(secrets_data.get("results", {}))
                    
                    total_secrets = 0
                    for file_path, secrets in secrets_data.get("results", {}).items():
                        total_secrets += len(secrets)
                    
                    secret_data["secrets_found"] = total_secrets
            except json.JSONDecodeError:
                logger.error("Failed to parse secrets results")
        
        self.report_data["scans"]["secrets"] = secret_data
    
    def _collect_license_results(self) -> None:
        """Collect license scan results."""
        license_dir = self.scan_results_dir / "license-scan-results"
        if not license_dir.exists():
            logger.warning("License scan results directory not found")
            return
        
        license_data = {"status": "completed", "licenses": [], "compliance": True}
        
        # pip-licenses results
        licenses_file = license_dir / "licenses.json"
        if licenses_file.exists():
            try:
                with open(licenses_file) as f:
                    licenses_data = json.load(f)
                    
                    approved_licenses = {
                        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", 
                        "ISC", "Apache Software License", "BSD License"
                    }
                    
                    for package in licenses_data:
                        license_name = package.get("License", "Unknown")
                        is_approved = license_name in approved_licenses
                        
                        license_data["licenses"].append({
                            "package": package.get("Name", "unknown"),
                            "version": package.get("Version", "unknown"),
                            "license": license_name,
                            "approved": is_approved
                        })
                        
                        if not is_approved:
                            license_data["compliance"] = False
            
            except json.JSONDecodeError:
                logger.error("Failed to parse license results")
        
        self.report_data["scans"]["licenses"] = license_data
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate executive summary of all scans."""
        summary = {
            "total_scans": len(self.report_data["scans"]),
            "scans_passed": 0,
            "scans_failed": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "overall_status": "pass"
        }
        
        # Count issues by severity
        for scan_type, scan_data in self.report_data["scans"].items():
            if scan_data.get("status") == "completed":
                summary["scans_passed"] += 1
            else:
                summary["scans_failed"] += 1
            
            # Count vulnerabilities/findings
            findings = []
            if "findings" in scan_data:
                findings = scan_data["findings"]
            elif "vulnerabilities" in scan_data:
                findings = scan_data["vulnerabilities"]
            
            for finding in findings:
                severity = finding.get("severity", "unknown").lower()
                if severity == "critical":
                    summary["critical_issues"] += 1
                elif severity == "high":
                    summary["high_issues"] += 1
                elif severity == "medium":
                    summary["medium_issues"] += 1
                elif severity == "low":
                    summary["low_issues"] += 1
        
        # Determine overall status
        if summary["critical_issues"] > 0 or summary["scans_failed"] > 0:
            summary["overall_status"] = "fail"
        elif summary["high_issues"] > 0:
            summary["overall_status"] = "warning"
        
        self.report_data["summary"] = summary
        return summary
    
    def generate_html_report(self) -> str:
        """Generate HTML compliance report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Security Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e9ecef; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .scan-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ color: #28a745; }}
        .fail {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .critical {{ background-color: #f8d7da; }}
        .high {{ background-color: #fff3cd; }}
        .medium {{ background-color: #d1ecf1; }}
        .low {{ background-color: #d4edda; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Compliance Report</h1>
        <p><strong>Repository:</strong> {repository}</p>
        <p><strong>Branch:</strong> {branch}</p>
        <p><strong>Commit:</strong> {commit_sha}</p>
        <p><strong>Generated:</strong> {generated_at}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p><strong>Overall Status:</strong> <span class="{overall_status}">{overall_status_text}</span></p>
        <p><strong>Total Scans:</strong> {total_scans}</p>
        <p><strong>Scans Passed:</strong> {scans_passed}</p>
        <p><strong>Scans Failed:</strong> {scans_failed}</p>
        
        <h3>Issue Breakdown</h3>
        <ul>
            <li><span class="critical">Critical: {critical_issues}</span></li>
            <li><span class="high">High: {high_issues}</span></li>
            <li><span class="medium">Medium: {medium_issues}</span></li>
            <li><span class="low">Low: {low_issues}</span></li>
        </ul>
    </div>
    
    {scan_details}
</body>
</html>
        """
        
        summary = self.generate_summary()
        
        # Generate scan details
        scan_details = ""
        for scan_type, scan_data in self.report_data["scans"].items():
            scan_details += f'<div class="scan-section">'
            scan_details += f'<h3>{scan_type.upper()} Scan</h3>'
            scan_details += f'<p><strong>Status:</strong> {scan_data.get("status", "unknown")}</p>'
            
            if "findings" in scan_data and scan_data["findings"]:
                scan_details += '<table><tr><th>File</th><th>Severity</th><th>Description</th><th>Rule ID</th></tr>'
                for finding in scan_data["findings"][:20]:  # Limit to first 20
                    severity = finding.get("severity", "unknown")
                    scan_details += f'''
                    <tr class="{severity}">
                        <td>{finding.get("file", "unknown")}</td>
                        <td>{severity}</td>
                        <td>{finding.get("description", "")[:100]}</td>
                        <td>{finding.get("rule_id", "")}</td>
                    </tr>
                    '''
                scan_details += '</table>'
            
            elif "vulnerabilities" in scan_data and scan_data["vulnerabilities"]:
                scan_details += '<table><tr><th>Package</th><th>Version</th><th>Severity</th><th>CVE</th></tr>'
                for vuln in scan_data["vulnerabilities"][:20]:  # Limit to first 20
                    severity = vuln.get("severity", "unknown")
                    scan_details += f'''
                    <tr class="{severity}">
                        <td>{vuln.get("package", "unknown")}</td>
                        <td>{vuln.get("version", "unknown")}</td>
                        <td>{severity}</td>
                        <td>{vuln.get("vulnerability_id", "")}</td>
                    </tr>
                    '''
                scan_details += '</table>'
            
            scan_details += '</div>'
        
        return html_template.format(
            repository=self.report_data["repository"],
            branch=self.report_data["branch"],
            commit_sha=self.report_data["commit_sha"][:8],
            generated_at=self.report_data["generated_at"],
            overall_status=summary["overall_status"],
            overall_status_text=summary["overall_status"].upper(),
            total_scans=summary["total_scans"],
            scans_passed=summary["scans_passed"],
            scans_failed=summary["scans_failed"],
            critical_issues=summary["critical_issues"],
            high_issues=summary["high_issues"],
            medium_issues=summary["medium_issues"],
            low_issues=summary["low_issues"],
            scan_details=scan_details
        )
    
    def generate_report(self) -> None:
        """Generate the compliance report."""
        logger.info("Collecting scan results...")
        self.collect_scan_results()
        
        logger.info("Generating report...")
        if self.format_type.lower() == "html":
            report_content = self.generate_html_report()
        else:
            report_content = json.dumps(self.report_data, indent=2)
        
        logger.info(f"Writing report to {self.output_file}")
        with open(self.output_file, 'w') as f:
            f.write(report_content)
        
        logger.info("Compliance report generated successfully")

def main():
    parser = argparse.ArgumentParser(description="Generate compliance report from security scan results")
    parser.add_argument("--scan-results", required=True, help="Directory containing scan results")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--format", choices=["html", "json"], default="html", help="Report format")
    
    args = parser.parse_args()
    
    try:
        generator = ComplianceReportGenerator(args.scan_results, args.output, args.format)
        generator.generate_report()
        print(f"✅ Compliance report generated: {args.output}")
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()