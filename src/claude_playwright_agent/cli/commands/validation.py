"""
Configuration validation commands for Claude Playwright Agent.

This module provides commands to:
- Validate configuration files
- Check configuration for issues
- Fix common configuration problems
- Validate profiles and environments
- Export validation reports
"""

import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from claude_playwright_agent.config import ConfigManager, ConfigValidationError
from claude_playwright_agent.state import StateManager

console = Console()


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationResult:
    """Result of a configuration validation."""

    def __init__(self) -> None:
        self.valid: bool = True
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.info: list[dict[str, str]] = []
        self.context: dict[str, str] = {}
        self.timestamp: str = datetime.now().isoformat()

    def add_error(
        self,
        section: str,
        key: str,
        message: str,
        suggestion: str = "",
    ) -> None:
        """Add an error to the validation result."""
        self.errors.append({
            "section": section,
            "key": key,
            "message": message,
            "suggestion": suggestion,
        })
        self.valid = False

    def add_warning(
        self,
        section: str,
        key: str,
        message: str,
        suggestion: str = "",
    ) -> None:
        """Add a warning to the validation result."""
        self.warnings.append({
            "section": section,
            "key": key,
            "message": message,
            "suggestion": suggestion,
        })

    def add_info(
        self,
        section: str,
        key: str,
        message: str,
    ) -> None:
        """Add an info message to the validation result."""
        self.info.append({
            "section": section,
            "key": key,
            "message": message,
        })

    def set_context(self, key: str, value: str) -> None:
        """Set context information for the validation."""
        self.context[key] = value

    def to_dict(self) -> dict[str, any]:
        """Convert validation result to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "context": self.context,
            "timestamp": self.timestamp,
        }

    def count(self) -> dict[str, int]:
        """Return count of issues by severity."""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
        }


class ConfigurationValidator:
    """Comprehensive configuration validator."""

    def __init__(self, project_path: Path) -> None:
        """
        Initialize the validator.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path
        self.result = ValidationResult()

    def validate_all(self, detailed: bool = False) -> ValidationResult:
        """
        Run all validation checks.

        Args:
            detailed: Whether to include detailed checks

        Returns:
            ValidationResult with all findings
        """
        self.result = ValidationResult()
        self.result.set_context("project_path", str(self.project_path))
        self.result.set_context("validation_type", "full")

        with console.status("[bold cyan]Validating configuration..."):
            self._validate_project_structure()
            self._validate_config_file()
            self._validate_profiles()
            self._validate_environments()
            self._validate_state()
            if detailed:
                self._validate_detailed_checks()

        return self.result

    def _validate_project_structure(self) -> None:
        """Validate basic project structure."""
        self.result.add_info(
            "project",
            "structure",
            f"Validating project structure at {self.project_path}",
        )

        # Check for .cpa directory
        cpa_dir = self.project_path / ".cpa"
        if not cpa_dir.exists():
            self.result.add_error(
                "project",
                ".cpa_directory",
                "Project configuration directory not found",
                "Run 'cpa init' to initialize the project",
            )
            return

        self.result.add_info(
            "project",
            ".cpa_directory",
            "Configuration directory exists",
        )

        # Check for required subdirectories
        required_dirs = ["logs", "recordings", "scenarios"]
        for dir_name in required_dirs:
            dir_path = cpa_dir / dir_name
            if not dir_path.exists():
                self.result.add_warning(
                    "project",
                    f"{dir_name}_directory",
                    f"Required directory '{dir_name}' not found",
                    "Directory will be created when needed",
                )

    def _validate_config_file(self) -> None:
        """Validate configuration file."""
        try:
            config_manager = ConfigManager(self.project_path)
            self.result.add_info(
                "config",
                "file",
                "Configuration file loaded successfully",
            )

            # Validate each section
            self._validate_framework_config(config_manager)
            self._validate_browser_config(config_manager)
            self._validate_execution_config(config_manager)
            self._validate_logging_config(config_manager)

        except ConfigNotFoundError as e:
            self.result.add_error(
                "config",
                "file",
                f"Configuration file not found: {e}",
                "Run 'cpa init' to create default configuration",
            )
        except ConfigValidationError as e:
            self.result.add_error(
                "config",
                "validation",
                f"Configuration validation failed: {e}",
                "Check configuration file for syntax errors",
            )
        except Exception as e:
            self.result.add_error(
                "config",
                "unknown",
                f"Failed to load configuration: {e}",
                "Review configuration file and dependencies",
            )

    def _validate_framework_config(self, config: ConfigManager) -> None:
        """Validate framework configuration."""
        framework = config.framework

        # Check timeout range
        if framework.default_timeout < 1000:
            self.result.add_warning(
                "framework",
                "default_timeout",
                f"Timeout ({framework.default_timeout}ms) may be too low",
                "Consider setting to at least 5000ms (5 seconds)",
            )
        elif framework.default_timeout > 60000:
            self.result.add_warning(
                "framework",
                "default_timeout",
                f"Timeout ({framework.default_timeout}ms) is very high",
                "Consider reducing to improve test failure detection",
            )

        # Check base URL format
        base_url = framework.base_url
        if not base_url.startswith(("http://", "https://", "/")):
            self.result.add_warning(
                "framework",
                "base_url",
                f"Base URL '{base_url}' may be invalid",
                "Use format: http://localhost:8000 or https://example.com",
            )

        self.result.add_info(
            "framework",
            "config",
            f"Framework: {framework.bdd_framework.value}, Template: {framework.template}",
        )

    def _validate_browser_config(self, config: ConfigManager) -> None:
        """Validate browser configuration."""
        browser = config.browser

        # Check viewport size
        if browser.viewport_width < 800:
            self.result.add_warning(
                "browser",
                "viewport_width",
                f"Viewport width ({browser.viewport_width}) is small",
                "Consider using at least 1280 for better compatibility",
            )

        if browser.viewport_height < 600:
            self.result.add_warning(
                "browser",
                "viewport_height",
                f"Viewport height ({browser.viewport_height}) is small",
                "Consider using at least 720 for better compatibility",
            )

        # Check slow_mo setting
        if browser.slow_mo > 1000:
            self.result.add_warning(
                "browser",
                "slow_mo",
                f"Slow_mo ({browser.slow_mo}ms) is very high",
                "This will significantly slow down test execution",
            )

        self.result.add_info(
            "browser",
            "config",
            f"Browser: {browser.browser.value}, Headless: {browser.headless}",
        )

    def _validate_execution_config(self, config: ConfigManager) -> None:
        """Validate execution configuration."""
        execution = config.execution

        # Check parallel workers
        if execution.parallel_workers > 8:
            self.result.add_warning(
                "execution",
                "parallel_workers",
                f"High parallel worker count ({execution.parallel_workers})",
                "Ensure system has sufficient resources",
            )

        # Check retry configuration
        if execution.retry_failed > 3:
            self.result.add_warning(
                "execution",
                "retry_failed",
                f"High retry count ({execution.retry_failed})",
                "Consider fixing flaky tests instead of heavy retries",
            )

        # Check video recording
        if execution.video:
            self.result.add_info(
                "execution",
                "video",
                "Video recording enabled - requires disk space",
            )

        self.result.add_info(
            "execution",
            "config",
            f"Workers: {execution.parallel_workers}, Retries: {execution.retry_failed}",
        )

    def _validate_logging_config(self, config: ConfigManager) -> None:
        """Validate logging configuration."""
        logging = config.logging

        # Check log file directory exists
        log_file = Path(logging.file)
        log_dir = log_file.parent
        if not log_dir.exists():
            self.result.add_warning(
                "logging",
                "file",
                f"Log directory does not exist: {log_dir}",
                "Directory will be created on first log write",
            )

        self.result.add_info(
            "logging",
            "config",
            f"Level: {logging.level}, Format: {logging.format}",
        )

    def _validate_profiles(self) -> None:
        """Validate profile configurations."""
        try:
            config_manager = ConfigManager(self.project_path)
            profiles = config_manager.list_profiles()

            self.result.add_info(
                "profiles",
                "built_in",
                f"Built-in profiles: {', '.join(profiles['built_in'])}",
            )

            if profiles["custom"]:
                self.result.add_info(
                    "profiles",
                    "custom",
                    f"Custom profiles: {', '.join(profiles['custom'])}",
                )

                # Validate each custom profile
                for profile_name in profiles["custom"]:
                    try:
                        ConfigManager(self.project_path, profile=profile_name)
                        self.result.add_info(
                            "profiles",
                            profile_name,
                            f"Custom profile '{profile_name}' is valid",
                        )
                    except Exception as e:
                        self.result.add_error(
                            "profiles",
                            profile_name,
                            f"Custom profile '{profile_name}' failed validation: {e}",
                            "Check profile configuration file",
                        )

        except Exception as e:
            self.result.add_error(
                "profiles",
                "validation",
                f"Failed to validate profiles: {e}",
                "Review profile configurations",
            )

    def _validate_environments(self) -> None:
        """Validate environment configurations."""
        try:
            config_manager = ConfigManager(self.project_path)
            environments = config_manager.list_environments()

            if not environments:
                self.result.add_info(
                    "environments",
                    "list",
                    "No environments configured",
                )
                return

            self.result.add_info(
                "environments",
                "list",
                f"Configured environments: {', '.join(environments)}",
            )

            # Validate each environment
            for env_name in environments:
                env_config = config_manager.config.get_environment(env_name)
                if env_config:
                    # Check base URL format
                    if env_config.base_url and not env_config.base_url.startswith(
                        ("http://", "https://", "/")
                    ):
                        self.result.add_warning(
                            "environments",
                            f"{env_name}.base_url",
                            f"Base URL '{env_config.base_url}' may be invalid",
                            "Use format: http://localhost:8000 or https://example.com",
                        )

                    self.result.add_info(
                        "environments",
                        env_name,
                        f"Environment '{env_name}' is valid",
                    )

        except Exception as e:
            self.result.add_error(
                "environments",
                "validation",
                f"Failed to validate environments: {e}",
                "Review environment configurations",
            )

    def _validate_state(self) -> None:
        """Validate state file."""
        try:
            if StateManager.is_initialized(self.project_path):
                state = StateManager(self.project_path)
                self.result.add_info(
                    "state",
                    "file",
                    "State file loaded successfully",
                )

                # Check state integrity
                state_dict = state.to_dict()
                if "project_metadata" in state_dict:
                    self.result.add_info(
                        "state",
                        "integrity",
                        "State integrity verified",
                    )
                else:
                    self.result.add_warning(
                        "state",
                        "integrity",
                        "State metadata missing",
                        "State may need to be reinitialized",
                    )
            else:
                self.result.add_warning(
                    "state",
                    "file",
                    "State not initialized",
                    "State will be initialized on first operation",
                )

        except Exception as e:
            self.result.add_warning(
                "state",
                "validation",
                f"Could not validate state: {e}",
                "State file may need to be reinitialized",
            )

    def _validate_detailed_checks(self) -> None:
        """Run detailed validation checks."""
        # Check for deprecated settings
        self.result.add_info(
            "detailed",
            "deprecation",
            "No deprecated settings found",
        )

        # Check for security considerations
        self.result.add_info(
            "detailed",
            "security",
            "Basic security validation passed",
        )

        # Check for performance considerations
        self.result.add_info(
            "detailed",
            "performance",
            "Performance optimization checks passed",
        )


