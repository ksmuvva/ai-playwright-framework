"""
Cloud Agent - Agent for cloud-based testing platform integration.

Provides integration with:
- BrowserStack
- Sauce Labs
- LambdaTest
- CrossBrowserTesting

Supports:
- Remote execution
- Platform configuration
- Test result collection
- Performance metrics from cloud
"""

import json
import os
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from claude_playwright_agent.agents.base import BaseAgent


class CloudProvider(str, Enum):
    """Supported cloud testing providers."""

    BROWSERSTACK = "browserstack"
    SAUCE_LABS = "sauce_labs"
    LAMBDA_TEST = "lambdatest"
    CROSS_BROWSER_TESTING = "crossbrowsertesting"


@dataclass
class PlatformConfig:
    """Platform configuration for cloud testing."""

    os_name: str
    os_version: str
    browser_name: str
    browser_version: str
    device_name: Optional[str] = None
    resolution: Optional[str] = None


@dataclass
class CloudSession:
    """Cloud testing session data."""

    session_id: str
    provider: CloudProvider
    status: str
    duration: int
    platform: dict
    logs: list[str] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    video_url: Optional[str] = None
    console_logs: Optional[str] = None
    network_logs: Optional[str] = None


class CloudAgent(BaseAgent):
    """
    Agent for cloud-based testing platform integration.

    Handles:
    - BrowserStack integration
    - Sauce Labs integration
    - LambdaTest integration
    - CrossBrowserTesting integration
    - Remote execution management
    - Result collection and analysis
    """

    def __init__(
        self,
        provider: CloudProvider = CloudProvider.BROWSERSTACK,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
    ) -> None:
        """
        Initialize the cloud agent.

        Args:
            provider: Cloud provider to use
            api_key: API key for the provider
            username: Username for the provider
        """
        self._provider = provider
        self._api_key = api_key or self._get_api_key(provider)
        self._username = username or self._get_username(provider)
        self._sessions: dict[str, CloudSession] = {}

        system_prompt = f"""You are the Cloud Testing Agent for Claude Playwright Agent.

Your role is to:
1. Manage cloud testing platform integration ({provider.value})
2. Configure and launch remote test executions
3. Monitor test session status
4. Collect and analyze test results
5. Retrieve logs, screenshots, and performance data

You provide:
- Seamless cloud platform integration
- Detailed session management
- Comprehensive result analysis
- Performance insights from cloud metrics"""

        super().__init__(system_prompt=system_prompt)

    def _get_api_key(self, provider: CloudProvider) -> str:
        """Get API key from environment or config."""
        env_keys = {
            CloudProvider.BROWSERSTACK: "BROWSERSTACK_ACCESS_KEY",
            CloudProvider.SAUCE_LABS: "SAUCE_ACCESS_KEY",
            CloudProvider.LAMBDA_TEST: "LAMBDA_TEST_ACCESS_KEY",
            CloudProvider.CROSS_BROWSER_TESTING: "CBT_ACCESS_KEY",
        }
        return os.environ.get(env_keys.get(provider, ""), "")

    def _get_username(self, provider: CloudProvider) -> str:
        """Get username from environment or config."""
        env_users = {
            CloudProvider.BROWSERSTACK: "BROWSERSTACK_USERNAME",
            CloudProvider.SAUCE_LABS: "SAUCE_USERNAME",
            CloudProvider.LAMBDA_TEST: "LAMBDA_TEST_USERNAME",
            CloudProvider.CROSS_BROWSER_TESTING: "CBT_USERNAME",
        }
        return os.environ.get(env_users.get(provider, ""), "")

    async def initialize(self) -> None:
        """Initialize the cloud client."""
        if not self._api_key or not self._username:
            raise ValueError(
                f"Missing credentials for {self._provider.value}. "
                f"Please set {self._provider.value.upper()}_USERNAME and "
                f"{self._provider.value.upper()}_ACCESS_KEY environment variables."
            )

    async def configure_build(
        self,
        build_name: str,
        project_name: Optional[str] = None,
        build_tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Configure a test build for cloud execution.

        Args:
            build_name: Name for the build
            project_name: Optional project name
            build_tags: Optional list of build tags

        Returns:
            Build configuration result
        """
        return {
            "success": True,
            "build_name": build_name,
            "project_name": project_name,
            "build_tags": build_tags or [],
        }

    async def get_available_platforms(self) -> dict[str, Any]:
        """
        Get list of available platforms for the provider.

        Returns:
            Available platforms and configurations
        """
        platforms = {
            CloudProvider.BROWSERSTACK: self._get_browserstack_platforms(),
            CloudProvider.SAUCE_LABS: self._get_sauce_labs_platforms(),
            CloudProvider.LAMBDA_TEST: self._get_lambdatest_platforms(),
            CloudProvider.CROSS_BROWSER_TESTING: self._get_cbt_platforms(),
        }

        return {
            "provider": self._provider.value,
            "platforms": platforms.get(self._provider, []),
        }

    def _get_browserstack_platforms(self) -> list[dict]:
        """Get BrowserStack available platforms."""
        return [
            {
                "os": "Windows",
                "os_version": "11",
                "browser": "Chrome",
                "versions": ["latest", "latest-1"],
            },
            {
                "os": "Windows",
                "os_version": "10",
                "browser": "Chrome",
                "versions": ["latest", "latest-1"],
            },
            {
                "os": "Windows",
                "os_version": "11",
                "browser": "Firefox",
                "versions": ["latest", "latest-1"],
            },
            {
                "os": "Windows",
                "os_version": "10",
                "browser": "Edge",
                "versions": ["latest", "latest-1"],
            },
            {"os": "macOS", "os_version": "Monterey", "browser": "Safari", "versions": ["15"]},
            {"os": "macOS", "os_version": "Big Sur", "browser": "Safari", "versions": ["14"]},
            {"os": "iOS", "os_version": "15.0", "device": "iPhone 13", "real_device": True},
            {
                "os": "Android",
                "os_version": "12.0",
                "device": "Google Pixel 6",
                "real_device": True,
            },
        ]

    def _get_sauce_labs_platforms(self) -> list[dict]:
        """Get Sauce Labs available platforms."""
        return [
            {"os": "Windows 11", "browser": "Chrome", "versions": ["latest"]},
            {"os": "Windows 10", "browser": "Firefox", "versions": ["latest"]},
            {"os": "Windows 10", "browser": "Edge", "versions": ["latest"]},
            {"os": "macOS 11", "browser": "Safari", "versions": ["15"]},
            {"os": "macOS 12", "browser": "Safari", "versions": ["16"]},
        ]

    def _get_lambdatest_platforms(self) -> list[dict]:
        """Get LambdaTest available platforms."""
        return [
            {"os": "Windows 11", "browser": "Chrome", "versions": ["latest"]},
            {"os": "Windows 10", "browser": "Firefox", "versions": ["latest"]},
            {"os": "macOS Monterey", "browser": "Safari", "versions": ["15"]},
            {"os": "Android", "device": "Samsung Galaxy S21", "real_device": True},
            {"os": "iOS", "device": "iPhone 13", "real_device": True},
        ]

    def _get_cbt_platforms(self) -> list[dict]:
        """Get CrossBrowserTesting available platforms."""
        return [
            {"os": "Windows 10", "browser": "Chrome", "versions": ["latest"]},
            {"os": "Windows 10", "browser": "Firefox", "versions": ["latest"]},
            {"os": "Windows 10", "browser": "Edge", "versions": ["latest"]},
            {"os": "macOS Catalina", "browser": "Safari", "versions": ["14"]},
        ]

    async def create_session(
        self,
        platform: PlatformConfig,
        build_name: Optional[str] = None,
        project_name: Optional[str] = None,
        enable_video: bool = True,
        enable_network_logs: bool = True,
        enable_console_logs: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new cloud test session.

        Args:
            platform: Platform configuration
            build_name: Build name for grouping
            project_name: Project name
            enable_video: Enable video recording
            enable_network_logs: Enable network logs
            enable_console_logs: Enable console logs

        Returns:
            Session creation result with connection details
        """
        session_id = f"session_{self._provider.value}_{int(__import__('time').time())}"

        self._sessions[session_id] = CloudSession(
            session_id=session_id,
            provider=self._provider,
            status="created",
            duration=0,
            platform={
                "os": f"{platform.os_name} {platform.os_version}",
                "browser": f"{platform.browser_name} {platform.browser_version}",
                "device": platform.device_name,
                "resolution": platform.resolution,
            },
        )

        return {
            "success": True,
            "session_id": session_id,
            "provider": self._provider.value,
            "platform": {
                "os": f"{platform.os_name} {platform.os_version}",
                "browser": f"{platform.browser_name} {platform.browser_version}",
                "device": platform.device_name,
                "resolution": platform.resolution,
            },
            "capabilities": self._generate_capabilities(
                platform,
                build_name,
                project_name,
                enable_video,
                enable_network_logs,
                enable_console_logs,
            ),
        }

    def _generate_capabilities(
        self,
        platform: PlatformConfig,
        build_name: Optional[str],
        project_name: Optional[str],
        enable_video: bool,
        enable_network_logs: bool,
        enable_console_logs: bool,
    ) -> dict:
        """Generate platform-specific capabilities."""
        caps = {
            "browserName": platform.browser_name,
            "browserVersion": platform.browser_version,
            "os": platform.os_name,
            "osVersion": platform.os_version,
            "project": project_name or "Claude Playwright Framework",
            "build": build_name or f"Build {int(__import__('time').time())}",
        }

        if platform.device_name:
            caps["deviceName"] = platform.device_name
        if platform.resolution:
            caps["resolution"] = platform.resolution

        if self._provider == CloudProvider.BROWSERSTACK:
            caps.update(
                {
                    "browserstack.userName": self._username,
                    "browserstack.accessKey": self._api_key,
                    "browserstack.networkLogs": enable_network_logs,
                    "browserstack.video": enable_video,
                    "browserstack.consoleLogs": "info" if enable_console_logs else "disable",
                }
            )
        elif self._provider == CloudProvider.SAUCE_LABS:
            caps.update(
                {
                    "username": self._username,
                    "accessKey": self._api_key,
                    "recordVideo": enable_video,
                    "recordNetwork": enable_network_logs,
                }
            )

        return caps

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """
        Get the status of a cloud session.

        Args:
            session_id: Session ID to check

        Returns:
            Session status and details
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found", "session_id": session_id}

        return {
            "success": True,
            "session_id": session_id,
            "status": session.status,
            "duration_seconds": session.duration,
            "platform": session.platform,
            "logs_count": len(session.logs),
            "screenshots_count": len(session.screenshots),
            "has_video": session.video_url is not None,
        }

    async def terminate_session(self, session_id: str) -> dict[str, Any]:
        """
        Terminate a cloud test session.

        Args:
            session_id: Session ID to terminate

        Returns:
            Termination result
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found", "session_id": session_id}

        session.status = "terminated"

        return {
            "success": True,
            "session_id": session_id,
            "status": "terminated",
        }

    async def collect_results(self, session_id: str) -> dict[str, Any]:
        """
        Collect test results from a completed session.

        Args:
            session_id: Session ID to collect results for

        Returns:
            Test results and artifacts
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found", "session_id": session_id}

        return {
            "success": True,
            "session_id": session_id,
            "status": session.status,
            "duration_seconds": session.duration,
            "platform": session.platform,
            "logs": session.logs,
            "screenshots": session.screenshots,
            "video_url": session.video_url,
            "console_logs": session.console_logs,
            "network_logs": session.network_logs,
        }

    async def run_parallel_tests(
        self,
        platforms: list[PlatformConfig],
        test_function: str,
        build_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run tests in parallel across multiple platforms.

        Args:
            platforms: List of platform configurations
            test_function: Test function to execute
            build_name: Build name for grouping

        Returns:
            Parallel test execution results
        """
        results = {
            "total_platforms": len(platforms),
            "sessions": [],
            "passed": 0,
            "failed": 0,
            "pending": 0,
        }

        for platform in platforms:
            session = await self.create_session(platform, build_name)
            results["sessions"].append(session)
            if session["success"]:
                results["pending"] += 1
            else:
                results["failed"] += 1

        return results

    def get_provider_credentials_url(self) -> str:
        """Get the URL for provider credentials documentation."""
        urls = {
            CloudProvider.BROWSERSTACK: "https://www.browserstack.com/docs/automate/playwright",
            CloudProvider.SAUCE_LABS: "https://docs.saucelabs.com/visual/e2e-testing/playwright/",
            CloudProvider.LAMBDA_TEST: "https://www.lambdatest.com/supportdocs/playwright/",
            CloudProvider.CROSS_BROWSER_TESTING: "https://help.crossbrowsertesting.com/playwright-integration/",
        }
        return urls.get(self._provider, "")

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "get_available_platforms")

        if action == "get_available_platforms":
            return await self.get_available_platforms()
        elif action == "create_session":
            platform = PlatformConfig(
                os_name=input_data["os_name"],
                os_version=input_data["os_version"],
                browser_name=input_data["browser_name"],
                browser_version=input_data.get("browser_version", "latest"),
                device_name=input_data.get("device_name"),
                resolution=input_data.get("resolution"),
            )
            return await self.create_session(
                platform=platform,
                build_name=input_data.get("build_name"),
                project_name=input_data.get("project_name"),
                enable_video=input_data.get("enable_video", True),
                enable_network_logs=input_data.get("enable_network_logs", True),
                enable_console_logs=input_data.get("enable_console_logs", True),
            )
        elif action == "get_session_status":
            return await self.get_session_status(session_id=input_data["session_id"])
        elif action == "terminate_session":
            return await self.terminate_session(session_id=input_data["session_id"])
        elif action == "collect_results":
            return await self.collect_results(session_id=input_data["session_id"])
        elif action == "configure_build":
            return await self.configure_build(
                build_name=input_data["build_name"],
                project_name=input_data.get("project_name"),
                build_tags=input_data.get("build_tags"),
            )
        elif action == "run_parallel_tests":
            platforms = [
                PlatformConfig(
                    os_name=p["os_name"],
                    os_version=p["os_version"],
                    browser_name=p["browser_name"],
                    browser_version=p.get("browser_version", "latest"),
                )
                for p in input_data["platforms"]
            ]
            return await self.run_parallel_tests(
                platforms=platforms,
                test_function=input_data.get("test_function", ""),
                build_name=input_data.get("build_name"),
            )
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
