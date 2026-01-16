"""
CI/CD Template Generator for Claude Playwright Agent.

This module provides template generation for CI/CD pipelines:
- GitHub Actions
- GitLab CI/CD
- Jenkins
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Any


class CIPlatform(str, Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github"
    GITLAB_CI = "gitlab"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure"
    CIRCLE_CI = "circleci"


class TestFramework(str, Enum):
    """BDD test frameworks."""
    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"


@dataclass
class CIConfig:
    """Configuration for CI/CD pipeline generation."""
    platform: CIPlatform
    framework: TestFramework = TestFramework.BEHAVE
    python_version: str = "3.12"
    node_version: str = "20"
    playwright_version: str = "1.40.0"
    parallel_jobs: int = 4
    enable_cache: bool = True
    enable_artifacts: bool = True
    enable_notifications: bool = False
    slack_webhook: str = ""
    report_format: str = "html"
    triggers: list[str] = field(default_factory=lambda: ["push", "pull_request"])
    branches: list[str] = field(default_factory=lambda: ["main", "develop"])
    environment: dict[str, str] = field(default_factory=dict)
    install_command: str = "pip install -r requirements.txt"
    test_command: str = "cpa run test"
    browser_install_command: str = "playwright install chromium"


class CICDTemplateGenerator:
    """Generate CI/CD pipeline configuration files."""

    def generate(self, config: CIConfig, output_path: Path) -> None:
        """Generate CI/CD configuration file."""
        generator = {
            CIPlatform.GITHUB_ACTIONS: self._generate_github_actions,
            CIPlatform.GITLAB_CI: self._generate_gitlab_ci,
            CIPlatform.JENKINS: self._generate_jenkins,
            CIPlatform.AZURE_DEVOPS: self._generate_azure_devops,
            CIPlatform.CIRCLE_CI: self._generate_circle_ci,
        }.get(config.platform, self._generate_github_actions)

        content = generator(config)
        output_path.write_text(content, encoding="utf-8")

    def _generate_github_actions(self, config: CIConfig) -> str:
        """Generate GitHub Actions workflow."""
        triggers_yaml = "\n".join(f"      - {t}" for t in config.triggers)

        cache_steps = ""
        if config.enable_cache:
            cache_steps = f"""
      - name: Cache Playwright binaries
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/ms-playwright
            node_modules/.cache
          key: ${{{{ runner.os }}}}-playwright-${{{{ hashFiles('**/playwright-*.lock') }}}}
          restore-keys: |
            ${{{{ runner.os }}}}-playwright-

      - name: Cache Python packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}
          restore-keys: |
            ${{{{ runner.os }}}}-pip-