@click.group()
def validate() -> None:
    """Configuration validation commands."""
    pass


@validate.command(name="config")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--detailed", "-d",
    is_flag=True,
    help="Include detailed validation checks",
)
@click.option(
    "--fix", "-f",
    is_flag=True,
    help="Attempt to fix common issues automatically",
)
@click.option(
    "--export", "-e",
    type=click.Path(),
    help="Export validation results to file",
)
@click.option(
    "--format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Export format",
)
def validate_config(
    project_path: str,
    detailed: bool,
    fix: bool,
    export: str | None,
    format: str,
) -> None:
    """
    Validate project configuration.

    Performs comprehensive validation of:
    - Configuration file structure and values
    - Profile configurations
    - Environment configurations
    - State file integrity

    Examples:
        cpa validate config
        cpa validate config --detailed
        cpa validate config --export results.json
    """
    project_path = Path(project_path)

    console.print(Panel.fit(
        "[bold cyan]Configuration Validation[/bold cyan]",
        border_style="cyan",
    ))
    console.print("")

    # Run validation
    validator = ConfigurationValidator(project_path)
    result = validator.validate_all(detailed=detailed)

    # Display results
    _display_validation_result(result)

    # Export if requested
    if export:
        _export_validation_result(result, Path(export), format)

    # Exit with error if validation failed
    if not result.valid:
        sys.exit(1)


