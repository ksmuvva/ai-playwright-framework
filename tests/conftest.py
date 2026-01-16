"""
Pytest configuration for integration tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def features_dir(project_root):
    """Get features directory."""
    return project_root / "features"


@pytest.fixture(scope="session")
def pages_dir(project_root):
    """Get pages directory."""
    return project_root / "pages"


@pytest.fixture(scope="function")
async def memory_manager():
    """Provide a MemoryManager instance for testing."""
    from src.claude_playwright_agent.skills.builtins.e10_1_memory_manager import MemoryManager

    manager = MemoryManager(persist_to_disk=False)  # Don't persist during tests

    yield manager

    # Cleanup
    await manager.close()


@pytest.fixture(scope="function")
async def agent():
    """Provide an agent instance for testing."""
    from src.claude_playwright_agent.agents.ingest_agent import IngestionAgent

    agent = IngestionAgent(enable_memory=True)

    yield agent

    # Cleanup
    await agent.cleanup()


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture(scope="function")
def temp_project():
    """Provide a temporary project directory for testing."""
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())

    yield temp_dir

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
