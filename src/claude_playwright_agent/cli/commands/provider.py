"""
Provider Management Commands for Claude Playwright Agent.

This module provides provider management commands:
- List all available LLM providers
- Test provider connectivity
- Set active provider
- Configure fallback provider chain
- Show provider details
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from claude_playwright_agent.config import ConfigManager

console = Console()


# =============================================================================
# Provider Commands
# =============================================================================


@click.group()
def provider() -> None:
    """LLM provider management commands."""
    pass


@provider.command(name="list")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed provider information",
)
def provider_list(project_path: str, output_json: bool, verbose: bool) -> None:
    """
    List all available LLM providers.

    Shows registered providers with their:
    - Provider type (anthropic, openai, glm)
    - Default models
    - Capabilities (tool-calling, streaming, etc.)
    - Configuration status (API key set or not)

    Examples:
        cpa provider list
        cpa provider list --verbose
        cpa provider list --json
    """
    from claude_playwright_agent.llm import LLMProviderType, ProviderRegistry
    from claude_playwright_agent.llm.models.config import MODEL_ALIASES

    project_path = Path(project_path)
    config_manager = ConfigManager(project_path)
    current_provider = config_manager.ai.provider

    # Get all registered providers
    registered_providers = ProviderRegistry.list_providers()

    if output_json:
        data = {
            "current_provider": current_provider,
            "fallback_providers": config_manager.ai.fallback_providers,
            "available_providers": [],
        }

        for provider_type in registered_providers:
            provider_class = ProviderRegistry.get(provider_type)
            # Create a dummy config to get provider info
            from claude_playwright_agent.llm.models.config import ProviderConfig

            if provider_type == LLMProviderType.ANTHROPIC:
                from claude_playwright_agent.llm.models.config import AnthropicConfig
                dummy_config = AnthropicConfig(api_key="", model="claude-3-5-sonnet-20241022")
            elif provider_type == LLMProviderType.OPENAI:
                from claude_playwright_agent.llm.models.config import OpenAIConfig
                dummy_config = OpenAIConfig(api_key="", model="gpt-4-turbo-preview")
            elif provider_type == LLMProviderType.GLM:
                from claude_playwright_agent.llm.models.config import GLMConfig
                dummy_config = GLMConfig(api_key="", model="glm-4-plus")
            else:
                continue

            provider_instance = provider_class(dummy_config)
            info = provider_instance.get_provider_info()

            # Check if API key is configured
            api_key_env = _get_api_key_env(provider_type.value)
            api_key_set = bool(os.environ.get(api_key_env, ""))

            data["available_providers"].append({
                "type": provider_type.value,
                "name": info.get("name", provider_type.value),
                "models": info.get("models", []),
                "capabilities": info.get("capabilities", []),
                "api_key_env": api_key_env,
                "api_key_configured": api_key_set,
            })

        import json
        console.print_json(json.dumps(data, indent=2))
        return

    # Create table for output
    if verbose:
        table = Table(title="Available LLM Providers", show_header=True)
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("API Key", style="white")
        table.add_column("Models", style="green")
        table.add_column("Capabilities", style="blue")
    else:
        table = Table(title="Available LLM Providers", show_header=True)
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Models", style="green")

    for provider_type in registered_providers:
        # Get provider info
        provider_class = ProviderRegistry.get(provider_type)

        # Create provider instance to get info
        from claude_playwright_agent.llm.models.config import ProviderConfig

        if provider_type == LLMProviderType.ANTHROPIC:
            from claude_playwright_agent.llm.models.config import AnthropicConfig
            dummy_config = AnthropicConfig(api_key="", model="claude-3-5-sonnet-20241022")
        elif provider_type == LLMProviderType.OPENAI:
            from claude_playwright_agent.llm.models.config import OpenAIConfig
            dummy_config = OpenAIConfig(api_key="", model="gpt-4-turbo-preview")
        elif provider_type == LLMProviderType.GLM:
            from claude_playwright_agent.llm.models.config import GLMConfig
            dummy_config = GLMConfig(api_key="", model="glm-4-plus")
        else:
            continue

        provider_instance = provider_class(dummy_config)
        info = provider_instance.get_provider_info()

        # Check if API key is configured
        api_key_env = _get_api_key_env(provider_type.value)
        api_key_set = bool(os.environ.get(api_key_env, ""))
        api_key_status = "[green]SET[/green]" if api_key_set else "[red]NOT SET[/red]"
        is_current = "[bold]*[/bold] " if provider_type.value == current_provider else ""

        # Format models
        models = info.get("models", [])
        if verbose:
            models_str = "\n".join(models)
        else:
            models_str = ", ".join(models[:3])
            if len(models) > 3:
                models_str += f" (+{len(models) - 3} more)"

        if verbose:
            capabilities = ", ".join(info.get("capabilities", []))
            table.add_row(
                f"{is_current}{info.get('name', provider_type.value)}",
                api_key_status,
                api_key_env,
                models_str,
                capabilities,
            )
        else:
            table.add_row(
                f"{is_current}{info.get('name', provider_type.value)}",
                api_key_status,
                models_str,
            )

    console.print(table)

    # Show current configuration
    console.print(f"\n[bold]Current Provider:[/bold] {current_provider}")
    fallback_providers = config_manager.ai.fallback_providers
    if fallback_providers:
        console.print(f"[bold]Fallback Chain:[/bold] {' -> '.join(fallback_providers)}")


@provider.command(name="test")
@click.argument("provider_name", type=click.Choice(["anthropic", "openai", "glm"]))
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--model", "-m",
    help="Specific model to test (uses default if not specified)",
)
def provider_test(provider_name: str, project_path: str, model: str | None) -> None:
    """
    Test connectivity to an LLM provider.

    Sends a simple test query to verify that:
    - API key is correctly configured
    - Provider is accessible
    - Authentication is working

    Examples:
        cpa provider test anthropic
        cpa provider test openai --model gpt-4-turbo-preview
        cpa provider test glm
    """
    from claude_playwright_agent.llm import LLMProviderFactory, LLMProviderType, LLMMessage
    from claude_playwright_agent.llm.models.config import ProviderConfig

    project_path = Path(project_path)

    # Determine which model to use
    if not model:
        config_manager = ConfigManager(project_path)
        provider_settings = config_manager.ai.provider_settings.get(provider_name, {})
        model = provider_settings.get("model", config_manager.ai.model)

    console.print(f"[info]Testing {provider_name} provider...[/info]")

    # Get API key from environment
    api_key_env = _get_api_key_env(provider_name)
    api_key = os.environ.get(api_key_env, "")

    if not api_key:
        console.print(f"[error]API key not found: {api_key_env}[/error]")
        console.print(f"[dim]Set it with: export {api_key_env}=your_key_here[/dim]")
        sys.exit(1)

    # Create provider config
    provider_config = ProviderConfig(
        provider=provider_name,
        model=model,
        api_key=api_key,
        max_tokens=100,
        temperature=0.7,
        timeout=30,
    )

    # Create provider instance
    try:
        llm_provider = LLMProviderFactory.create_provider(provider_config)
    except Exception as e:
        console.print(f"[error]Failed to create provider: {e}[/error]")
        sys.exit(1)

    # Test the provider
    async def run_test():
        try:
            await llm_provider.initialize()

            # Send a simple test message
            messages = [
                LLMMessage.system("You are a helpful assistant."),
                LLMMessage.user("Say 'Test successful' in exactly those words."),
            ]

            console.print("[dim]Sending test query...[/dim]")
            response = await llm_provider.query(messages)

            await llm_provider.cleanup()

            console.print(f"[success]Test successful![/success]")
            console.print(f"[dim]Provider: {provider_name}[/dim]")
            console.print(f"[dim]Model: {response.model or model}[/dim]")
            console.print(f"[dim]Response: {response.content[:100]}...[/dim]")

            # Show token usage if available
            if response.usage:
                console.print(f"[dim]Tokens used: {response.usage.get('prompt_tokens', 0)} + {response.usage.get('completion_tokens', 0)}[/dim]")

        except Exception as e:
            console.print(f"[error]Provider test failed: {e}[/error]")
            sys.exit(1)

    asyncio.run(run_test())


@provider.command(name="set")
@click.argument("provider_name", type=click.Choice(["anthropic", "openai", "glm"]))
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--model", "-m",
    help="Model to use for this provider",
)
@click.option(
    "--fallback", "-f",
    multiple=True,
    help="Fallback providers (can be specified multiple times)",
)
def provider_set(
    provider_name: str,
    project_path: str,
    model: str | None,
    fallback: tuple,
) -> None:
    """
    Set the active LLM provider.

    Updates the project configuration to use the specified provider.
    Optionally set the model and configure fallback providers.

    Examples:
        cpa provider set openai
        cpa provider set glm --model glm-4-plus
        cpa provider set anthropic --fallback openai --fallback glm
    """
    from claude_playwright_agent.llm import LLMProviderType

    project_path = Path(project_path)

    try:
        config_manager = ConfigManager(project_path)
    except Exception as e:
        console.print(f"[error]Failed to load configuration: {e}[/error]")
        sys.exit(1)

    # Validate provider
    valid_providers = ["anthropic", "openai", "glm"]
    if provider_name not in valid_providers:
        console.print(f"[error]Invalid provider: {provider_name}[/error]")
        console.print(f"Valid providers: {', '.join(valid_providers)}")
        sys.exit(1)

    # Update configuration
    updates: dict[str, Any] = {"ai_provider": provider_name}

    if model:
        # Set provider-specific model
        provider_settings = config_manager.ai.provider_settings or {}
        provider_settings[provider_name] = provider_settings.get(provider_name, {})
        provider_settings[provider_name]["model"] = model
        updates["ai_provider_settings"] = provider_settings

    if fallback:
        # Validate fallback providers
        for fb in fallback:
            if fb not in valid_providers:
                console.print(f"[error]Invalid fallback provider: {fb}[/error]")
                sys.exit(1)
        updates["ai_fallback_providers"] = list(fallback)

    try:
        config_manager.update(**updates)
        config_manager.save()
    except Exception as e:
        console.print(f"[error]Failed to update configuration: {e}[/error]")
        sys.exit(1)

    console.print(f"[success]Provider set to: {provider_name}[/success]")
    if model:
        console.print(f"[dim]Model: {model}[/dim]")
    if fallback:
        console.print(f"[dim]Fallback chain: {' -> '.join(fallback)}[/dim]")


@provider.command(name="show")
@click.argument("provider_name", type=click.Choice(["anthropic", "openai", "glm"]), required=False)
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def provider_show(provider_name: str | None, project_path: str) -> None:
    """
    Show provider configuration details.

    Displays detailed configuration for a specific provider or all providers.

    Examples:
        cpa provider show
        cpa provider show anthropic
        cpa provider show openai
    """
    from claude_playwright_agent.llm import LLMProviderType, ProviderRegistry
    from claude_playwright_agent.llm.models.config import MODEL_ALIASES

    project_path = Path(project_path)

    try:
        config_manager = ConfigManager(project_path)
    except Exception as e:
        console.print(f"[error]Failed to load configuration: {e}[/error]")
        sys.exit(1)

    # Determine which providers to show
    if provider_name:
        providers_to_show = [provider_name]
    else:
        providers_to_show = ["anthropic", "openai", "glm"]

    for provider in providers_to_show:
        # Get provider-specific config
        provider_config = config_manager.ai.get_provider_config(provider)

        # Build display data
        display_data = {
            "provider": provider,
            "is_current": provider == config_manager.ai.provider,
            "is_fallback": provider in config_manager.ai.fallback_providers,
            "configured_model": provider_config.get("model"),
            "max_tokens": provider_config.get("max_tokens"),
            "temperature": provider_config.get("temperature"),
        }

        # Add provider-specific info
        from claude_playwright_agent.llm import LLMProviderType

        if provider == "anthropic":
            display_data["api_key_env"] = "ANTHROPIC_API_KEY"
            display_data["enable_caching"] = provider_config.get("enable_caching", True)
            display_data["version"] = "2023-06-01"
        elif provider == "openai":
            display_data["api_key_env"] = "OPENAI_API_KEY"
            display_data["organization"] = provider_config.get("organization")
            display_data["base_url"] = provider_config.get("base_url")
        elif provider == "glm":
            display_data["api_key_env"] = "ZHIPUAI_API_KEY"

        # Display as panel
        title = f"Provider: {provider}"
        if display_data["is_current"]:
            title += " [bold green]*[CURRENT][/bold green]"
        if display_data["is_fallback"]:
            title += " [bold yellow][FALLBACK][/bold yellow]"

        # Format as YAML-like output
        lines = []
        for key, value in display_data.items():
            if key == "is_current" or key == "is_fallback":
                continue
            if value is None:
                lines.append(f"{key}: null")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            else:
                lines.append(f"{key}: {value}")

        yaml_str = "\n".join(lines)
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title=title, expand=False))


# =============================================================================
# Utility Functions
# =============================================================================


def _get_api_key_env(provider_name: str) -> str:
    """Get the API key environment variable name for a provider."""
    env_mapping = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "glm": "ZHIPUAI_API_KEY",
    }
    return env_mapping.get(provider_name, f"{provider_name.upper()}_API_KEY")


__all__ = ["provider"]
