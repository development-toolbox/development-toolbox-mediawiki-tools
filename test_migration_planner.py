#!/usr/bin/env python3
"""
Comprehensive Test Suite for migration_planner.py

This test suite validates all aspects of the migration_planner module including:
- Import and syntax testing
- Class instantiation testing
- Method testing with mocked data
- Configuration testing
- Integration testing
- Error handling testing

Author: Johan Sörell
Contact: https://github.com/J-SirL | https://se.linkedin.com/in/johansorell | automationblueprint.site
Date: 2025
Version: 1.0.0
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
from typing import Dict, Any, List
import requests

# Add the migration directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'migration'))

try:
    import migration_planner
    from migration_planner import MigrationPlanner, load_config, main
except ImportError as e:
    print(f"❌ Failed to import migration_planner: {e}")
    sys.exit(1)


class TestMigrationPlannerImports(unittest.TestCase):
    """Test import and syntax validation."""

    def test_imports_successful(self):
        """Test that all required imports are successful."""
        # These should not raise ImportError
        import migration.migration_planner
        from migration.migration_planner import MigrationPlanner, load_config, main
        self.assertTrue(True)  # If we get here, imports succeeded

    def test_required_dependencies(self):
        """Test that required dependencies are available."""
        try:
            import requests
            import dotenv
        except ImportError as e:
            self.fail(f"Required dependency missing: {e}")

    def test_module_attributes(self):
        """Test that the module has expected attributes and functions."""
        import migration.migration_planner as mp
        
        # Check class exists
        self.assertTrue(hasattr(mp, 'MigrationPlanner'))
        self.assertTrue(callable(mp.MigrationPlanner))
        
        # Check functions exist
        self.assertTrue(hasattr(mp, 'load_config'))
        self.assertTrue(callable(mp.load_config))
        
        self.assertTrue(hasattr(mp, 'main'))
        self.assertTrue(callable(mp.main))


class TestMigrationPlannerInstantiation(unittest.TestCase):
    """Test MigrationPlanner class instantiation and initialization."""

    def test_valid_instantiation(self):
        """Test successful instantiation with valid parameters."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        self.assertEqual(planner.organization, "test-org")
        self.assertEqual(planner.project, "test-project")
        self.assertEqual(planner.pat, "test-pat")
        self.assertEqual(planner.base_url, "https://dev.azure.com/test-org/test-project/_apis")
        
        # Check session is configured
        self.assertIsInstance(planner.session, requests.Session)
        self.assertIn('Authorization', planner.session.headers)
        self.assertIn('Content-Type', planner.session.headers)
        self.assertIn('User-Agent', planner.session.headers)

    def test_empty_parameters(self):
        """Test instantiation fails with empty parameters."""
        with self.assertRaises(ValueError) as context:
            MigrationPlanner("", "test-project", "test-pat")
        self.assertIn("Organization, project, and personal access token are required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            MigrationPlanner("test-org", "", "test-pat")
        self.assertIn("Organization, project, and personal access token are required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            MigrationPlanner("test-org", "test-project", "")
        self.assertIn("Organization, project, and personal access token are required", str(context.exception))

    def test_none_parameters(self):
        """Test instantiation fails with None parameters."""
        with self.assertRaises(ValueError):
            MigrationPlanner(None, "test-project", "test-pat")

        with self.assertRaises(ValueError):
            MigrationPlanner("test-org", None, "test-pat")

        with self.assertRaises(ValueError):
            MigrationPlanner("test-org", "test-project", None)

    def test_authentication_header(self):
        """Test that authentication header is properly set."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        # The auth header should be Basic auth with base64 encoded :pat
        auth_header = planner.session.headers['Authorization']
        self.assertTrue(auth_header.startswith('Basic '))
        
        # Decode and verify
        import base64
        encoded_part = auth_header.split(' ')[1]
        decoded = base64.b64decode(encoded_part).decode()
        self.assertEqual(decoded, ":test-pat")


class TestMigrationPlannerMethods(unittest.TestCase):
    """Test MigrationPlanner methods with mocked data."""

    def setUp(self):
        """Set up test fixtures."""
        self.planner = MigrationPlanner("test-org", "test-project", "test-pat")

    @patch('requests.Session.get')
    def test_make_api_request_success(self, mock_get):
        """Test successful API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"value": [{"id": "123", "name": "test-wiki"}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.planner._make_api_request('GET', 'https://test.com/api')
        
        self.assertEqual(result, {"value": [{"id": "123", "name": "test-wiki"}]})
        mock_get.assert_called_once_with('https://test.com/api', timeout=30)

    @patch('requests.Session.get')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_make_api_request_timeout_retry(self, mock_print, mock_get):
        """Test API request with timeout and retry logic."""
        # First call times out, second succeeds
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            mock_response
        ]

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.planner._make_api_request('GET', 'https://test.com/api', max_retries=2)
        
        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_get.call_count, 2)

    @patch('requests.Session.get')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_make_api_request_auth_failure(self, mock_print, mock_get):
        """Test API request with authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            self.planner._make_api_request('GET', 'https://test.com/api')

    @patch.object(MigrationPlanner, '_make_api_request')
    def test_get_wikis_success(self, mock_api):
        """Test successful wiki retrieval."""
        mock_api.return_value = {
            "value": [
                {"id": "wiki1", "name": "Project Wiki", "type": "projectWiki"},
                {"id": "wiki2", "name": "Code Wiki", "type": "codeWiki"}
            ]
        }

        wikis = self.planner.get_wikis()
        
        self.assertEqual(len(wikis), 2)
        self.assertEqual(wikis[0]['name'], 'Project Wiki')
        mock_api.assert_called_once()

    @patch.object(MigrationPlanner, '_make_api_request')
    def test_get_wikis_empty_response(self, mock_api):
        """Test wiki retrieval with empty response."""
        mock_api.return_value = {}

        wikis = self.planner.get_wikis()
        
        self.assertEqual(wikis, [])

    @patch.object(MigrationPlanner, '_make_api_request')
    def test_get_wiki_pages_success(self, mock_api):
        """Test successful page retrieval."""
        mock_api.return_value = {
            "value": [
                {"id": "page1", "path": "/Home", "isParentPage": False},
                {"id": "page2", "path": "/Documentation", "isParentPage": True},
                {"id": "page3", "path": "/Documentation/API", "isParentPage": False}
            ]
        }

        pages = self.planner.get_wiki_pages("wiki1")
        
        self.assertEqual(len(pages), 3)
        self.assertEqual(pages[0]['path'], '/Home')
        mock_api.assert_called_once()

    @patch.object(MigrationPlanner, '_make_api_request')
    def test_get_page_content_success(self, mock_api):
        """Test successful page content retrieval."""
        test_content = "# Test Page\n\nThis is a test page with some content."
        mock_api.return_value = {"content": test_content}

        content = self.planner.get_page_content("wiki1", "page1")
        
        self.assertEqual(content, test_content)

    @patch.object(MigrationPlanner, '_make_api_request')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_get_page_content_error_handling(self, mock_print, mock_api):
        """Test page content retrieval with error handling."""
        mock_api.side_effect = requests.RequestException("API error")

        content = self.planner.get_page_content("wiki1", "page1")
        
        self.assertEqual(content, '')  # Should return empty string on error

    def test_analyze_content_complexity_simple(self):
        """Test content complexity analysis with simple content."""
        simple_content = """# Simple Page

This is a simple page with just text and a header.

Some regular text here.
"""
        
        analysis = self.planner.analyze_content_complexity(simple_content)
        
        # Check basic metrics
        self.assertEqual(analysis['headers'], 1)
        self.assertEqual(analysis['complexity_level'], 'Low')
        self.assertGreater(analysis['word_count'], 0)

    def test_analyze_content_complexity_complex(self):
        """Test content complexity analysis with complex content."""
        complex_content = """# Complex Page

This is a complex page with multiple elements.

## Tables
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

## Code Examples
```python
def hello_world():
    print("Hello, World!")
```

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}
```

## Images
![Test Image](test.png)
![Another Image](another.png)

## Links
[Link 1](http://example.com)
[Link 2](http://another.com)

## HTML Content
<div class="highlight">
    <p>Some HTML content</p>
</div>

**Bold text** and *italic text*.
"""
        
        analysis = self.planner.analyze_content_complexity(complex_content)
        
        # Check that complex elements are detected
        self.assertGreater(analysis['tables'], 0)
        self.assertGreater(analysis['code_blocks'], 0)
        self.assertGreater(analysis['images'], 0)
        self.assertGreater(analysis['links'], 0)
        self.assertGreater(analysis['html_tags'], 0)
        self.assertEqual(analysis['complexity_level'], 'High')
        self.assertGreater(analysis['complexity_score'], 20)

    @patch.object(MigrationPlanner, 'get_wikis')
    @patch.object(MigrationPlanner, 'get_wiki_pages')
    @patch.object(MigrationPlanner, 'get_page_content')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_analyze_wiki_success(self, mock_print, mock_content, mock_pages, mock_wikis):
        """Test successful wiki analysis."""
        # Mock wiki data
        mock_wikis.return_value = [{"id": "wiki1", "name": "Test Wiki"}]
        mock_pages.return_value = [
            {"id": "page1", "path": "/Home"},
            {"id": "page2", "path": "/Docs"}
        ]
        mock_content.side_effect = [
            "# Home\nSimple home page.",
            "# Documentation\n\n| Table | Data |\n|-------|------|\n| A | B |"
        ]

        analysis = self.planner.analyze_wiki()
        
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis['total_pages'], 2)
        self.assertEqual(analysis['pages_with_content'], 2)
        self.assertIn('complexity_distribution', analysis)
        self.assertIn('content_stats', analysis)

    @patch.object(MigrationPlanner, 'get_wikis')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_analyze_wiki_no_wikis(self, mock_print, mock_wikis):
        """Test wiki analysis when no wikis are found."""
        mock_wikis.return_value = []

        analysis = self.planner.analyze_wiki()
        
        self.assertEqual(analysis, {})

    @patch.object(MigrationPlanner, 'get_wikis')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_analyze_wiki_specific_name_not_found(self, mock_print, mock_wikis):
        """Test wiki analysis when specific wiki name is not found."""
        mock_wikis.return_value = [{"id": "wiki1", "name": "Other Wiki"}]

        analysis = self.planner.analyze_wiki("NonExistent Wiki")
        
        self.assertEqual(analysis, {})

    def test_generate_report_empty_analysis(self):
        """Test report generation with empty analysis."""
        report = self.planner.generate_report({})
        
        self.assertIn("No analysis data available", report)

    def test_generate_report_valid_analysis(self):
        """Test report generation with valid analysis data."""
        test_analysis = {
            'wiki_info': {'name': 'Test Wiki'},
            'total_pages': 10,
            'pages_with_content': 8,
            'total_complexity_score': 50,
            'complexity_distribution': {'Low': 5, 'Medium': 2, 'High': 1},
            'content_stats': {
                'total_words': 1000,
                'total_chars': 5000,
                'total_lines': 100,
                'total_headers': 15,
                'total_links': 25,
                'total_images': 5,
                'total_code_blocks': 3,
                'total_tables': 2
            },
            'largest_pages': [
                {'path': '/Large', 'word_count': 500, 'complexity_level': 'Medium'}
            ],
            'most_complex_pages': [
                {'path': '/Complex', 'complexity_score': 30, 'complexity_level': 'High', 'issues': ['5 images']}
            ]
        }

        report = self.planner.generate_report(test_analysis)
        
        self.assertIn('# Azure DevOps Wiki Migration Analysis Report', report)
        self.assertIn('Test Wiki', report)
        self.assertIn('Total Pages**: 10', report)
        self.assertIn('Estimated Migration Time', report)

    def test_calculate_time_estimate(self):
        """Test time estimation calculation."""
        test_analysis = {
            'complexity_distribution': {'Low': 5, 'Medium': 3, 'High': 2},
            'content_stats': {'total_images': 10}
        }

        estimate = self.planner._calculate_time_estimate(test_analysis)
        
        self.assertIsInstance(estimate, str)
        # Should contain either "minutes", "hours", or "days"
        self.assertTrue(any(unit in estimate for unit in ['minutes', 'hours', 'days']))

    def test_get_current_date(self):
        """Test current date formatting."""
        date_str = self.planner._get_current_date()
        
        self.assertIsInstance(date_str, str)
        # Should be in format like "August 07, 2025"
        self.assertRegex(date_str, r'^[A-Z][a-z]+ \d{1,2}, \d{4}$')


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading and validation."""

    @patch.dict(os.environ, {
        'AZURE_DEVOPS_ORGANIZATION': 'test-org',
        'AZURE_DEVOPS_PROJECT': 'test-project',
        'AZURE_DEVOPS_PAT': 'test-pat',
        'AZURE_WIKI_NAME': 'test-wiki'
    })
    @patch('migration.migration_planner.load_dotenv')
    def test_load_config_success(self, mock_load_dotenv):
        """Test successful configuration loading."""
        org, project, pat, wiki_name = load_config()
        
        self.assertEqual(org, 'test-org')
        self.assertEqual(project, 'test-project')
        self.assertEqual(pat, 'test-pat')
        self.assertEqual(wiki_name, 'test-wiki')

    @patch.dict(os.environ, {
        'AZURE_DEVOPS_ORGANIZATION': 'test-org',
        'AZURE_DEVOPS_PROJECT': 'test-project',
        'AZURE_DEVOPS_PAT': 'test-pat'
        # AZURE_WIKI_NAME is optional
    })
    @patch('migration.migration_planner.load_dotenv')
    def test_load_config_optional_wiki_name(self, mock_load_dotenv):
        """Test configuration loading with optional wiki name."""
        org, project, pat, wiki_name = load_config()
        
        self.assertEqual(org, 'test-org')
        self.assertEqual(project, 'test-project')
        self.assertEqual(pat, 'test-pat')
        self.assertIsNone(wiki_name)

    @patch.dict(os.environ, {
        'AZURE_DEVOPS_PROJECT': 'test-project',
        'AZURE_DEVOPS_PAT': 'test-pat'
        # Missing AZURE_DEVOPS_ORGANIZATION
    })
    @patch('migration.migration_planner.load_dotenv')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_load_config_missing_org(self, mock_print, mock_load_dotenv):
        """Test configuration loading with missing organization."""
        with self.assertRaises(SystemExit):
            load_config()

    @patch.dict(os.environ, {
        'AZURE_DEVOPS_ORGANIZATION': '',  # Empty string
        'AZURE_DEVOPS_PROJECT': 'test-project',
        'AZURE_DEVOPS_PAT': 'test-pat'
    })
    @patch('migration.migration_planner.load_dotenv')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_load_config_empty_values(self, mock_print, mock_load_dotenv):
        """Test configuration loading with empty values."""
        with self.assertRaises(SystemExit):
            load_config()


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.planner = MigrationPlanner("test-org", "test-project", "test-pat")

    @patch('requests.Session.get')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_network_error_handling(self, mock_print, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        with self.assertRaises(requests.exceptions.ConnectionError):
            self.planner._make_api_request('GET', 'https://test.com/api', max_retries=1)

    @patch('requests.Session.get')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_rate_limiting_handling(self, mock_print, mock_get):
        """Test handling of rate limiting (HTTP 429)."""
        # First call returns 429, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        rate_limit_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=rate_limit_response)
        
        success_response = Mock()
        success_response.json.return_value = {"success": True}
        success_response.raise_for_status = Mock()
        
        mock_get.side_effect = [rate_limit_response, success_response]

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.planner._make_api_request('GET', 'https://test.com/api')
        
        self.assertEqual(result, {"success": True})

    @patch('requests.Session.get')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_json_decode_error_handling(self, mock_print, mock_get):
        """Test handling of JSON decode errors."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaises(json.JSONDecodeError):
            self.planner._make_api_request('GET', 'https://test.com/api')

    def test_unsupported_http_method(self):
        """Test handling of unsupported HTTP methods."""
        with self.assertRaises(ValueError) as context:
            self.planner._make_api_request('DELETE', 'https://test.com/api')
        self.assertIn("Unsupported HTTP method", str(context.exception))


class TestIntegration(unittest.TestCase):
    """Test integration scenarios and main function."""

    @patch.dict(os.environ, {
        'AZURE_DEVOPS_ORGANIZATION': 'test-org',
        'AZURE_DEVOPS_PROJECT': 'test-project', 
        'AZURE_DEVOPS_PAT': 'test-pat',
        'AZURE_WIKI_NAME': 'test-wiki'
    })
    @patch('os.access')
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(MigrationPlanner, 'generate_report')
    @patch.object(MigrationPlanner, 'analyze_wiki')
    @patch.object(MigrationPlanner, '__init__', return_value=None)  # Mock the constructor
    @patch('migration_planner.load_dotenv')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_main_function_success(self, mock_print, mock_dotenv, mock_init, mock_analyze, mock_generate, mock_file, mock_access):
        """Test successful main function execution."""
        # Mock analysis results
        mock_analyze.return_value = {
            'pages_with_content': 10,
            'complexity_distribution': {'High': 2},
            'content_stats': {'total_images': 5}
        }
        
        # Mock report
        mock_generate.return_value = "Mock report content"
        
        # Mock file system access
        mock_access.return_value = True

        # Main function should work without errors
        main()
        
        # Verify functions were called
        mock_init.assert_called_once()
        mock_analyze.assert_called_once()
        mock_generate.assert_called_once()
        mock_file.assert_called_once()

    @patch('migration.migration_planner.load_config')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_main_function_config_error(self, mock_print, mock_config):
        """Test main function with configuration error."""
        mock_config.side_effect = SystemExit(1)

        with self.assertRaises(SystemExit):
            main()

    @patch('migration.migration_planner.load_config')
    @patch.object(MigrationPlanner, 'analyze_wiki')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_main_function_empty_analysis(self, mock_print, mock_analyze, mock_config):
        """Test main function with empty analysis results."""
        mock_config.return_value = ('test-org', 'test-project', 'test-pat', None)
        mock_analyze.return_value = {}

        with self.assertRaises(SystemExit):
            main()

    @patch('migration.migration_planner.load_config')
    @patch.object(MigrationPlanner, '__init__')
    @patch('builtins.print')  # Suppress print statements that contain Unicode
    def test_main_function_api_error(self, mock_print, mock_init, mock_config):
        """Test main function with API error."""
        mock_config.return_value = ('test-org', 'test-project', 'test-pat', None)
        mock_init.side_effect = requests.RequestException("API Error")

        with self.assertRaises(SystemExit):
            main()


def run_comprehensive_tests():
    """Run all comprehensive tests and provide detailed results."""
    print("Running Comprehensive Tests for migration_planner.py")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestMigrationPlannerImports,
        TestMigrationPlannerInstantiation,
        TestMigrationPlannerMethods,
        TestConfigurationLoading,
        TestErrorHandling,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Create a custom stream that handles encoding issues
    import io
    test_stream = io.StringIO()
    
    # Run tests with detailed results but capture output
    runner = unittest.TextTestRunner(verbosity=2, stream=test_stream)
    result = runner.run(suite)
    
    # Get the output and handle encoding issues
    test_output = test_stream.getvalue()
    # Replace problematic Unicode characters with ASCII equivalents
    safe_output = test_output.encode('ascii', errors='replace').decode('ascii')
    print(safe_output)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Overall result
    if result.wasSuccessful():
        print("\nALL TESTS PASSED! migration_planner.py is working correctly.")
        return True
    else:
        print(f"\nSOME TESTS FAILED. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)