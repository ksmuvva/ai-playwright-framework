"""Unit tests for E9.3 - Test Reporting skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e9_3_test_reporting import (
    ReportFormat,
    TestReport,
    TestReportingAgent,
    TestResult,
    TestStatus,
    TestSuite,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestReportFormat:
    @pytest.mark.unit
    def test_report_format_values(self):
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.JSON.value == "json"


class TestTestStatus:
    @pytest.mark.unit
    def test_test_status_values(self):
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"


class TestTestResult:
    @pytest.mark.unit
    def test_test_result_creation(self):
        result = TestResult(
            result_id="res_001",
            test_name="test_login",
            status=TestStatus.PASSED,
        )
        assert result.test_name == "test_login"


class TestTestSuite:
    @pytest.mark.unit
    def test_test_suite_creation(self):
        suite = TestSuite(
            suite_id="suite_001",
            suite_name="Login Tests",
        )
        assert suite.suite_name == "Login Tests"


class TestTestReport:
    @pytest.mark.unit
    def test_test_report_creation(self):
        report = TestReport(
            report_id="rep_001",
            title="Test Report",
            format=ReportFormat.HTML,
        )
        assert report.title == "Test Report"


class TestTestReportingAgent:
    @pytest.fixture
    def agent(self):
        return TestReportingAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e9_3_test_reporting"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_suite(self, agent):
        context = {"suite_name": "Login Tests"}
        result = await agent.run("create_suite", context)
        assert "suite" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_result(self, agent):
        context = {"test_name": "test_login", "status": TestStatus.PASSED}
        result = await agent.run("add_result", context)
        assert "result" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_report(self, agent):
        context = {"title": "Test Report", "format": ReportFormat.HTML}
        result = await agent.run("generate_report", context)
        assert "report" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
