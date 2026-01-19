"""
Agent implementations for Claude Playwright Agent.
"""

from claude_playwright_agent.agents.base import BaseAgent, get_settings
from claude_playwright_agent.agents.test_agent import TestAgent
from claude_playwright_agent.agents.debug_agent import DebugAgent
from claude_playwright_agent.agents.report_agent import ReportAgent
from claude_playwright_agent.agents.ingest_agent import IngestionAgent
from claude_playwright_agent.agents.bdd_agent import BDDConversionAgent
from claude_playwright_agent.agents.dedup_agent import DeduplicationAgent
from claude_playwright_agent.agents.exec_agent import ExecutionAgent
from claude_playwright_agent.agents.recording_agent import RecordingAgent
from claude_playwright_agent.agents.api_agent import APITestingAgent
from claude_playwright_agent.agents.performance_agent import PerformanceAgent
from claude_playwright_agent.agents.accessibility_agent import AccessibilityAgent
from claude_playwright_agent.agents.visual_regression_agent import VisualRegressionAgent
from claude_playwright_agent.agents.orchestrator import (
    AgentMessage,
    AgentLifecycleManager,
    AgentTask,
    MessageQueue,
    MessageType,
    get_orchestrator,
    OrchestratorAgent,
)
from claude_playwright_agent.agents.playwright_parser import (
    Action,
    ActionType,
    ParsedRecording,
    PlaywrightRecordingParser,
    SelectorInfo,
    SelectorType,
    FragilityLevel,
    parse_recording,
    parse_recording_content,
)
from claude_playwright_agent.agents.bdd_conversion import (
    BDDConverter,
    convert_to_gherkin,
    save_feature_file,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
    StepDefinitionGenerator,
    StepKeyword,
)
from claude_playwright_agent.agents.deduplication import (
    PageElement,
    PageObject,
    analyze_patterns,
    generate_page_objects,
    PageObjectGenerator,
    DeduplicationEngine,
    DeduplicationResult,
    SelectorPattern,
    SimilarityMetric,
)
from claude_playwright_agent.agents.execution import (
    TestExecutionEngine,
    TestFramework,
    TestStatus,
    TestResult,
    ExecutionResult,
    RetryConfig,
    execute_tests,
)
from claude_playwright_agent.agents.reporting import (
    TestMetric,
    ReportFormat,
    ReportSection,
    TestReport,
    ReportGenerator,
    create_report,
)
from claude_playwright_agent.agents.failure_analysis import (
    FailureCategory,
    Severity,
    FixSuggestion,
    Failure,
    FailureCluster,
    FlakyTest,
    AnalysisResult,
    FailureAnalyzer,
    analyze_failures,
)
from claude_playwright_agent.agents.self_healing import (
    HealingStatus,
    HealingStrategy,
    SelectorHealing,
    HealingAttempt,
    HealingConfig,
    SelfHealingEngine,
    analyze_selector_for_healing,
    heal_selector,
)
from claude_playwright_agent.agents.health import (
    HealthStatus,
    HealthCheckResult,
    AgentHealth,
    HealthChecker,
    AgentHealthMonitor,
    HealthCheckCommand,
    get_health_monitor,
)

__all__ = [
    # Base
    "BaseAgent",
    "get_settings",
    # Specialist Agents
    "TestAgent",
    "DebugAgent",
    "ReportAgent",
    "IngestionAgent",
    "BDDConversionAgent",
    "DeduplicationAgent",
    "ExecutionAgent",
    "RecordingAgent",
    "APITestingAgent",
    "PerformanceAgent",
    "AccessibilityAgent",
    "VisualRegressionAgent",
    # Orchestrator
    "OrchestratorAgent",
    "get_orchestrator",
    # Orchestration Components
    "AgentMessage",
    "AgentTask",
    "MessageType",
    "MessageQueue",
    "AgentLifecycleManager",
    # Playwright Parser
    "Action",
    "ActionType",
    "ParsedRecording",
    "PlaywrightParser",
    "SelectorInfo",
    "parse_recording",
    "parse_recording_content",
    # BDD Conversion
    "BDDConverter",
    "convert_to_gherkin",
    "save_feature_file",
    "GherkinFeature",
    "GherkinScenario",
    "GherkinStep",
    "StepDefinitionGenerator",
    "StepKeyword",
    # Deduplication
    "PageElement",
    "PageObject",
    "analyze_patterns",
    "generate_page_objects",
    "PageObjectGenerator",
    "DeduplicationEngine",
    "DeduplicationResult",
    "SelectorPattern",
    "SimilarityMetric",
    # Execution
    "TestExecutionEngine",
    "TestFramework",
    "TestStatus",
    "TestResult",
    "ExecutionResult",
    "RetryConfig",
    "execute_tests",
    # Reporting
    "TestMetric",
    "ReportFormat",
    "ReportSection",
    "TestReport",
    "ReportGenerator",
    "create_report",
    # Failure Analysis
    "FailureCategory",
    "Severity",
    "FixSuggestion",
    "Failure",
    "FailureCluster",
    "FlakyTest",
    "AnalysisResult",
    "FailureAnalyzer",
    "analyze_failures",
    # Self-Healing
    "HealingStatus",
    "HealingStrategy",
    "SelectorHealing",
    "HealingAttempt",
    "HealingConfig",
    "SelfHealingEngine",
    "analyze_selector_for_healing",
    "heal_selector",
    # Health Monitoring
    "HealthStatus",
    "HealthCheckResult",
    "AgentHealth",
    "HealthChecker",
    "AgentHealthMonitor",
    "HealthCheckCommand",
    "get_health_monitor",
]
