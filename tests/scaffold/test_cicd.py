"""
Tests for CI/CD Template Generator.

Tests cover:
- GitHub Actions workflow generation
- GitLab CI/CD configuration generation
- Jenkins pipeline generation
- Azure DevOps pipeline generation
- CircleCI configuration generation
- Custom configuration options
"""

from pathlib import Path

import pytest

from claude_playwright_agent.scaffold.cicd import (
    CICDTemplateGenerator,
    CIConfig,
    CIPlatform,
    TestFramework as CICTestFramework,
    generate_ci_config,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for testing."""
    return tmp_path / "output"


@pytest.fixture
def generator() -> CICDTemplateGenerator:
    """Create a template generator instance."""
    return CICDTemplateGenerator()


@pytest.fixture
def basic_config() -> CIConfig:
    """Create a basic CI/CD configuration."""
    return CIConfig(
        platform=CIPlatform.GITHUB_ACTIONS,
        framework=CICTestFramework.BEHAVE,
        python_version="3.12",
        node_version="20",
        playwright_version="1.40.0",
        parallel_jobs=4,
        enable_cache=True,
        enable_artifacts=True,
    )


# =============================================================================
# GitHub Actions Tests
# =============================================================================


class TestGitHubActions:
    """Tests for GitHub Actions workflow generation."""

    def test_generate_basic_workflow(self, generator: CICDTemplateGenerator, basic_config: CIConfig, temp_dir: Path) -> None:
        """Test generating a basic GitHub Actions workflow."""
        output_path = temp_dir / ".github" / "workflows" / "test.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(basic_config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check for key sections
        assert "name:" in content
        assert "on:" in content
        assert "jobs:" in content
        assert "runs-on:" in content
        assert "steps:" in content

    def test_workflow_includes_python_setup(self, generator: CICDTemplateGenerator, basic_config: CIConfig, temp_dir: Path) -> None:
        """Test that workflow includes Python setup."""
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(basic_config, output_path)
        content = output_path.read_text()

        assert "actions/setup-python@v5" in content
        assert "python-version:" in content

    def test_workflow_includes_node_setup(self, generator: CICDTemplateGenerator, basic_config: CIConfig, temp_dir: Path) -> None:
        """Test that workflow includes Node.js setup."""
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(basic_config, output_path)
        content = output_path.read_text()

        assert "actions/setup-node@v4" in content
        assert "node-version:" in content

    def test_workflow_with_cache(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test workflow with caching enabled."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            enable_cache=True,
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "actions/cache@v4" in content
        assert "Playwright binaries" in content or "Python packages" in content

    def test_workflow_without_cache(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test workflow with caching disabled."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            enable_cache=False,
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        # Cache steps should not be present
        assert "actions/cache@v4" not in content

    def test_workflow_with_artifacts(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test workflow with artifact upload enabled."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            enable_artifacts=True,
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "actions/upload-artifact@v4" in content
        assert "test-results" in content

    def test_workflow_with_slack_notifications(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test workflow with Slack notifications."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            enable_notifications=True,
            slack_webhook="https://hooks.slack.com/services/xxx",
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "action-slack@v3" in content or "slack" in content.lower()
        assert "SLACK_WEBHOOK" in content

    def test_workflow_with_custom_python_version(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test workflow with custom Python version."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            python_version="3.11",
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert 'PYTHON_VERSION: \'3.11\'' in content or "python-version: 3.11" in content

    def test_workflow_with_environment_variables(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test workflow with custom environment variables."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            environment={"API_KEY": "secret", "BASE_URL": "https://api.example.com"},
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "API_KEY" in content
        assert "BASE_URL" in content
        assert "secrets." in content

    def test_workflow_matrix_builds(self, generator: CICDTemplateGenerator, basic_config: CIConfig, temp_dir: Path) -> None:
        """Test that workflow includes matrix builds for OS."""
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(basic_config, output_path)
        content = output_path.read_text()

        assert "matrix:" in content
        assert "os:" in content
        assert "ubuntu-latest" in content
        assert "windows-latest" in content or "macos-latest" in content


# =============================================================================
# GitLab CI Tests
# =============================================================================


class TestGitLabCI:
    """Tests for GitLab CI/CD configuration generation."""

    def test_generate_gitlab_ci(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test generating GitLab CI configuration."""
        config = CIConfig(
            platform=CIPlatform.GITLAB_CI,
            framework=CICTestFramework.BEHAVE,
        )
        output_path = temp_dir / ".gitlab-ci.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check for key sections
        assert "stages:" in content
        assert "before_script:" in content
        assert "bdd_tests:" in content

    def test_gitlab_ci_with_cache(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test GitLab CI with caching enabled."""
        config = CIConfig(
            platform=CIPlatform.GITLAB_CI,
            enable_cache=True,
        )
        output_path = temp_dir / ".gitlab-ci.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "cache:" in content
        assert "paths:" in content

    def test_gitlab_ci_with_artifacts(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test GitLab CI with artifacts enabled."""
        config = CIConfig(
            platform=CIPlatform.GITLAB_CI,
            enable_artifacts=True,
        )
        output_path = temp_dir / ".gitlab-ci.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "artifacts:" in content
        assert "paths:" in content
        assert "expire_in:" in content


# =============================================================================
# Jenkins Tests
# =============================================================================


class TestJenkins:
    """Tests for Jenkins pipeline generation."""

    def test_generate_jenkinsfile(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test generating Jenkins pipeline."""
        config = CIConfig(
            platform=CIPlatform.JENKINS,
            framework=CICTestFramework.BEHAVE,
        )
        output_path = temp_dir / "Jenkinsfile"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check for key sections
        assert "pipeline {" in content
        assert "agent any" in content
        assert "stages {" in content
        assert "steps {" in content
        assert "post {" in content

    def test_jenkins_with_environment(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test Jenkins pipeline with environment variables."""
        config = CIConfig(
            platform=CIPlatform.JENKINS,
            environment={"API_KEY": "secret"},
        )
        output_path = temp_dir / "Jenkinsfile"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "environment {" in content
        assert "API_KEY" in content


# =============================================================================
# Azure DevOps Tests
# =============================================================================


class TestAzureDevOps:
    """Tests for Azure DevOps pipeline generation."""

    def test_generate_azure_pipelines(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test generating Azure DevOps pipeline."""
        config = CIConfig(
            platform=CIPlatform.AZURE_DEVOPS,
            framework=CICTestFramework.BEHAVE,
        )
        output_path = temp_dir / "azure-pipelines.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check for key sections
        assert "trigger:" in content
        assert "variables:" in content
        assert "stages:" in content
        assert "jobs:" in content


# =============================================================================
# CircleCI Tests
# =============================================================================


class TestCircleCI:
    """Tests for CircleCI configuration generation."""

    def test_generate_circleci_config(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test generating CircleCI configuration."""
        config = CIConfig(
            platform=CIPlatform.CIRCLE_CI,
            framework=CICTestFramework.BEHAVE,
        )
        output_path = temp_dir / ".circleci" / "config.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check for key sections
        assert "version:" in content
        assert "executors:" in content
        assert "jobs:" in content
        assert "workflows:" in content

    def test_circleci_with_parallelism(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test CircleCI configuration with parallel jobs."""
        config = CIConfig(
            platform=CIPlatform.CIRCLE_CI,
            parallel_jobs=8,
        )
        output_path = temp_dir / ".circleci" / "config.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "parallelism: 8" in content


# =============================================================================
# Generate All Tests
# =============================================================================


class TestGenerateAll:
    """Tests for generating all CI/CD configurations."""

    def test_generate_all_platforms(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test generating all platform configurations."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            framework=CICTestFramework.BEHAVE,
        )

        generated = generator.generate_all(config, temp_dir)

        assert len(generated) == 5  # All 5 platforms

        # Check that all files were created
        for platform, path in generated.items():
            assert path.exists()
            assert path.parent.exists()


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_ci_config_with_string_platform(self, temp_dir: Path) -> None:
        """Test generate_ci_config with string platform."""
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generate_ci_config("github", output_path)

        assert output_path.exists()

    def test_generate_ci_config_with_invalid_platform(self, temp_dir: Path) -> None:
        """Test generate_ci_config with invalid platform raises error."""
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="Unsupported platform"):
            generate_ci_config("invalid_platform", output_path)

    def test_generate_ci_config_with_custom_options(self, temp_dir: Path) -> None:
        """Test generate_ci_config with custom options."""
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generate_ci_config(
            "github",
            output_path,
            framework="pytest-bdd",
            python_version="3.10",
            parallel_jobs=2,
        )

        content = output_path.read_text()
        # Verify Python version was applied
        assert "3.10" in content
        # Verify it's a valid workflow
        assert "name:" in content
        assert "on:" in content
        assert "jobs:" in content


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_environment_variables(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test with empty environment variables dict."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            environment={},
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Should not raise an error
        generator.generate(config, output_path)
        assert output_path.exists()

    def test_no_triggers(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test with no triggers specified."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            triggers=[],
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Should still generate a valid workflow
        generator.generate(config, output_path)
        assert output_path.exists()

    def test_pytest_bdd_framework(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test with pytest-bdd framework."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            framework=CICTestFramework.PYTEST_BDD,
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        assert output_path.exists()

    def test_custom_install_command(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test with custom install command."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            install_command="poetry install",
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "poetry install" in content

    def test_custom_test_command(self, generator: CICDTemplateGenerator, temp_dir: Path) -> None:
        """Test with custom test command."""
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            test_command="pytest tests/",
        )
        output_path = temp_dir / "workflow.yml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)
        content = output_path.read_text()

        assert "pytest tests/" in content
