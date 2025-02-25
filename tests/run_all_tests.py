"""
Run all tests for the blog-AI project.
"""
import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from tests.test_blog import TestBlogModule
from tests.test_book import TestBookModule
from tests.test_planning import (
    TestContentCalendar,
    TestCompetitorAnalysis,
    TestTopicClusters,
    TestContentOutline
)
from tests.test_integrations import (
    TestGitHubIntegration,
    TestMediumIntegration,
    TestWordPressIntegration
)


def run_all_tests():
    """Run all tests for the blog-AI project."""
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases to the suite
    test_suite.addTest(unittest.makeSuite(TestBlogModule))
    test_suite.addTest(unittest.makeSuite(TestBookModule))
    test_suite.addTest(unittest.makeSuite(TestContentCalendar))
    test_suite.addTest(unittest.makeSuite(TestCompetitorAnalysis))
    test_suite.addTest(unittest.makeSuite(TestTopicClusters))
    test_suite.addTest(unittest.makeSuite(TestContentOutline))
    test_suite.addTest(unittest.makeSuite(TestGitHubIntegration))
    test_suite.addTest(unittest.makeSuite(TestMediumIntegration))
    test_suite.addTest(unittest.makeSuite(TestWordPressIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return the result
    return result


if __name__ == '__main__':
    print("Running all tests for the blog-AI project...")
    result = run_all_tests()
    
    # Print a summary
    print("\nTest Summary:")
    print(f"  Ran {result.testsRun} tests")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    
    # Exit with appropriate code
    sys.exit(len(result.failures) + len(result.errors))