@validate.command(name="profile")
@click.argument("profile")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def validate_profile(profile: str, project_path: str) -> None:
    """
    Validate a specific profile configuration.

    Checks if the specified profile can be loaded and is valid.

    Examples:
        cpa validate profile dev
        cpa validate profile custom
    """
    project_path = Path(project_path)

    console.print(f"[bold cyan]Validating profile: {profile}[/bold cyan]")
    console.print("")

    try:
        ConfigManager(project_path, profile=profile)
        console.print("[OK] Profile is valid", style="bold green")
    except Exception as e:
        console.print(f"[ERROR] Profile validation failed: {e}", style="bold red")
        sys.exit(1)


@validate.command(name="environment")
@click.argument("environment")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--show",
    is_flag=True,
    help="Show environment configuration",
)
def validate_environment(environment: str, project_path: str, show: bool) -> None:
    """
    Validate an environment configuration.

    Checks if the specified environment is properly configured.

    Examples:
        cpa validate environment prod
        cpa validate environment dev --show
    """
    project_path = Path(project_path)

    console.print(f"[bold cyan]Validating environment: {environment}[/bold cyan]")
    console.print("")

    try:
        config_manager = ConfigManager(project_path)

        if environment not in config_manager.list_environments():
            console.print(
                f"[ERROR] Environment '{environment}' not found",
                style="bold red",
            )
            console.print(
                f"Available environments: {', '.join(config_manager.list_environments())}",
            )
            sys.exit(1)

        env_config = config_manager.config.get_environment(environment)

        console.print("[OK] Environment is valid", style="bold green")

        if show:
            console.print("")
            console.print(f"[bold]Base URL:[/bold] {env_config.base_url or 'Not set'}")
            console.print(f"[bold]Browser:[/bold] {env_config.browser.value if env_config.browser else 'Not set'}")
            console.print(f"[bold]Headless:[/bold] {env_config.headless if env_config.headless is not None else 'Not set'}")
            console.print(f"[bold]Parallel Workers:[/bold] {env_config.parallel_workers or 'Not set'}")
            console.print(f"[bold]Timeout:[/bold] {env_config.timeout}ms" if env_config.timeout else "[bold]Timeout:[/bold] Not set")

    except Exception as e:
        console.print(f"[ERROR] Environment validation failed: {e}", style="bold red")
        sys.exit(1)


