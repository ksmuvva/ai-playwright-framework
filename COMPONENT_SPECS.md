# Component Specifications - Detailed Design

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 1.0 |
| **Date** | 2025-01-11 |
| **Status** | Design |

---

## Table of Contents

1. [CLI Components](#1-cli-components)
2. [Agent Components](#2-agent-components)
3. [MCP Tool Components](#3-mcp-tool-components)
4. [Data Models](#4-data-models)
5. [Interfaces](#5-interfaces)
6. [State Management](#6-state-management)

---

## 1. CLI Components

### 1.1 Main CLI Entry Point

**File:** `src/claude_playwright_agent/cli/main.py`

```python
"""
Main CLI entry point for Claude Playwright Agent.
"""

import click
from pathlib import Path
from typing import Optional

from claude_playwright_agent.config import settings
from claude_playwright_agent.cli.commands import (
    init_command,
    ingest_command,
    run_command,
    report_command,
    skills_command,
    config_command,
)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config: Optional[Path]):
    """
    Claude Playwright Agent - AI-powered test automation framework.

    Create, manage, and execute BDD test automation with AI assistance.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_path'] = config


# Register commands
cli.add_command(init_command.init)
cli.add_command(ingest_command.ingest)
cli.add_command(run_command.run)
cli.add_command(report_command.report)
cli.add_command(skills_command.skills)
cli.add_command(config_command.config)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()
```

---

### 1.2 Init Command

**File:** `src/claude_playwright_agent/cli/commands/init.py`

```python
"""
Init command - Create new test automation framework.
"""

import click
from pathlib import Path
from typing import Optional

from claude_playwright_agent.agents.framework_agent import FrameworkAgent


@click.command()
@click.argument('project_name')
@click.option('--framework', '-f',
              type=click.Choice(['behave', 'pytest-bdd']),
              default='behave',
              help='BDD framework to use')
@click.option('--template', '-t',
              type=click.Choice(['basic', 'advanced', 'ecommerce']),
              default='basic',
              help='Project template')
@click.option('--browser', '-b',
              type=click.Choice(['chromium', 'firefox', 'webkit']),
              default='chromium',
              help='Default browser')
@click.option('--base-url',
              type=str,
              default='',
              help='Base URL for testing')
@click.option('--with-screenshots',
              is_flag=True,
              help='Enable auto-screenshots on failure')
@click.option('--with-videos',
              is_flag=True,
              help='Enable video recording')
@click.option('--with-reports',
              is_flag=True,
              default=True,
              help='Enable HTML reports')
@click.option('--self-healing',
              is_flag=True,
              help='Enable self-healing locators')
@click.pass_context
def init(ctx: click.Context,
         project_name: str,
         framework: str,
         template: str,
         browser: str,
         base_url: str,
         with_screenshots: bool,
         with_videos: bool,
         with_reports: bool,
         self_healing: bool):
    """
    Initialize a new test automation framework.

    Creates a complete project structure with configuration,
    templates, and example files.
    """
    click.echo(f"🚀 Creating framework: {project_name}")

    # Create project path
    project_path = Path.cwd() / project_name

    if project_path.exists():
        click.echo(f"❌ Directory already exists: {project_path}", err=True)
        raise click.Abort()

    # Framework creation options
    options = {
        'project_name': project_name,
        'framework': framework,
        'template': template,
        'browser': browser,
        'base_url': base_url,
        'with_screenshots': with_screenshots,
        'with_videos': with_videos,
        'with_reports': with_reports,
        'self_healing': self_healing,
    }

    # Execute framework creation
    agent = FrameworkAgent()
    result = agent.create_project(options)

    if result['success']:
        click.echo(f"✅ Framework created successfully!")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. cd {project_name}")
        click.echo(f"  2. cpa ingest <recording.js>  # Add your first test")
        click.echo(f"  3. cpa run                     # Run tests")
    else:
        click.echo(f"❌ Failed to create framework: {result.get('error')}", err=True)
        raise click.Abort()
```

---

### 1.3 Ingest Command

**File:** `src/claude_playwright_agent/cli/commands/ingest.py`

```python
"""
Ingest command - Convert Playwright recordings to BDD.
"""

import click
import json
from pathlib import Path
from typing import Optional

from claude_playwright_agent.agents.conversion_agent import ConversionAgent


@click.command()
@click.argument('recording_path', type=click.Path(exists=True))
@click.option('--feature-name', '-f',
              type=str,
              help='Name for the feature file')
@click.option('--scenario-name', '-s',
              type=str,
              help='Name for the scenario')
@click.option('--tags', '-t',
              type=str,
              help='Comma-separated tags (e.g., @smoke,@regression)')
@click.option('--with-pages',
              is_flag=True,
              help='Generate page objects')
@click.option('--self-healing',
              is_flag=True,
              help='Enable self-healing locators')
@click.option('--output', '-o',
              type=click.Path(),
              default='features',
              help='Output directory')
@click.pass_context
def ingest(ctx: click.Context,
           recording_path: str,
           feature_name: Optional[str],
           scenario_name: Optional[str],
           tags: Optional[str],
           with_pages: bool,
           self_healing: bool,
           output: str):
    """
    Ingest a Playwright recording and convert to BDD scenarios.

    RECORDING_PATH: Path to Playwright codegen output (.js file)
    """
    recording_file = Path(recording_path)

    if not recording_file.suffix == '.js':
        click.echo("❌ Recording must be a .js file from Playwright codegen", err=True)
        raise click.Abort()

    click.echo(f"📥 Ingesting recording: {recording_file.name}")

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]

    # Ingestion options
    options = {
        'recording_path': str(recording_file.absolute()),
        'feature_name': feature_name,
        'scenario_name': scenario_name,
        'tags': tag_list,
        'with_pages': with_pages,
        'self_healing': self_healing,
        'output_dir': output,
    }

    # Execute ingestion
    agent = ConversionAgent()
    result = agent.ingest_recording(options)

    if result['success']:
        click.echo(f"✅ Successfully ingested recording!")
        click.echo(f"\nCreated files:")
        for file_path in result.get('files', []):
            click.echo(f"  • {file_path}")

        if result.get('scenarios'):
            click.echo(f"\nGenerated {len(result['scenarios'])} scenario(s)")
    else:
        click.echo(f"❌ Failed to ingest: {result.get('error')}", err=True)
        raise click.Abort()
```

---

### 1.4 Run Command

**File:** `src/claude_playwright_agent/cli/commands/run.py`

```python
"""
Run command - Execute BDD tests.
"""

import click
from pathlib import Path
from typing import Optional, Tuple

from claude_playwright_agent.agents.execution_agent import ExecutionAgent


@click.command()
@click.option('--tags', '-t',
              type=str,
              help='Run scenarios by tags (e.g., @smoke,@regression)')
@click.option('--feature', '-f',
              type=click.Path(exists=True),
              help='Run specific feature file')
@click.option('--scenario', '-s',
              type=str,
              help='Run specific scenario by name')
@click.option('--browser', '-b',
              type=click.Choice(['chromium', 'firefox', 'webkit']),
              help='Browser to use')
@click.option('--headless/--headed',
              default=True,
              help='Run in headless mode')
@click.option('--parallel', '-p',
              type=int,
              help='Number of parallel workers')
@click.option('--self-heal',
              is_flag=True,
              help='Enable self-healing during execution')
@click.option('--ai-report',
              is_flag=True,
              help='Generate AI report after run')
@click.option('--output', '-o',
              type=click.Path(),
              default='reports',
              help='Output directory for results')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Show detailed output')
@click.pass_context
def run(ctx: click.Context,
        tags: Optional[str],
        feature: Optional[str],
        scenario: Optional[str],
        browser: Optional[str],
        headless: bool,
        parallel: Optional[int],
        self_heal: bool,
        ai_report: bool,
        output: str,
        verbose: bool):
    """
    Execute BDD test scenarios.
    """
    click.echo("🧪 Running tests...")

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]

    # Execution options
    options = {
        'tags': tag_list,
        'feature': feature,
        'scenario': scenario,
        'browser': browser,
        'headless': headless,
        'parallel': parallel,
        'self_heal': self_heal,
        'ai_report': ai_report,
        'output_dir': output,
        'verbose': verbose,
    }

    # Execute tests
    agent = ExecutionAgent()
    result = agent.execute(options)

    # Display results
    click.echo(f"\n{'='*60}")
    click.echo(f"📊 Test Results")
    click.echo(f"{'='*60}")
    click.echo(f"  Total:    {result['total']}")
    click.echo(f"  Passed:   {result['passed']} ✅")
    click.echo(f"  Failed:   {result['failed']} ❌")
    click.echo(f"  Skipped:  {result['skipped']} ⏭️")
    click.echo(f"  Duration: {result['duration']}s")

    if result['failed'] > 0:
        click.echo(f"\n❌ {result['failed']} test(s) failed")
        if result.get('failures'):
            for failure in result['failures'][:3]:  # Show first 3
                click.echo(f"  • {failure['scenario']}: {failure['error']}")
    else:
        click.echo(f"\n✅ All tests passed!")

    if ai_report and result.get('report_path'):
        click.echo(f"\n📄 AI Report: {result['report_path']}")
```

---

### 1.5 Report Command

**File:** `src/claude_playwright_agent/cli/commands/report.py`

```python
"""
Report command - Generate AI-analyzed test reports.
"""

import click
from pathlib import Path
from typing import Optional

from claude_playwright_agent.agents.analysis_agent import AnalysisAgent


@click.command()
@click.option('--source', '-s',
              type=click.Path(exists=True),
              default='reports/results.json',
              help='Path to test results JSON')
@click.option('--output', '-o',
              type=click.Path(),
              default='reports',
              help='Output directory')
@click.option('--format', '-f',
              type=click.Choice(['html', 'json', 'markdown']),
              default='html',
              help='Report format')
@click.option('--include-screenshots',
              is_flag=True,
              help='Include failure screenshots')
@click.option('--compare',
              type=click.Path(exists=True),
              help='Compare with previous run')
@click.option('--executive',
              is_flag=True,
              help='Generate executive summary')
@click.pass_context
def report(ctx: click.Context,
           source: str,
           output: str,
           format: str,
           include_screenshots: bool,
           compare: Optional[str],
           executive: bool):
    """
    Generate AI-analyzed test reports.

    Analyzes test results, clusters failures, and provides actionable insights.
    """
    click.echo(f"📊 Generating report...")

    # Report options
    options = {
        'source': source,
        'output_dir': output,
        'format': format,
        'include_screenshots': include_screenshots,
        'compare_with': compare,
        'executive_summary': executive,
    }

    # Generate report
    agent = AnalysisAgent()
    result = agent.generate_report(options)

    if result['success']:
        click.echo(f"✅ Report generated: {result['report_path']}")

        # Show summary
        if result.get('summary'):
            click.echo(f"\n📈 Summary:")
            click.echo(f"  Failure clusters: {result['summary']['clusters']}")
            click.echo(f"  Flaky tests: {result['summary']['flaky']}")
            click.echo(f"  Top issue: {result['summary']['top_issue']}")

        if executive and result.get('executive_path'):
            click.echo(f"\n📄 Executive summary: {result['executive_path']}")
    else:
        click.echo(f"❌ Failed to generate report: {result.get('error')}", err=True)
        raise click.Abort()
```

---

### 1.6 Skills Command

**File:** `src/claude_playwright_agent/cli/commands/skills.py`

```python
"""
Skills command - Manage Claude Skills.
"""

import click
from pathlib import Path
import json

from claude_playwright_agent.skills.manager import SkillManager


@click.group()
def skills():
    """Manage Claude Skills for extending agent capabilities."""
    pass


@skills.command('list')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def list_skills(verbose: bool):
    """List all available skills."""
    manager = SkillManager()
    skills_list = manager.list_skills()

    click.echo(f"📚 Available Skills ({len(skills_list)})\n")

    for skill in skills_list:
        # Type indicator
        type_icon = "🔧" if skill['built_in'] else "📝"

        click.echo(f"{type_icon} {skill['name']}")
        click.echo(f"   {skill['description']}")

        if verbose:
            click.echo(f"   Version: {skill['version']}")
            click.echo(f"   Category: {skill['category']}")
            if skill['triggers']:
                click.echo(f"   Triggers: {', '.join(skill['triggers'])}")
        click.echo()


@skills.command('create')
@click.argument('skill_name')
@click.option('--category', '-c',
              type=click.Choice(['reliability', 'execution', 'analysis', 'custom']),
              default='custom',
              help='Skill category')
@click.option('--trigger',
              type=str,
              help='Event trigger (e.g., TestFailure, BeforeTest)')
@click.option('--description', '-d',
              type=str,
              help='Skill description')
@click.option('--template',
              type=click.Choice(['basic', 'advanced', 'multi-step']),
              default='basic',
              help='Skill template')
def create_skill(skill_name: str, category: str, trigger: Optional[str],
                description: Optional[str], template: str):
    """Create a new custom skill."""
    manager = SkillManager()

    skill_options = {
        'name': skill_name,
        'category': category,
        'trigger': trigger,
        'description': description or f'{skill_name} skill',
        'template': template,
    }

    result = manager.create_skill(skill_options)

    if result['success']:
        click.echo(f"✅ Skill created: {result['skill_path']}")
        click.echo(f"\nEdit the skill file to add your custom logic.")
    else:
        click.echo(f"❌ Failed to create skill: {result.get('error')}", err=True)
        raise click.Abort()


@skills.command('run')
@click.argument('skill_name')
@click.option('--context', '-c',
              type=click.Path(exists=True),
              help='Context JSON file')
@click.option('--dry-run',
              is_flag=True,
              help='Show what would be done without executing')
def run_skill(skill_name: str, context: Optional[str], dry_run: bool):
    """Manually invoke a skill."""
    manager = SkillManager()

    # Load context
    context_data = {}
    if context:
        with open(context, 'r') as f:
            context_data = json.load(f)

    result = manager.invoke_skill(skill_name, context_data, dry_run=dry_run)

    if result['success']:
        if dry_run:
            click.echo(f"🔍 Dry run for skill: {skill_name}")
            click.echo(f"\nWould execute:")
            for action in result['actions']:
                click.echo(f"  • {action}")
        else:
            click.echo(f"✅ Skill executed: {skill_name}")
            if result.get('output'):
                click.echo(f"\nOutput:\n{result['output']}")
    else:
        click.echo(f"❌ Failed to execute skill: {result.get('error')}", err=True)
        raise click.Abort()


@skills.command('update')
@click.argument('skill_name')
@click.option('--enable/--disable',
              default=None,
              help='Enable or disable the skill')
def update_skill(skill_name: str, enable: Optional[bool]):
    """Update a skill's configuration."""
    manager = SkillManager()

    result = manager.update_skill(skill_name, enabled=enable)

    if result['success']:
        status = "enabled" if enable else "disabled"
        click.echo(f"✅ Skill {status}: {skill_name}")
    else:
        click.echo(f"❌ Failed to update skill: {result.get('error')}", err=True)
        raise click.Abort()


@skills.command('delete')
@click.argument('skill_name')
@click.confirmation_option(prompt='Are you sure you want to delete this skill?')
def delete_skill(skill_name: str):
    """Delete a custom skill."""
    manager = SkillManager()

    result = manager.delete_skill(skill_name)

    if result['success']:
        click.echo(f"✅ Skill deleted: {skill_name}")
    else:
        click.echo(f"❌ Failed to delete skill: {result.get('error')}", err=True)
        raise click.Abort()


@skills.command('validate')
@click.argument('skill_path', type=click.Path(exists=True))
def validate_skill(skill_path: str):
    """Validate a skill configuration file."""
    manager = SkillManager()

    result = manager.validate_skill(skill_path)

    if result['valid']:
        click.echo(f"✅ Skill is valid!")
        click.echo(f"\nSkill: {result['name']}")
        click.echo(f"Version: {result['version']}")
        click.echo(f"Triggers: {', '.join(result['triggers'])}")
    else:
        click.echo(f"❌ Skill validation failed:", err=True)
        for error in result['errors']:
            click.echo(f"  • {error}", err=True)
        raise click.Abort()
```

---

### 1.7 Config Command

**File:** `src/claude_playwright_agent/cli/commands/config.py`

```python
"""
Config command - Manage framework configuration.
"""

import click
import yaml
from pathlib import Path

from claude_playwright_agent.config import settings


@click.group()
def config():
    """Manage framework configuration."""
    pass


@config.command('get')
@click.argument('key')
@click.option('--project', '-p',
              type=click.Path(exists=True),
              help='Project config (default: global)')
def config_get(key: str, project: Optional[str]):
    """Get a configuration value."""
    config_path = _get_config_path(project)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Navigate nested keys (dot notation)
    value = config
    for part in key.split('.'):
        value = value.get(part, {})
        if value == {}:
            click.echo(f"❌ Key not found: {key}", err=True)
            raise click.Abort()

    if isinstance(value, dict):
        click.echo(yaml.dump(value, default_flow_style=False))
    else:
        click.echo(value)


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.option('--project', '-p',
              type=click.Path(exists=True),
              help='Project config (default: global)')
def config_set(key: str, value: str, project: Optional[str]):
    """Set a configuration value."""
    config_path = _get_config_path(project)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Navigate and set nested keys
    target = config
    parts = key.split('.')

    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]

    # Convert value to appropriate type
    target[parts[-1]] = _convert_value(value)

    # Write back
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    click.echo(f"✅ Set {key} = {value}")


@config.command('list')
@click.option('--project', '-p',
              type=click.Path(exists=True),
              help='Project config (default: global)')
def config_list(project: Optional[str]):
    """List all configuration values."""
    config_path = _get_config_path(project)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    click.echo(yaml.dump(config, default_flow_style=False))


@config.command('edit')
@click.option('--project', '-p',
              type=click.Path(exists=True),
              help='Project config (default: global)')
def config_edit(project: Optional[str]):
    """Open config in editor."""
    config_path = _get_config_path(project)

    editor = click.edit(filename=config_path)

    if editor:
        click.echo(f"✅ Config updated")
    else:
        click.echo(f"❌ No changes made")


def _get_config_path(project: Optional[str]) -> Path:
    """Get config file path."""
    if project:
        return Path(project) / '.cpa' / 'config.yaml'
    else:
        return Path.home() / '.cpa' / 'config.yaml'


def _convert_value(value: str):
    """Convert string value to appropriate type."""
    # Try boolean
    if value.lower() in ('true', 'yes', 'on'):
        return True
    if value.lower() in ('false', 'no', 'off'):
        return False

    # Try number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Return as string
    return value
```

---

## 2. Agent Components

### 2.1 FrameworkAgent

**File:** `src/claude_playwright_agent/agents/framework_agent.py`

```python
"""
FrameworkAgent - Creates and configures test automation frameworks.
"""

from pathlib import Path
from typing import Any, Dict, List
import shutil

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.tools.framework_tools import (
    create_directory_structure,
    generate_config_files,
    create_templates,
)


class FrameworkAgent(BaseAgent):
    """
    Agent responsible for creating and configuring test automation frameworks.
    """

    def __init__(self):
        system_prompt = """You are a test automation framework architect.

Your responsibilities:
1. Create well-structured project layouts
2. Generate appropriate configuration files
3. Create reusable templates
4. Follow industry best practices

Framework structure principles:
- Clear separation of concerns (features, steps, pages, data)
- Convention over configuration
- Easy to understand and navigate
- Scalable for large projects
- Include helpful documentation"""

        super().__init__(system_prompt=system_prompt)

    def create_project(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new test automation project.

        Args:
            options: Project creation options

        Returns:
            Result with success status and created files
        """
        project_name = options['project_name']
        project_path = Path.cwd() / project_name

        try:
            # Create directory structure
            dirs = create_directory_structure(options)
            for dir_path in dirs:
                full_path = project_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)

            # Generate configuration files
            config_files = generate_config_files(options)
            for file_info in config_files:
                file_path = project_path / file_info['path']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(file_info['content'])

            # Create templates
            templates = create_templates(options)
            for template in templates:
                template_path = project_path / template['path']
                template_path.parent.mkdir(parents=True, exist_ok=True)
                with open(template_path, 'w') as f:
                    f.write(template['content'])

            return {
                'success': True,
                'project_path': str(project_path),
                'files': [f['path'] for f in config_files + templates],
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def add_feature(self, project_path: str, feature_name: str) -> Dict[str, Any]:
        """Add a new feature to an existing project."""
        features_dir = Path(project_path) / 'features'
        feature_file = features_dir / f'{feature_name}.feature'

        if feature_file.exists():
            return {'success': False, 'error': 'Feature already exists'}

        # Create feature template
        template = f"""Feature: {feature_name.title()}
  As a user
  I want to perform an action
  So that I can achieve a goal

  Scenario: Example scenario
    Given I am on the homepage
    When I perform an action
    Then I should see the result
"""

        feature_file.write_text(template)

        return {
            'success': True,
            'feature_file': str(feature_file),
        }

    def configure_project(self, project_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update project configuration."""
        config_file = Path(project_path) / '.cpa' / 'config.yaml'

        import yaml
        with open(config_file, 'r') as f:
            current_config = yaml.safe_load(f) or {}

        # Merge new config
        current_config.update(config)

        with open(config_file, 'w') as f:
            yaml.dump(current_config, f, default_flow_style=False)

        return {'success': True}
```

---

### 2.2 ConversionAgent

**File:** `src/claude_playwright_agent/agents/conversion_agent.py`

```python
"""
ConversionAgent - Converts Playwright recordings to BDD scenarios.
"""

from pathlib import Path
from typing import Any, Dict, List
import re
import ast

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.tools.bdd_tools import (
    parse_playwright_script,
    generate_feature_file,
    generate_step_definitions,
)


class ConversionAgent(BaseAgent):
    """
    Agent responsible for converting Playwright recordings to BDD.
    """

    def __init__(self):
        system_prompt = """You are a BDD expert specializing in test automation.

Your responsibilities:
1. Analyze Playwright recordings and extract user intent
2. Convert technical actions to business language
3. Generate clear, maintainable Gherkin scenarios
4. Create reusable step definitions
5. Suggest appropriate page objects

BDD conversion principles:
- Use business language, not technical details
- Create scenarios that tell a story
- Extract reusable steps
- Make scenarios readable by non-technical stakeholders
- Include appropriate tags for organization"""

        super().__init__(system_prompt=system_prompt)

    def ingest_recording(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a Playwright recording and convert to BDD.

        Args:
            options: Ingestion options

        Returns:
            Result with success status and created files
        """
        recording_path = Path(options['recording_path'])

        try:
            # Parse the Playwright script
            with open(recording_path, 'r') as f:
                script_content = f.read()

            actions = parse_playwright_script(script_content)

            # Extract feature/scenario names
            feature_name = options.get('feature_name') or self._extract_feature_name(actions)
            scenario_name = options.get('scenario_name') or self._extract_scenario_name(actions)

            # Generate feature file
            feature_content = generate_feature_file({
                'feature_name': feature_name,
                'scenario_name': scenario_name,
                'actions': actions,
                'tags': options.get('tags', []),
            })

            feature_path = Path(options['output_dir']) / f'{feature_name}.feature'
            feature_path.parent.mkdir(parents=True, exist_ok=True)
            feature_path.write_text(feature_content)

            # Generate step definitions
            steps_content = generate_step_definitions({
                'feature_file': str(feature_path),
                'framework': 'behave',
                'actions': actions,
            })

            steps_path = Path('steps') / f'{feature_name}_steps.py'
            steps_path.parent.mkdir(parents=True, exist_ok=True)
            steps_path.write_text(steps_content)

            created_files = [str(feature_path), str(steps_path)]

            # Generate page objects if requested
            if options.get('with_pages'):
                page_objects = self._generate_page_objects(actions, feature_name)
                for page_name, page_content in page_objects.items():
                    page_path = Path('pages') / f'{page_name}.py'
                    page_path.parent.mkdir(parents=True, exist_ok=True)
                    page_path.write_text(page_content)
                    created_files.append(str(page_path))

            return {
                'success': True,
                'files': created_files,
                'scenarios': 1,
                'feature_name': feature_name,
                'scenario_name': scenario_name,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def _extract_feature_name(self, actions: List[Dict]) -> str:
        """Extract feature name from actions."""
        # Look for the first navigate action
        for action in actions:
            if action['type'] == 'goto':
                url = action.get('url', '')
                # Extract domain/path
                parts = url.replace('https://', '').replace('http://', '').split('/')
                if parts:
                    return parts[0].replace('.', '_').replace('-', '_')
        return 'feature'

    def _extract_scenario_name(self, actions: List[Dict]) -> str:
        """Extract scenario name from actions."""
        # Analyze actions to determine intent
        if any(a['type'] == 'fill' for a in actions):
            if 'login' in str(actions).lower():
                return 'user_login'
            elif 'search' in str(actions).lower():
                return 'search'
        return 'user_action'

    def _generate_page_objects(self, actions: List[Dict], feature_name: str) -> Dict[str, str]:
        """Generate page object classes."""
        pages = {}
        current_page = 'BasePage'

        page_content = f'''"""
Page objects for {feature_name}
"""

from playwright.sync_api import Page, Locator


class {current_page}:
    """Base page object"""

    def __init__(self, page: Page):
        self.page = page

'''

        # Extract selectors from actions
        for action in actions:
            if 'selector' in action:
                selector = action['selector']
                element_name = self._selector_to_name(selector, action['type'])

                page_content += f'''
    @property
    def {element_name}(self) -> Locator:
        """{action.get('description', selector)}"""
        return self.page.locator("{selector}")
'''

        pages[current_page] = page_content
        return pages

    def _selector_to_name(self, selector: str, action_type: str) -> str:
        """Convert selector to Python property name."""
        # Extract meaningful name from selector
        if '[' in selector:
            # Attribute selector like [data-testid="submit"]
            match = re.search(r'[\w-]+', selector)
            if match:
                return f'{match.group()}_{action_type}'

        # CSS selector
        parts = selector.split('.')
        if len(parts) > 1:
            return parts[-1].replace('[', '').replace(']', '')

        return f'element_{action_type}'
```

---

### 2.3 ExecutionAgent

**File:** `src/claude_playwright_agent/agents/execution_agent.py`

```python
"""
ExecutionAgent - Executes BDD tests with Playwright.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess
import json
import time

from claude_playwright_agent.agents.base import BaseAgent


class ExecutionAgent(BaseAgent):
    """
    Agent responsible for executing BDD tests.
    """

    def __init__(self):
        system_prompt = """You are a test execution coordinator.

Your responsibilities:
1. Execute BDD scenarios reliably
2. Capture detailed results
3. Handle failures gracefully
4. Enable self-healing when requested
5. Generate comprehensive output

Execution principles:
- Clear progress reporting
- Detailed logging
- Proper cleanup
- Accurate timing
- Screenshot on failure"""

        super().__init__(system_prompt=system_prompt)

    def execute(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute BDD tests.

        Args:
            options: Execution options

        Returns:
            Test results summary
        """
        framework = self._detect_framework()
        start_time = time.time()

        try:
            if framework == 'behave':
                results = self._execute_behave(options)
            elif framework == 'pytest-bdd':
                results = self._execute_pytest_bdd(options)
            else:
                return {
                    'success': False,
                    'error': f'Unknown framework: {framework}',
                }

            duration = time.time() - start_time

            # Generate report if requested
            if options.get('ai_report'):
                report_path = self._generate_ai_report(results, options)
                results['report_path'] = report_path

            results['duration'] = round(duration, 2)
            results['success'] = True

            return results

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': round(time.time() - start_time, 2),
            }

    def _detect_framework(self) -> str:
        """Detect which BDD framework is being used."""
        if Path('behave.ini').exists() or (Path('features').exists() and Path('steps').exists()):
            return 'behave'
        elif Path('pytest.ini').exists() or Path('pyproject.toml').exists():
            return 'pytest-bdd'
        return 'behave'  # Default

    def _execute_behave(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tests using Behave."""
        cmd = ['behave']

        # Add options
        if options.get('tags'):
            for tag in options['tags']:
                cmd.extend(['--tags', tag])

        if options.get('feature'):
            cmd.append(options['feature'])

        if options.get('verbose'):
            cmd.append('--verbose')

        # Add output format
        cmd.extend(['--format', 'json', '--outfile', 'reports/results.json'])

        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        # Parse results
        return self._parse_behave_results('reports/results.json')

    def _execute_pytest_bdd(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tests using pytest-bdd."""
        cmd = ['pytest', '-v']

        # Add options
        if options.get('tags'):
            cmd.extend(['-k', ' or '.join(options['tags'])])

        if options.get('feature'):
            cmd.append(options['feature'])

        if options.get('parallel'):
            cmd.extend(['-n', str(options['parallel'])])

        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        # Parse results
        return self._parse_pytest_results()

    def _parse_behave_results(self, results_path: str) -> Dict[str, Any]:
        """Parse Behave JSON results."""
        with open(results_path, 'r') as f:
            data = json.load(f)

        total = 0
        passed = 0
        failed = 0
        skipped = 0
        failures = []

        for feature in data:
            for element in feature.get('elements', []):
                for step in element.get('steps', []):
                    total += 1
                    status = step.get('result', {}).get('status', 'skipped')

                    if status == 'passed':
                        passed += 1
                    elif status == 'failed':
                        failed += 1
                        failures.append({
                            'scenario': element.get('name'),
                            'step': step.get('name'),
                            'error': step.get('result', {}).get('error_message', 'Unknown error'),
                        })
                    elif status == 'skipped':
                        skipped += 1
                    elif status == 'undefined':
                        skipped += 1

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'failures': failures,
        }

    def _parse_pytest_results(self) -> Dict[str, Any]:
        """Parse pytest results from terminal output."""
        # This would parse pytest output
        # For now, return placeholder
        return {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'failures': [],
        }

    def _generate_ai_report(self, results: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Generate AI-analyzed report."""
        from claude_playwright_agent.agents.analysis_agent import AnalysisAgent

        agent = AnalysisAgent()

        report_options = {
            'source': 'reports/results.json',
            'output_dir': options.get('output_dir', 'reports'),
            'format': 'html',
        }

        result = agent.generate_report(report_options)

        return result.get('report_path', '')
```

---

### 2.4 AnalysisAgent

**File:** `src/claude_playwright_agent/agents/analysis_agent.py`

```python
"""
AnalysisAgent - Analyzes test results and generates reports.
"""

from pathlib import Path
from typing import Any, Dict, List
import json
from datetime import datetime

from claude_playwright_agent.agents.base import BaseAgent


class AnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing test results and generating reports.
    """

    def __init__(self):
        system_prompt = """You are a test analysis expert.

Your responsibilities:
1. Analyze test results comprehensively
2. Cluster similar failures
3. Identify root causes
4. Generate actionable insights
5. Create executive summaries

Analysis principles:
- Focus on business impact
- Provide clear next steps
- Highlight patterns and trends
- Quantify risk and coverage
- Be concise and actionable"""

        super().__init__(system_prompt=system_prompt)

    def generate_report(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-analyzed test report.

        Args:
            options: Report generation options

        Returns:
            Report generation result
        """
        source_path = Path(options['source'])

        try:
            # Load results
            with open(source_path, 'r') as f:
                results_data = json.load(f)

            # Analyze results
            analysis = self._analyze_results(results_data)

            # Generate report based on format
            if options['format'] == 'html':
                report_path = self._generate_html_report(analysis, options)
            elif options['format'] == 'json':
                report_path = self._generate_json_report(analysis, options)
            else:
                report_path = self._generate_markdown_report(analysis, options)

            # Generate executive summary if requested
            executive_path = None
            if options.get('executive_summary'):
                executive_path = self._generate_executive_summary(analysis, options)

            return {
                'success': True,
                'report_path': report_path,
                'executive_path': executive_path,
                'summary': {
                    'clusters': analysis.get('cluster_count', 0),
                    'flaky': analysis.get('flaky_count', 0),
                    'top_issue': analysis.get('top_issue', 'None'),
                },
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def _analyze_results(self, results: Dict) -> Dict[str, Any]:
        """Analyze test results."""
        failures = results.get('failures', [])

        # Cluster failures
        clusters = self._cluster_failures(failures)

        # Identify flaky tests
        flaky = self._identify_flaky_tests(results)

        # Find top issue
        top_issue = clusters[0]['name'] if clusters else 'No failures'

        return {
            'total': results.get('total', 0),
            'passed': results.get('passed', 0),
            'failed': results.get('failed', 0),
            'skipped': results.get('skipped', 0),
            'clusters': clusters,
            'flaky': flaky,
            'cluster_count': len(clusters),
            'flaky_count': len(flaky),
            'top_issue': top_issue,
            'timestamp': datetime.now().isoformat(),
        }

    def _cluster_failures(self, failures: List[Dict]) -> List[Dict]:
        """Cluster similar failures."""
        if not failures:
            return []

        # Simple clustering by error type
        clusters = {}

        for failure in failures:
            error = failure.get('error', 'Unknown')
            error_type = error.split(':')[0] if ':' in error else 'Unknown'

            if error_type not in clusters:
                clusters[error_type] = {
                    'name': error_type,
                    'count': 0,
                    'failures': [],
                }

            clusters[error_type]['count'] += 1
            clusters[error_type]['failures'].append(failure)

        # Sort by count
        return sorted(clusters.values(), key=lambda x: x['count'], reverse=True)

    def _identify_flaky_tests(self, results: Dict) -> List[str]:
        """Identify potentially flaky tests."""
        # This would analyze historical data
        # For now, return empty list
        return []

    def _generate_html_report(self, analysis: Dict, options: Dict) -> str:
        """Generate HTML report."""
        output_path = Path(options['output_dir']) / 'html' / 'report.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 8px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .cluster {{ margin: 20px 0; padding: 15px; background: #fafafa; border-left: 4px solid #007acc; }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total: {analysis['total']}</p>
        <p class="passed">Passed: {analysis['passed']}</p>
        <p class="failed">Failed: {analysis['failed']}</p>
        <p>Skipped: {analysis['skipped']}</p>
        <p>Generated: {analysis['timestamp']}</p>
    </div>

    <h2>Failure Clusters</h2>
    {self._render_clusters_html(analysis['clusters'])}
</body>
</html>
"""

        output_path.write_text(html_template)
        return str(output_path)

    def _render_clusters_html(self, clusters: List[Dict]) -> str:
        """Render failure clusters as HTML."""
        if not clusters:
            return '<p>No failures</p>'

        html = ''
        for cluster in clusters:
            html += f'''
    <div class="cluster">
        <h3>{cluster['name']} ({cluster['count']} failures)</h3>
        <ul>
'''
            for failure in cluster['failures'][:5]:  # Show first 5
                html += f'            <li>{failure.get("scenario", "Unknown")}: {failure.get("step", "")}</li>\n'

            html += '        </ul>\n    </div>\n'

        return html

    def _generate_json_report(self, analysis: Dict, options: Dict) -> str:
        """Generate JSON report."""
        output_path = Path(options['output_dir']) / 'json' / 'report.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(json.dumps(analysis, indent=2))
        return str(output_path)

    def _generate_markdown_report(self, analysis: Dict, options: Dict) -> str:
        """Generate Markdown report."""
        output_path = Path(options['output_dir']) / 'report.md'

        markdown = f"""# Test Report

## Summary

| Metric | Count |
|--------|-------|
| Total | {analysis['total']} |
| Passed | {analysis['passed']} ✅ |
| Failed | {analysis['failed']} ❌ |
| Skipped | {analysis['skipped']} |

Generated: {analysis['timestamp']}

## Failure Clusters

"""

        for cluster in analysis['clusters']:
            markdown += f"### {cluster['name']} ({cluster['count']} failures)\n\n"
            for failure in cluster['failures'][:5]:
                markdown += f"- **{failure.get('scenario', 'Unknown')}**: {failure.get('step', '')}\n"
            markdown += "\n"

        output_path.write_text(markdown)
        return str(output_path)

    def _generate_executive_summary(self, analysis: Dict, options: Dict) -> str:
        """Generate executive summary."""
        output_path = Path(options['output_dir']) / 'executive_summary.md'

        summary = f"""# Executive Summary

## Test Execution Overview

- **Total Tests**: {analysis['total']}
- **Pass Rate**: {round(analysis['passed'] / analysis['total'] * 100, 1) if analysis['total'] > 0 else 0}%
- **Failed**: {analysis['failed']}
- **Key Issues**: {analysis['cluster_count']} failure cluster(s)

## Top Issues

1. **{analysis['top_issue']}** - See detailed report for more information

## Recommendations

{'All tests passed!' if analysis['failed'] == 0 else 'Review failed tests and address identified issues.'}

---

*Generated on {analysis['timestamp']}*
"""

        output_path.write_text(summary)
        return str(output_path)
```

---

## 3. MCP Tool Components

### 3.1 Framework Tools

**File:** `src/claude_playwright_agent/tools/framework_tools.py`

```python
"""
Framework generation tools as MCP server.
"""

from pathlib import Path
from typing import Dict, Any

from claude_agent_sdk import tool, create_sdk_mcp_server


@tool("create_directory_structure", "Create project directory structure", {
    "project_name": str,
    "template": str,
})
async def create_directory_structure(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create directory structure for test automation framework."""
    template = args.get('template', 'basic')

    if template == 'basic':
        return {
            "directories": [
                "features",
                "steps",
                "pages",
                "test_data",
                "reports",
                "reports/html",
                "reports/json",
                "reports/screenshots",
                "recordings",
                ".cpa",
                ".cpa/skills",
                ".cpa/state",
            ]
        }
    elif template == 'advanced':
        return {
            "directories": [
                "features",
                "features/smoke",
                "features/regression",
                "features/api",
                "steps",
                "steps/common",
                "pages",
                "test_data",
                "test_data/json",
                "test_data/csv",
                "reports",
                "utils",
                "hooks",
                ".cpa",
                ".cpa/skills",
                ".cpa/state",
            ]
        }
    else:  # ecommerce
        return {
            "directories": [
                "features",
                "features/account",
                "features/checkout",
                "features/product",
                "features/search",
                "steps",
                "pages",
                "pages/account",
                "pages/checkout",
                "pages/product",
                "test_data",
                "reports",
                ".cpa",
            ]
        }


@tool("generate_config_files", "Generate configuration files", {
    "framework": str,
    "browser": str,
    "base_url": str,
})
async def generate_config_files(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate configuration files."""
    framework = args.get('framework', 'behave')
    browser = args.get('browser', 'chromium')
    base_url = args.get('base_url', '')

    files = []

    # conftest.py
    conftest_content = f'''"""
Configuration for {framework} tests.
"""

from playwright.sync_api import BrowserType, BrowserContext, Page
import pytest

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend browser context."""
    return {{
        **browser_context_args,
        "viewport": {{"width": 1920, "height": 1080}},
    }}

@pytest.fixture(scope="session")
def base_url():
    """Base URL for tests."""
    return "{base_url}"

@pytest.fixture(scope="function")
def page(browser_context: BrowserContext, base_url: str):
    """Create a new page."""
    page = browser_context.new_page()
    page.goto(base_url)
    yield page
    page.close()
'''

    files.append({
        'path': 'conftest.py',
        'content': conftest_content,
    })

    # requirements.txt
    requirements_content = f'''#
# Test Framework
#
{framework}-pytest

#
# Browser Automation
#
playwright==1.40.0

#
# Reporting
#
allure-pytest==2.13.2
pytest-html==3.2.0

#
# Utilities
#
python-dotenv==1.0.0
pyyaml==6.0.1
'''

    files.append({
        'path': 'requirements.txt',
        'content': requirements_content,
    })

    # .env.example
    env_content = f'''#
# Environment Configuration
#

# Base URL for testing
BASE_URL={base_url}

# Default browser
DEFAULT_BROWSER={browser}

# API Keys (if needed)
# API_KEY=your_api_key_here
'''

    files.append({
        'path': '.env.example',
        'content': env_content,
    })

    # .cpa/config.yaml
    config_content = f'''#
# Claude Playwright Agent Configuration
#

framework:
  bdd: {framework}
  browser: {browser}
  headless: true
  base_url: {base_url}
  timeout: 30000

execution:
  parallel: 4
  retry: 2
  self_healing: true

recording:
  auto_screenshots: true
  video: false

reporting:
  formats: [html, json]
  include_ai: true

skills:
  enabled: []
  auto_invoke: []
'''

    files.append({
        'path': '.cpa/config.yaml',
        'content': config_content,
    })

    return {"files": files}


@tool("create_templates", "Create template files", {
    "template": str,
    "framework": str,
})
async def create_templates(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create template files."""
    framework = args.get('framework', 'behave')
    template = args.get('template', 'basic')

    templates = []

    # Example feature file
    feature_content = '''Feature: Example Feature
  As a user
  I want to perform an action
  So that I can achieve a goal

  Scenario: Example scenario
    Given I am on the homepage
    When I perform an action
    Then I should see the result
'''

    templates.append({
        'path': 'features/example.feature',
        'content': feature_content,
    })

    # Example step definitions
    if framework == 'behave':
        steps_content = '''"""
Common step definitions.
"""

from playwright.sync_api import Page, expect
from behave import given, when, then


@given('I am on the homepage')
def step_homepage(context):
    """Navigate to homepage."""
    context.page.goto(context.config.userdata.get('base_url', '/'))


@when('I perform an action')
def step_perform_action(context):
    """Perform an action."""
    # Add your action here
    pass


@then('I should see the result')
def step_see_result(context):
    """Verify result."""
    # Add verification here
    pass
'''
    else:  # pytest-bdd
        steps_content = '''"""
Common step definitions.
"""

from playwright.sync_api import Page, expect
from pytest_bdd import given, when, then, scenario


@scenario('features/example.feature', 'Example scenario')
def test_example_scenario():
    """Test example scenario."""
    pass


@given('I am on the homepage')
def step_homepage(page: Page):
    """Navigate to homepage."""
    page.goto('/')


@when('I perform an action')
def step_perform_action(page: Page):
    """Perform an action."""
    # Add your action here
    pass


@then('I should see the result')
def step_see_result(page: Page):
    """Verify result."""
    # Add verification here
    pass
'''

    templates.append({
        'path': f'steps/common_steps.py',
        'content': steps_content,
    })

    # README
    readme_content = f'''# Test Automation Framework

This framework was generated by Claude Playwright Agent.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install --with-deps
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Record your first test:
   ```bash
   npx playwright codegen https://example.com
   ```

4. Ingest the recording:
   ```bash
   cpa ingest recording.js
   ```

5. Run tests:
   ```bash
   cpa run
   ```

## Framework: {framework}

## Template: {template}

## Documentation

For more information, see the [Claude Playwright Agent documentation](https://docs.claudeplaywright.ai).
'''

    templates.append({
        'path': 'README.md',
        'content': readme_content,
    })

    return {"templates": templates}


# Create the MCP server
framework_server = create_sdk_mcp_server(
    name="framework-tools",
    version="1.0.0",
    tools=[
        create_directory_structure,
        generate_config_files,
        create_templates,
    ],
)
```

---

### 3.2 BDD Tools

**File:** `src/claude_playwright_agent/tools/bdd_tools.py`

```python
"""
BDD conversion tools as MCP server.
"""

import re
from typing import Dict, Any, List
from pathlib import Path

from claude_agent_sdk import tool, create_sdk_mcp_server


@tool("parse_playwright_script", "Parse Playwright codegen output", {
    "script_content": str,
})
async def parse_playwright_script(args: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Playwright codegen JavaScript and extract actions."""
    script = args['script_content']

    actions = []

    # Pattern matching for Playwright actions
    patterns = {
        'goto': r'page\.goto\([\'"]([^\'"]+)[\'"]\)',
        'click': r'page\.click\([\'"]([^\'"]+)[\'"]\)',
        'fill': r'page\.fill\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]*)[\'"]\)',
        'type': r'page\.type\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]*)[\'"]\)',
        'select': r'page\.selectOption\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]*)[\'"]\)',
        'check': r'page\.check\([\'"]([^\'"]+)[\'"]\)',
        'uncheck': r'page\.uncheck\([\'"]([^\'"]+)[\'"]\)',
        'press': r'page\.press\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]*)[\'"]\)',
        'wait': r'page\.waitFor\(?[\'"]?([^\'")\]]+)[\'"]?\)?',
        'screenshot': r'page\.screenshot\([^)]*\)',
    }

    lines = script.split('\n')
    for line in lines:
        line = line.strip()

        for action_type, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                action = {
                    'type': action_type,
                    'selector': match.group(1) if match.groups() else '',
                    'line': line,
                }

                # Add value if applicable
                if action_type in ['fill', 'type', 'select', 'press']:
                    action['value'] = match.group(2) if len(match.groups()) > 1 else ''

                actions.append(action)
                break

    return {"actions": actions}


@tool("generate_feature_file", "Generate Gherkin feature file", {
    "feature_name": str,
    "scenario_name": str,
    "actions": list,
    "tags": list,
})
async def generate_feature_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Gherkin feature file from actions."""
    feature_name = args['feature_name']
    scenario_name = args['scenario_name']
    actions = args['actions']
    tags = args.get('tags', [])

    # Build feature content
    feature = f'''Feature: {feature_name.replace('_', ' ').title()}
  As a user
  I want to perform actions on the page
  So that I can achieve my goal

'''

    # Add tags if present
    if tags:
        feature += '  ' + ' '.join(tags) + '\n'

    feature += f'''  Scenario: {scenario_name.replace('_', ' ').title()}
'''

    # Convert actions to Gherkin steps
    for i, action in enumerate(actions):
        step = _action_to_gherkin(action, i == 0, i == len(actions) - 1)
        feature += f'    {step}\n'

    return {"feature_content": feature}


def _action_to_gherkin(action: Dict, is_first: bool, is_last: bool) -> str:
    """Convert Playwright action to Gherkin step."""
    action_type = action['type']
    selector = action.get('selector', '')
    value = action.get('value', '')

    # Extract element description from selector
    element = _describe_element(selector)

    if action_type == 'goto':
        return f'Given I am on the page with URL "{selector}"'

    elif action_type in ['click', 'check']:
        return f'When I click {element}'

    elif action_type == 'uncheck':
        return f'When I uncheck {element}'

    elif action_type in ['fill', 'type']:
        return f'When I enter "{value}" in {element}'

    elif action_type == 'select':
        return f'When I select "{value}" from {element}'

    elif action_type == 'press':
        return f'When I press "{value}"'

    elif is_last and action_type in ['wait', 'screenshot']:
        return f'Then I should see the result'

    else:
        return f'And I wait for the page to load'


def _describe_element(selector: str) -> str:
    """Generate a human-readable description of an element."""
    # Data attribute
    if 'data-testid=' in selector or 'data-test=' in selector:
        match = re.search(r'data-[a-z]+=[\'"]([^\'"]+)[\'"]', selector)
        if match:
            return f'the "{match.group(1)}" element'

    # ID
    if '#' in selector:
        match = re.search(r'#([\w-]+)', selector)
        if match:
            return f'the "{match.group(1)}" element'

    # Class
    if '.' in selector:
        match = re.search(r'\.([\w-]+)', selector)
        if match:
            return f'the element with class "{match.group(1)}"'

    # Input type
    if 'input' in selector and 'type=' in selector:
        match = re.search(r'type=[\'"]([^\'"]+)[\'"]', selector)
        if match:
            return f'the {match.group(1)} field'

    # Button
    if 'button' in selector:
        return 'the button'

    # Link
    if 'a' in selector:
        return 'the link'

    return f'the element ({selector})'


@tool("generate_step_definitions", "Generate Python step definitions", {
    "feature_file": str,
    "framework": str,
    "actions": list,
})
async def generate_step_definitions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Python step definitions."""
    framework = args['framework']
    actions = args['actions']

    if framework == 'behave':
        return {"steps_content": _generate_behave_steps(actions)}
    else:
        return {"steps_content": _generate_pytest_steps(actions)}


def _generate_behave_steps(actions: List[Dict]) -> str:
    """Generate Behave step definitions."""
    steps = '''"""
Auto-generated step definitions.
"""

from playwright.sync_api import Page, expect
from behave import given, when, then

'''

    for i, action in enumerate(actions):
        action_type = action['type']
        selector = action.get('selector', '')
        value = action.get('value', '')
        element = _describe_element(selector)

        if action_type == 'goto':
            steps += f'''
@given('I am on the page with URL "{selector}"')
def step_navigate_to_url(context):
    """Navigate to URL."""
    context.page.goto("{selector}")
'''

        elif action_type in ['click', 'check']:
            steps += f'''
@when('I click {element}')
def step_click_element(context):
    """Click element."""
    context.page.click("{selector}")
'''

        elif action_type in ['fill', 'type']:
            steps += f'''
@when('I enter "{{value}}" in {element}')
def step_fill_element(context, value):
    """Fill element."""
    context.page.fill("{selector}", value)
'''

        elif action_type == 'select':
            steps += f'''
@when('I select "{{option}}" from {element}')
def step_select_option(context, option):
    """Select option."""
    context.page.select_option("{selector}", option)
'''

    return steps


def _generate_pytest_steps(actions: List[Dict]) -> str:
    """Generate pytest-bdd step definitions."""
    steps = '''"""
Auto-generated step definitions.
"""

from playwright.sync_api import Page, expect
from pytest_bdd import given, when, then

'''

    for i, action in enumerate(actions):
        action_type = action['type']
        selector = action.get('selector', '')
        value = action.get('value', '')
        element = _describe_element(selector)

        if action_type == 'goto':
            steps += f'''
@given('I am on the page with URL "{selector}"')
def step_navigate_to_url(page: Page):
    """Navigate to URL."""
    page.goto("{selector}")
'''

        elif action_type in ['click', 'check']:
            steps += f'''
@when('I click {element}')
def step_click_element(page: Page):
    """Click element."""
    page.click("{selector}")
'''

        elif action_type in ['fill', 'type']:
            steps += f'''
@when('I enter "{{value}}" in {element}')
def step_fill_element(page: Page, value):
    """Fill element."""
    page.fill("{selector}", value)
'''

        elif action_type == 'select':
            steps += f'''
@when('I select "{{option}}" from {element}')
def step_select_option(page: Page, option):
    """Select option."""
    page.select_option("{selector}", option)
'''

    return steps


# Create the MCP server
bdd_server = create_sdk_mcp_server(
    name="bdd-tools",
    version="1.0.0",
    tools=[
        parse_playwright_script,
        generate_feature_file,
        generate_step_definitions,
    ],
)
```

---

## 4. Data Models

### 4.1 Configuration Models

**File:** `src/claude_playwright_agent/models/config.py`

```python
"""
Configuration data models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class FrameworkConfig(BaseModel):
    """Framework configuration."""

    bdd: str = Field(default="behave", description="BDD framework")
    browser: str = Field(default="chromium", description="Default browser")
    headless: bool = Field(default=True, description="Headless mode")
    base_url: str = Field(default="", description="Base URL")
    timeout: int = Field(default=30000, description="Timeout in ms")


class ExecutionConfig(BaseModel):
    """Execution configuration."""

    parallel: int = Field(default=4, description="Parallel workers")
    retry: int = Field(default=2, description="Retry attempts")
    self_healing: bool = Field(default=False, description="Enable self-healing")


class ReportingConfig(BaseModel):
    """Reporting configuration."""

    formats: List[str] = Field(default_factory=lambda: ["html"], description="Report formats")
    include_screenshots: bool = Field(default=True, description="Include screenshots")
    include_ai: bool = Field(default=False, description="Include AI analysis")


class AgentConfig(BaseModel):
    """Main agent configuration."""

    framework: FrameworkConfig = Field(default_factory=FrameworkConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
```

### 4.2 Test Result Models

**File:** `src/claude_playwright_agent/models/results.py`

```python
"""
Test result data models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class StepResult(BaseModel):
    """Step execution result."""

    name: str
    status: str = Field(description="passed, failed, skipped")
    duration: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None


class ScenarioResult(BaseModel):
    """Scenario execution result."""

    name: str
    feature: str
    status: str
    duration: float
    steps: List[StepResult]
    tags: List[str] = Field(default_factory=list)


class TestResults(BaseModel):
    """Complete test results."""

    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    scenarios: List[ScenarioResult]
    timestamp: datetime = Field(default_factory=datetime.now)


class FailureCluster(BaseModel):
    """Cluster of similar failures."""

    name: str
    count: int
    failures: List[ScenarioResult]
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None


class AnalysisReport(BaseModel):
    """AI analysis report."""

    results: TestResults
    clusters: List[FailureCluster]
    flaky_tests: List[str]
    executive_summary: str
    recommendations: List[str]
```

---

## 5. Interfaces

### 5.1 Agent Interface

**File:** `src/claude_playwright_agent/interfaces/agent.py`

```python
"""
Agent interface definitions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IAgent(ABC):
    """Base agent interface."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class IExecutableAgent(IAgent):
    """Interface for agents that execute tests."""

    @abstractmethod
    async def execute(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tests."""
        pass


class IAnalysisAgent(IAgent):
    """Interface for agents that analyze results."""

    @abstractmethod
    async def analyze(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results."""
        pass

    @abstractmethod
    async def generate_report(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report."""
        pass


class IConversionAgent(IAgent):
    """Interface for agents that convert formats."""

    @abstractmethod
    async def ingest(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest and convert source."""
        pass
```

### 5.2 Tool Interface

**File:** `src/claude_playwright_agent/interfaces/tool.py`

```python
"""
Tool interface definitions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ITool(ABC):
    """Base tool interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool."""
        pass


class IParserTool(ITool):
    """Interface for parser tools."""

    @abstractmethod
    async def parse(self, source: str) -> Dict[str, Any]:
        """Parse source data."""
        pass


class IGeneratorTool(ITool):
    """Interface for generator tools."""

    @abstractmethod
    async def generate(self, data: Dict[str, Any]) -> str:
        """Generate output."""
        pass
```

---

## 6. State Management

### 6.1 Session State

**File:** `src/claude_playwright_agent/state/session.py`

```python
"""
Session state management.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


class SessionState:
    """Manage agent session state."""

    def __init__(self, session_id: str, project_path: Optional[str] = None):
        self.session_id = session_id
        self.project_path = project_path
        self.created_at = datetime.now()
        self.data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set a session value."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a session value."""
        return self.data.get(key, default)

    def save(self) -> None:
        """Save session to disk."""
        if self.project_path:
            state_dir = Path(self.project_path) / '.cpa' / 'state'
            state_dir.mkdir(parents=True, exist_ok=True)

            state_file = state_dir / f'{self.session_id}.json'
            with open(state_file, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'created_at': self.created_at.isoformat(),
                    'data': self.data,
                }, f, indent=2)

    @classmethod
    def load(cls, session_id: str, project_path: str) -> 'SessionState':
        """Load session from disk."""
        state_file = Path(project_path) / '.cpa' / 'state' / f'{session_id}.json'

        with open(state_file, 'r') as f:
            data = json.load(f)

        session = cls(session_id, project_path)
        session.data = data.get('data', {})
        return session
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-11
