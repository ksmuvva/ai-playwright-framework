"""
E2E Test Runner for Demo Project
Runs all BDD tests and generates report
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path


async def run_tests():
    """Run all E2E tests."""
    print("=" * 70)
    print(" " * 20 + "E2E TEST EXECUTION")
    print("=" * 70)
    print()

    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"test_report_{timestamp}.txt"

    # Run pytest with BDD
    print("Running E2E Tests...")
    print("-" * 70)

    cmd = [
        sys.executable, "-m", "pytest",
        "steps/",
        "-v",
        "--tb=short",
        "-s",
        f"--html=reports/report_{timestamp}.html",
        "--self-contained-html",
    ]

    print(f"Command: {' '.join(cmd)}")
    print()

    # Run tests
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )

    # Save output
    with open(report_file, "w") as f:
        f.write(f"E2E Test Report - {datetime.now()}\n")
        f.write("=" * 70 + "\n\n")
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\n\nSTDERR:\n")
        f.write(result.stderr)
        f.write(f"\n\nExit Code: {result.returncode}\n")

    # Print output
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print()
    print("-" * 70)
    print(f"Report saved to: {report_file}")
    print()

    return result.returncode == 0


async def main():
    """Main entry point."""
    success = await run_tests()
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