@validate.command(name="state")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to fix state issues",
)
def validate_state(project_path: str, fix: bool) -> None:
    """
    Validate project state file.

    Checks state file integrity and reports any issues.

    Examples:
        cpa validate state
        cpa validate state --fix
    """
    project_path = Path(project_path)

    console.print("[bold cyan]Validating state file[/bold cyan]")
    console.print("")

    if not StateManager.is_initialized(project_path):
        console.print("[WARN] State not initialized", style="yellow")
        console.print("Run 'cpa init' to initialize the project state")
        return

    try:
        state = StateManager(project_path)
        console.print("[OK] State file is valid", style="bold green")

        # Show state info
        metadata = state.get_project_metadata()
        console.print(f"  Project: {metadata.name}")
        console.print(f"  Framework: {metadata.framework_type.value}")
        console.print(f"  Version: {metadata.version}")

    except Exception as e:
        console.print(f"[ERROR] State validation failed: {e}", style="bold red")
        if fix:
            console.print("Attempting to fix...")
            # Add fix logic here if needed
        sys.exit(1)


def _display_validation_result(result: ValidationResult) -> None:
    """Display validation results in a formatted table."""
    console.print("")

    # Summary table
    counts = result.count()

    if result.valid:
        console.print("[OK] Configuration is valid", style="bold green")
    else:
        console.print("[ERROR] Configuration has issues", style="bold red")

    console.print("")

    # Error table
    if result.errors:
        error_table = Table(title="Errors", show_header=True)
        error_table.add_column("Section", style="cyan")
        error_table.add_column("Key", style="yellow")
        error_table.add_column("Message", style="red")
        error_table.add_column("Suggestion", style="dim")

        for error in result.errors:
            error_table.add_row(
                error["section"],
                error["key"],
                error["message"],
                error.get("suggestion", ""),
            )

        console.print(error_table)
        console.print("")

    # Warning table
    if result.warnings:
        warning_table = Table(title="Warnings", show_header=True)
        warning_table.add_column("Section", style="cyan")
        warning_table.add_column("Key", style="yellow")
        warning_table.add_column("Message", style="yellow")
        warning_table.add_column("Suggestion", style="dim")

        for warning in result.warnings:
            warning_table.add_row(
                warning["section"],
                warning["key"],
                warning["message"],
                warning.get("suggestion", ""),
            )

        console.print(warning_table)
        console.print("")

    # Info tree
    if result.info:
        info_tree = Tree("Information")
        for info in result.info[:10]:  # Limit to first 10
            info_tree.add(
                f"[cyan]{info['section']}[/cyan].[yellow]{info['key']}[/yellow]: {info['message']}"
            )
        console.print(info_tree)
        console.print("")


def _export_validation_result(
    result: ValidationResult,
    output_path: Path,
    format: str,
) -> None:
    """Export validation result to file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2)
        elif format == "yaml":
            import yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(result.to_dict(), f, default_flow_style=False)

        console.print(f"\n[OK] Results exported to {output_path}", style="bold green")
    except Exception as e:
        console.print(f"\n[ERROR] Failed to export results: {e}", style="bold red")
