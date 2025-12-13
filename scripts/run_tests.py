#!/usr/bin/env python3
"""
Run all unit tests before commit.
Exit code 0 = all tests passed, safe to commit
Exit code 1 = tests failed, do not commit
"""

import subprocess
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

def run_tests():
    """Run pytest and return exit code."""
    print("=" * 60)
    print("🧪 Running unit tests...")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=False
    )
    
    return result.returncode

def run_linting():
    """Optional: Run linting checks."""
    # Could add flake8, mypy, etc. here
    pass

def main():
    """Run all checks."""
    print("\n🔍 Pre-commit checks for Find Better\n")
    
    # Run tests
    test_result = run_tests()
    
    print("\n" + "=" * 60)
    
    if test_result == 0:
        print("✅ All tests passed! Safe to commit.")
        print("=" * 60)
        return 0
    else:
        print("❌ Tests failed! Fix issues before committing.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