"""

        artifacts_step = ""
        if config.enable_artifacts:
            artifacts_step = f"""
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{{{ github.sha }}}}
          path: |
            reports/
            screenshots/
            videos/
          retention-days: 30

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: html-report-${{{{ github.sha }}}}
          path: reports/*.html
"""

        notification_step = ""
        if config.enable_notifications and config.slack_webhook:
            notification_step = f"""
      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{{{ job.status }}}}
          text: 'Test run ${{{{ job.status }}}}! ${{{{ github.event.pull_request.html_url || github.event.head_commit.url }}}}'
          webhook_url: ${{{{ secrets.SLACK_WEBHOOK }}}}
"""

        env_vars = ""
        if config.environment:
            env_vars = "\n".join(f"          {k}: ${{{{ secrets.{k} }}}}" for k in config.environment.keys())

        return dedent(f"""\
name: 'Playwright BDD Tests'

on:
  push:
    branches:
{triggers_yaml}
  pull_request:
    branches:
      - main
      - develop
  workflow_dispatch:

env:
  PYTHON_VERSION: '{config.python_version}'
  NODE_VERSION: '{config.node_version}'

jobs:
  test:
    name: 'BDD Tests (${{{{ matrix.os }}}})'
    runs-on: ${{{{ matrix.os }}}}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
          cache: 'pip'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
{cache_steps}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          {config.install_command}

      - name: Install Playwright browsers
        run: |
          {config.browser_install_command}
        shell: bash

      - name: Run BDD tests
        env:
{env_vars}
        run: |
          {config.test_command}
        shell: bash

      - name: Generate report
        if: always()
        run: |
          cpa report --format {config.report_format}

{artifacts_step}
{notification_step}
    """)

    def _generate_gitlab_ci(self, config: CIConfig) -> str:
        """Generate GitLab CI/CD configuration."""
        cache_config = ""
        if config.enable_cache:
            cache_config = f"""
cache:
  key: "$CI_COMMIT_REF_SLUG"
  paths:
    - .cache/pip
    - .cache/ms-playwright
    - node_modules/.cache
"""

        artifacts_config = ""
        if config.enable_artifacts:
            artifacts_config = f"""
  artifacts:
    when: always
    paths:
      - reports/
      - screenshots/
      - videos/
    expire_in: 30 days
    reports:
      junit: reports/junit.xml
"""

        env_vars = ""
        if config.environment:
            env_vars = "\n".join(f"    {k}: ${{{{ vars.{k}}}}}" for k in config.environment.keys())

        return dedent(f"""\
stages:
  - test
  - report
  - notify

variables:
  PYTHON_VERSION: "{config.python_version}"
  NODE_VERSION: "{config.node_version}"
  PLAYWRIGHT_BROWSERS_PATH: "$CI_PROJECT_DIR/.cache/ms-playwright"

{cache_config}
before_script:
  - python -m pip install --upgrade pip
  - {config.install_command}
  - {config.browser_install_command}

bdd_tests:
  stage: test
  image: mcr.microsoft.com/playwright:v{config.playwright_version}-jammy
  parallel: {config.parallel_jobs}
  script:
    - |
{env_vars}
      {config.test_command}
  coverage: '/(?i)total.*? (100(?:\\.0+)?\\%|[1-9]?\\d%)/'
{artifacts_config}
  only:
    variables:
      - $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_PIPELINE_SOURCE == "merge_request_event"

test_report:
  stage: report
  image: python:{config.python_version}
  script:
    - cpa report --format {config.report_format}
  dependencies:
    - bdd_tests
  when: always
  only:
    variables:
      - $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_PIPELINE_SOURCE == "merge_request_event"

notify_slack:
  stage: notify
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - |
      curl -X POST -H 'Content-type: application/json' \\
        --data '{{"text":"Pipeline ${{{{CI_PIPELINE_SOURCE}}}} finished with status ${{{{CI_JOB_STATUS}}}} in ${{{{CI_PROJECT_PATH}}}} (${{{{CI_COMMIT_SHA}}}})"}}' \\
        {config.slack_webhook or '$SLACK_WEBHOOK'}
  when: always
  only:
    variables:
      - $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_PIPELINE_SOURCE == "merge_request_event"
        """)

    def _generate_jenkins(self, config: CIConfig) -> str:
        """Generate Jenkins pipeline configuration."""
        env_block = ""
        if config.environment:
            env_vars = "\n        ".join(f'{k} = credentials("{k}")' for k in config.environment.keys())
            env_block = f"""
        environment {
            {env_vars}
        }
"""

        artifacts_block = ""
        if config.enable_artifacts:
            artifacts_block = """
        // Archive test results and reports
        archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
        archiveArtifacts artifacts: 'screenshots/**/*', fingerprint: true
        archiveArtifacts artifacts: 'videos/**/*', fingerprint: true

        // Publish JUnit test results
        junit testResults: 'reports/junit.xml', allowEmptyResults: true

        // Publish HTML report
        publishHTML(target: [
            reportDir: 'reports',
            reportFiles: '*.html',
            reportName: 'BDD Test Report',
            keepAll: true,
            alwaysLinkToLastBuild: true,
            allowMissing: true
        ])
"""

        notification_block = ""
        if config.enable_notifications and config.slack_webhook:
            notification_block = f'''
        // Send Slack notification
        slackSend(
            color: currentBuild.result == 'SUCCESS' ? 'good' : 'danger',
            message: "Job ${{env.JOB_NAME}} [${{env.BUILD_NUMBER}}] completed with status: ${{currentBuild.result}}\\nURL: ${{env.BUILD_URL}}",
            channel: '#test-results',
            webhookURL: '{config.slack_webhook}'
        )
'''

        return dedent(f"""\
pipeline {{
    agent any

    options {{
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }}

    tools {{
        'Python {config.python_version}'
        'NodeJS {config.node_version}'
    }}

{env_block}
    stages {{
        stage('Setup') {{
            steps {{
                script {{
                    echo 'Installing dependencies...'
                    sh '''
                        python -m pip install --upgrade pip
                        {config.install_command}
                        {config.browser_install_command}
                    '''
                }}
            }}
        }}

        stage('BDD Tests') {{
            parallel {{
                stage('Smoke Tests') {{
                    steps {{
                        script {{
                            sh '{config.test_command} --tags @smoke'
                        }}
                    }}
                }}
                stage('Regression Tests') {{
                    steps {{
                        script {{
                            sh '{config.test_command} --tags @regression'
                        }}
                    }}
                }}
            }}
        }}

        stage('Report') {{
            steps {{
                script {{
                    echo 'Generating test report...'
                    sh 'cpa report --format {config.report_format}'
                }}
            }}
        }}
    }}

    post {{
        always {{
            echo 'Cleaning up...'
            cleanWs()
        }}
        success {{
            echo 'Pipeline completed successfully!'
{notification_block}
        }}
        failure {{
            echo 'Pipeline failed!'
{notification_block}
        }}
        always {{
            script {{
{artifacts_block}
            }}
        }}
    }}
}}
""")

    def _generate_azure_devops(self, config: CIConfig) -> str:
        """Generate Azure DevOps pipeline configuration."""
        return dedent(f"""\
# Azure Pipelines CI/CD configuration for Claude Playwright Agent
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    exclude:
      - '**/*.md'
      - 'docs/**'

pr:
  branches:
    include:
      - main
      - develop

