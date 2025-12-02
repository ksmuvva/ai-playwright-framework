"""
AI-Powered Playwright Test Framework Setup
Fallback setup.py for systems that don't support pyproject.toml
"""

from setuptools import setup, find_packages

setup(
    name="ai-playwright-test-framework",
    version="2.0.0",
    description="AI-powered Playwright test automation framework with BDD support",
    author="AI Playwright Framework Team",
    license="MIT",
    packages=find_packages(where=".", exclude=["tests*", "docs*"]),
    python_requires=">=3.8",
    install_requires=[
        # Core testing framework
        "playwright>=1.40.0",
        "behave>=1.2.6",
        "pytest>=7.4.3",

        # AI providers
        "anthropic>=0.30.0",
        "openai>=1.6.1",

        # AI Observability & Tracing
        "arize-phoenix>=12.16.0",
        "opentelemetry-api>=1.38.0",
        "opentelemetry-sdk>=1.38.0",
        "opentelemetry-exporter-otlp>=1.38.0",

        # Test data generation
        "faker>=20.1.0",

        # Utilities
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.3",
        "structlog>=24.1.0",
        "colorama>=0.4.6",
        "requests>=2.31.0",
        "pyyaml>=6.0.0",
        "jinja2>=3.1.0",

        # Reporting
        "allure-behave>=2.13.2",
    ],
    extras_require={
        "dev": [
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.9",
        ]
    },
    entry_points={
        "console_scripts": [
            "setup-browsers=scripts.setup:install_browsers",
            "verify-setup=scripts.setup:verify_installation",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
