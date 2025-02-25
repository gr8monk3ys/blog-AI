#!/usr/bin/env python
"""
Command-line script to run all tests for the blog-AI project.
"""
import sys
import os
from tests.run_all_tests import run_all_tests


def main():
    """Run all tests and print a summary."""
    print("Running all tests for the blog-AI project...")
    result = run_all_tests()
    
    # Print a summary
    print("\nTest Summary:")
    print(f"  Ran {result.testsRun} tests")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    
    # Exit with appropriate code
    return len(result.failures) + len(result.errors)


if __name__ == '__main__':
    sys.exit(main())