variables:
  pythonVersion: '{config.python_version}'
  nodeVersion: '{config.node_version}'

stages:
  - stage: Test
    displayName: 'BDD Test Stage'
    jobs:
      - job: 'BDD_Tests'
        displayName: 'Run BDD Tests'
        pool:
          vmImage: 'ubuntu-latest'

        steps:
          - task: UsePythonVersion@0
            displayName: 'Set Python version'
            inputs:
              versionSpec: '$(pythonVersion)'

          - task: NodeTool@0
            displayName: 'Set Node.js version'
            inputs:
              versionSpec: '$(nodeVersion)'

          - script: |
              python -m pip install --upgrade pip
              {config.install_command}
            displayName: 'Install dependencies'

          - script: |
              {config.browser_install_command}
            displayName: 'Install Playwright browsers'

          - script: |
              {config.test_command}
            displayName: 'Run BDD tests'
            env:
              # Add environment variables here
              CI: true

          - script: |
              cpa report --format {config.report_format}
            displayName: 'Generate test report'
            condition: always()

          - task: PublishTestResults@2
            displayName: 'Publish test results'
            condition: always()
            inputs:
              testResultsFiles: 'reports/junit.xml'
              testRunTitle: 'BDD Test Results'
              mergeTestResults: true

          - task: PublishHtmlReport@1
            displayName: 'Publish HTML report'
            condition: always()
            inputs:
              reportDir: 'reports'
              reportFiles: '*.html'

  - stage: Report
    displayName: 'Generate Reports'
    dependsOn: Test
    condition: always()
    jobs:
      - job: 'Report'
        displayName: 'Create Test Report'
        pool:
          vmImage: 'ubuntu-latest'

        steps:
          - script: |
              cpa report --format {config.report_format} --output reports/summary.html
            displayName: 'Generate summary report'
""")

    def _generate_circle_ci(self, config: CIConfig) -> str:
        """Generate CircleCI configuration."""
        cache_key = f"v1-dependencies-{{{{ checksum \"requirements.txt\" }}}}"

        return dedent(f"""\
version: 2.1

orbs:
  playwright: circleci/playwright@1.3.0

executors:
  python-executor:
    docker:
      - image: cimg/python:{config.python_version}-node
    resource_class: medium

jobs:
  bdd_tests:
    executor: python-executor
    parallelism: {config.parallel_jobs}
    steps:
      - checkout

      - restore_cache:
          keys:
            - {cache_key}
            - v1-dependencies-

      - run:
          name: Install dependencies
          command: |
            python -m pip install --upgrade pip
            {config.install_command}

      - run:
          name: Install Playwright browsers
          command: |
            {config.browser_install_command}

      - save_cache:
          paths:
            - ~/.local/share/pip
            - ~/.cache/ms-playwright
          key: {cache_key}

      - run:
          name: Run BDD tests
          command: |
            {config.test_command}

      - run:
          name: Generate report
          command: |
            cpa report --format {config.report_format}
          when: always()

      - store_test_results:
          path: reports

      - store_artifacts:
          path: reports
          destination: test-reports

      - store_artifacts:
          path: screenshots
          destination: screenshots

      - store_artifacts:
          path: videos
          destination: videos

workflows:
  version: 2
  test-workflow:
    jobs:
      - bdd_tests:
          filters:
            branches:
              only:
                - main
                - develop
""")

    def generate_all(self, config: CIConfig, output_dir: Path) -> dict[CIPlatform, Path]:
        """Generate all CI/CD configurations."""
        generated = {}

        for platform in CIPlatform:
            filename = {
                CIPlatform.GITHUB_ACTIONS: ".github/workflows/bdd-tests.yml",
                CIPlatform.GITLAB_CI: ".gitlab-ci.yml",
                CIPlatform.JENKINS: "Jenkinsfile",
                CIPlatform.AZURE_DEVOPS: "azure-pipelines.yml",
                CIPlatform.CIRCLE_CI: ".circleci/config.yml",
            }[platform]

            output_path = output_dir / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            self.generate(config, output_path)
            generated[platform] = output_path

        return generated


def generate_ci_config(
    platform: str | CIPlatform,
    output_path: Path,
    framework: str = "behave",
    **kwargs: Any,
) -> None:
    """
    Convenience function to generate CI/CD configuration.

    Args:
        platform: CI/CD platform (github, gitlab, jenkins, azure, circleci)
        output_path: Path to write configuration file
        framework: BDD framework (behave or pytest-bdd)
        **kwargs: Additional configuration options
    """
    if isinstance(platform, str):
        try:
            platform = CIPlatform(platform)
        except ValueError:
            raise ValueError(f"Unsupported platform: {platform}")

    if isinstance(framework, str):
        try:
            framework = TestFramework(framework)
        except ValueError:
            raise ValueError(f"Unsupported framework: {framework}")

    config = CIConfig(
        platform=platform,
        framework=framework,
        **kwargs,
    )

    generator = CICDTemplateGenerator()
    generator.generate(config, output_path)
