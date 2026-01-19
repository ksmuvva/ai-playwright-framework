"""
Accessibility Agent - Agent for WCAG accessibility testing and compliance.
"""

from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class AccessibilityAgent(BaseAgent):
    """
    Agent for WCAG accessibility testing and compliance verification.

    Handles:
    - WCAG 2.1 Level A, AA, AAA compliance checking
    - axe-core integration for automated testing
    - Violation categorization and prioritization
    - Accessibility improvement recommendations
    - Accessible component testing
    """

    WCAG_LEVELS = ["A", "AA", "AAA"]

    def __init__(
        self,
        mcp_servers: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> None:
        """Initialize the Accessibility Agent."""
        system_prompt = """You are an accessibility testing expert specializing in WCAG compliance and inclusive design.

Your responsibilities:
1. Run automated accessibility tests using axe-core
2. Categorize violations by WCAG level (A, AA, AAA)
3. Prioritize issues by impact (critical, serious, moderate, minor)
4. Provide actionable remediation steps
5. Suggest accessible alternatives for problematic patterns

WCAG Guidelines:
- Level A: Essential accessibility requirements
- Level AA: Standard compliance target
- Level AAA: Enhanced accessibility (optional)

Impact Levels:
- Critical: Blocks functionality for screen reader users
- Serious: Significantly impairs usability
- Moderate: Causes confusion or difficulty
- Minor: Minimal impact on usability

When analyzing:
- Focus on real-world impact on users with disabilities
- Consider keyboard navigation, screen reader compatibility, color contrast
- Provide specific code-level remediation advice
- Include ARIA patterns and HTML semantics guidance"""

        default_tools = [
            "Read",
            "Write",
            "run_accessibility_scan",
            "check_wcag_compliance",
            "analyze_violations",
            "generate_accessibility_report",
        ]

        super().__init__(
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools or default_tools,
        )

    async def run_accessibility_scan(
        self,
        page_url: str,
        context_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run an accessibility scan on a page.

        Args:
            page_url: URL or page reference to scan
            context_options: Optional browser context options

        Returns:
            Accessibility scan results with violations
        """
        await self.initialize()

        prompt = f"""Run an accessibility scan on this page: {page_url}

Please perform the following checks:
1. Image alt text verification
2. Form label association
3. Keyboard navigation testing
4. ARIA attributes validation
5. Color contrast analysis
6. Heading structure verification
7. Link text uniqueness
8. Table structure validation
9. Focus management review
10. Skip link availability

Return a comprehensive report with all violations found."""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "page_url": page_url,
                "scan_results": "\n".join(response_parts),
                "violations_count": self._count_violations("\n".join(response_parts)),
                "timestamp": self._get_timestamp(),
            }

    def _count_violations(self, text: str) -> dict[str, int]:
        """Count violations by severity from scan results."""
        return {
            "critical": text.lower().count("critical") + text.lower().count("severe"),
            "serious": text.lower().count("serious"),
            "moderate": text.lower().count("moderate"),
            "minor": text.lower().count("minor"),
        }

    async def check_wcag_compliance(
        self,
        page_url: str,
        target_level: str = "AA",
        include_partials: bool = True,
    ) -> dict[str, Any]:
        """
        Check WCAG compliance at a specific level.

        Args:
            page_url: URL to check
            target_level: WCAG level (A, AA, AAA)
            include_partials: Whether to include partial failures

        Returns:
            WCAG compliance report with pass/fail for each criterion
        """
        await self.initialize()

        level_guidelines = {
            "A": [
                "1.1.1",
                "1.2.1",
                "1.2.2",
                "1.2.3",
                "1.3.1",
                "1.3.2",
                "1.3.3",
                "1.4.1",
                "2.1.1",
                "2.1.2",
                "2.2.1",
                "2.2.2",
                "2.3.1",
                "2.4.1",
                "2.4.2",
                "2.4.3",
                "2.4.4",
                "3.1.1",
                "3.2.1",
                "3.2.2",
                "3.3.1",
                "4.1.1",
                "4.1.2",
            ],
            "AA": [
                "1.2.4",
                "1.2.5",
                "1.4.3",
                "1.4.4",
                "1.4.5",
                "2.4.5",
                "2.4.6",
                "2.4.7",
                "3.1.2",
                "3.2.3",
                "3.2.4",
                "3.3.2",
                "3.3.3",
                "3.3.4",
            ],
            "AAA": [
                "1.2.6",
                "1.2.7",
                "1.2.8",
                "1.2.9",
                "1.4.6",
                "1.4.7",
                "1.4.8",
                "1.4.9",
                "2.1.3",
                "2.2.3",
                "2.2.4",
                "2.3.2",
                "2.4.8",
                "2.4.9",
                "2.4.10",
                "3.1.3",
                "3.1.4",
                "3.1.5",
                "3.1.6",
                "3.2.5",
                "3.2.6",
                "3.3.5",
                "3.3.6",
            ],
        }

        guidelines = level_guidelines.get(target_level, level_guidelines["AA"])

        prompt = f"""Check WCAG 2.1 {target_level} compliance for: {page_url}

Check these success criteria:
{chr(10).join(guidelines)}

For each criterion:
1. Verify if it passes, fails, or needs manual review
2. Note specific violations found
3. Provide remediation advice
4. Mark for manual review if automated testing is insufficient

Return results in structured format."""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "page_url": page_url,
                "target_level": target_level,
                "criteria_checked": len(guidelines),
                "results": "\n".join(response_parts),
                "timestamp": self._get_timestamp(),
            }

    async def analyze_violations(
        self,
        violations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze accessibility violations and prioritize fixes.

        Args:
            violations: List of accessibility violations

        Returns:
            Prioritized remediation plan
        """
        await self.initialize()

        prompt = f"""Analyze these accessibility violations and create a prioritized remediation plan:

{self._format_violations(violations)}

For each violation:
1. Identify the root cause
2. Estimate remediation effort (small, medium, large)
3. Prioritize based on impact and frequency
4. Provide specific code fixes
5. Suggest testing approach

Return a prioritized list with:
- Priority order
- Violation description
- WCAG criterion reference
- Remediation code
- Testing steps"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "violations_analyzed": len(violations),
                "remediation_plan": "\n".join(response_parts),
                "timestamp": self._get_timestamp(),
            }

    def _format_violations(self, violations: list[dict[str, Any]]) -> str:
        """Format violations for analysis."""
        return "\n".join(
            [
                f"- {v.get('id', 'Unknown')}: {v.get('impact', 'unknown')} impact - {v.get('description', 'No description')}"
                for v in violations
            ]
        )

    async def generate_accessibility_report(
        self,
        scan_results: dict[str, Any],
        output_format: str = "markdown",
    ) -> dict[str, Any]:
        """
        Generate a comprehensive accessibility report.

        Args:
            scan_results: Results from accessibility scan
            output_format: Report format (markdown, html, json)

        Returns:
            Formatted accessibility report
        """
        await self.initialize()

        violations_count = scan_results.get("violations_count", {})

        if output_format == "markdown":
            report = self._generate_markdown_report(scan_results)
        elif output_format == "html":
            report = self._generate_html_report(scan_results)
        else:
            report = scan_results

        return {
            "report": report,
            "format": output_format,
            "summary": {
                "total_violations": sum(violations_count.values()),
                "critical": violations_count.get("critical", 0),
                "serious": violations_count.get("serious", 0),
                "moderate": violations_count.get("moderate", 0),
                "minor": violations_count.get("minor", 0),
            },
            "timestamp": self._get_timestamp(),
        }

    def _generate_markdown_report(self, scan_results: dict[str, Any]) -> str:
        """Generate markdown accessibility report."""
        violations = scan_results.get("violations", [])
        summary = scan_results.get("violations_count", {})

        report = f"""# Accessibility Report

## Summary

| Metric | Count |
|--------|-------|
| Total Violations | {summary.get("total", 0)} |
| Critical | {summary.get("critical", 0)} |
| Serious | {summary.get("serious", 0)} |
| Moderate | {summary.get("moderate", 0)} |
| Minor | {summary.get("minor", 0)} |

## Violations

"""
        for v in violations[:20]:
            report += f"""### {v.get("id", "Unknown")}

- **Impact:** {v.get("impact", "unknown")}
- **Description:** {v.get("description", "No description")}
- **WCAG Criterion:** {v.get("wcag_criterion", "N/A")}
- **Help:** {v.get("help", "No help available")}
- **Help URL:** {v.get("helpUrl", "N/A")}

"""

        return report

    def _generate_html_report(self, scan_results: dict[str, Any]) -> str:
        """Generate HTML accessibility report."""
        violations = scan_results.get("violations", [])
        summary = scan_results.get("violations_count", {})

        impact_colors = {
            "critical": "#dc3545",
            "serious": "#fd7e14",
            "moderate": "#ffc107",
            "minor": "#17a2b8",
        }

        violation_rows = ""
        for v in violations[:30]:
            impact = v.get("impact", "minor")
            color = impact_colors.get(impact, "#6c757d")
            violation_rows += f"""
            <tr>
                <td><span style="color: {color}; font-weight: bold;">{v.get("id", "Unknown")}</span></td>
                <td><span class="badge badge-{impact}">{impact}</span></td>
                <td>{v.get("description", "N/A")[:100]}</td>
                <td>{v.get("wcag_criterion", "N/A")}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .header {{ background: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px; background: #e0e0e0; }}
        .metric {{ text-align: center; padding: 20px; background: white; }}
        .metric-value {{ font-size: 28px; font-weight: bold; }}
        .metric-label {{ font-size: 11px; color: #6c757d; text-transform: uppercase; }}
        .critical {{ color: #dc3545; }}
        .serious {{ color: #fd7e14; }}
        .moderate {{ color: #ffc107; }}
        .minor {{ color: #17a2b8; }}
        .section {{ padding: 20px; }}
        .section h2 {{ margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .badge-critical {{ background: #f8d7da; color: #721c24; }}
        .badge-serious {{ background: #ffe5d0; color: #8a4b1c; }}
        .badge-moderate {{ background: #fff3cd; color: #856404; }}
        .badge-minor {{ background: #d1ecf1; color: #0c5460; }}
        .footer {{ text-align: center; color: #6c757d; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>Accessibility Report</h1>
                <p>{scan_results.get("page_url", "N/A")}</p>
            </div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{summary.get("total", 0)}</div>
                    <div class="metric-label">Total</div>
                </div>
                <div class="metric">
                    <div class="metric-value critical">{summary.get("critical", 0)}</div>
                    <div class="metric-label">Critical</div>
                </div>
                <div class="metric">
                    <div class="metric-value serious">{summary.get("serious", 0)}</div>
                    <div class="metric-label">Serious</div>
                </div>
                <div class="metric">
                    <div class="metric-value moderate">{summary.get("moderate", 0)}</div>
                    <div class="metric-label">Moderate</div>
                </div>
                <div class="metric">
                    <div class="metric-value minor">{summary.get("minor", 0)}</div>
                    <div class="metric-label">Minor</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section">
                <h2>Violations</h2>
                {f"<table><tr><th>ID</th><th>Impact</th><th>Description</th><th>WCAG</th></tr>{violation_rows}</table>" if violation_rows else "<p>No violations found!</p>"}
            </div>
        </div>

        <div class="footer">
            <p>Claude Playwright Framework - Accessibility Report</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "run_accessibility_scan")

        if action == "run_accessibility_scan":
            return await self.run_accessibility_scan(
                page_url=input_data["page_url"],
                context_options=input_data.get("context_options"),
            )
        elif action == "check_wcag_compliance":
            return await self.check_wcag_compliance(
                page_url=input_data["page_url"],
                target_level=input_data.get("target_level", "AA"),
                include_partials=input_data.get("include_partials", True),
            )
        elif action == "analyze_violations":
            return await self.analyze_violations(
                violations=input_data["violations"],
            )
        elif action == "generate_accessibility_report":
            return await self.generate_accessibility_report(
                scan_results=input_data["scan_results"],
                output_format=input_data.get("output_format", "markdown"),
            )
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
