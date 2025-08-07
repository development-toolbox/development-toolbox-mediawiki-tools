#!/usr/bin/env python3
"""
Tests for migration_planner.py - Pre-Migration Analysis Tool for Azure DevOps to MediaWiki Migration.
"""

import os
import sys
import json
import time
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

import pytest
import requests

# Add the migration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'migration'))
from migration_planner import MigrationPlanner, load_config, main


@pytest.mark.unit
class TestMigrationPlanner:
    """Test MigrationPlanner class functionality."""
    
    def test_init_success(self):
        """Test successful MigrationPlanner initialization."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        assert planner.organization == "test-org"
        assert planner.project == "test-project"
        assert planner.pat == "test-pat"
        assert planner.base_url == "https://dev.azure.com/test-org/test-project/_apis"
        assert "Basic" in planner.session.headers['Authorization']
        assert "MediaWiki-Migration-Tool" in planner.session.headers['User-Agent']
    
    def test_init_missing_parameters(self):
        """Test MigrationPlanner initialization with missing parameters."""
        with pytest.raises(ValueError, match="Organization, project, and personal access token are required"):
            MigrationPlanner("", "test-project", "test-pat")
        
        with pytest.raises(ValueError, match="Organization, project, and personal access token are required"):
            MigrationPlanner("test-org", "", "test-pat")
        
        with pytest.raises(ValueError, match="Organization, project, and personal access token are required"):
            MigrationPlanner("test-org", "test-project", "")


@pytest.mark.unit
class TestApiRequests:
    """Test API request handling and retry logic."""
    
    def test_make_api_request_success(self, mock_azure_api_response):
        """Test successful API request."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_azure_api_response['wikis']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = planner._make_api_request('GET', 'https://example.com/api')
            
        assert result == mock_azure_api_response['wikis']
        mock_get.assert_called_once_with('https://example.com/api', timeout=30)
    
    def test_make_api_request_timeout_retry(self, capsys):
        """Test API request with timeout and retry logic."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # First two calls timeout, third succeeds
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timed out"),
                requests.exceptions.Timeout("Timed out"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = planner._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
    
    def test_make_api_request_connection_error_retry(self, capsys):
        """Test API request with connection error and retry logic."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("Connection failed"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = planner._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Connection error, retrying" in captured.out
    
    def test_make_api_request_rate_limit(self, capsys):
        """Test API request with rate limiting."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # First call is rate limited, second succeeds
            rate_limited_response = MagicMock()
            rate_limited_response.status_code = 429
            rate_limited_response.headers = {'Retry-After': '30'}
            rate_limited_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=rate_limited_response)
            
            success_response = MagicMock()
            success_response.json.return_value = {"success": True}
            success_response.raise_for_status.return_value = None
            
            mock_get.side_effect = [rate_limited_response, success_response]
            
            result = planner._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(30)
        
        captured = capsys.readouterr()
        assert "Rate limited, waiting 30s" in captured.out
    
    def test_make_api_request_authentication_error(self, capsys):
        """Test API request with authentication error."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner.session, 'get') as mock_get:
            auth_error_response = MagicMock()
            auth_error_response.status_code = 401
            auth_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=auth_error_response)
            mock_get.return_value = auth_error_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                planner._make_api_request('GET', 'https://example.com/api')
                
        captured = capsys.readouterr()
        assert "Authentication failed" in captured.out
    
    def test_make_api_request_unsupported_method(self):
        """Test API request with unsupported HTTP method."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with pytest.raises(ValueError, match="Unsupported HTTP method: PATCH"):
            planner._make_api_request('PATCH', 'https://example.com/api')


@pytest.mark.unit
class TestWikiOperations:
    """Test wiki-related operations."""
    
    def test_get_wikis_success(self, mock_azure_api_response):
        """Test successful retrieval of wikis."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, '_make_api_request') as mock_request:
            mock_request.return_value = mock_azure_api_response['wikis']
            
            wikis = planner.get_wikis()
            
        assert len(wikis) == 1
        assert wikis[0]['name'] == 'TestWiki'
        assert wikis[0]['id'] == 'wiki-123'
        mock_request.assert_called_once()
    
    def test_get_wikis_api_error(self, capsys):
        """Test get_wikis with API error."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, '_make_api_request') as mock_request:
            mock_request.side_effect = requests.RequestException("API Error")
            
            with pytest.raises(requests.RequestException):
                planner.get_wikis()
                
        captured = capsys.readouterr()
        assert "Failed to retrieve wikis" in captured.out
    
    def test_get_wiki_pages_success(self, mock_azure_api_response):
        """Test successful retrieval of wiki pages."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, '_make_api_request') as mock_request:
            mock_request.return_value = mock_azure_api_response['pages']
            
            pages = planner.get_wiki_pages("wiki-123")
            
        assert len(pages) == 3
        assert pages[0]['path'] == '/Home'
        assert pages[1]['path'] == '/Documentation/Setup'
        mock_request.assert_called_once()
    
    def test_get_page_content_success(self, mock_azure_api_response):
        """Test successful retrieval of page content."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, '_make_api_request') as mock_request:
            mock_request.return_value = {'content': mock_azure_api_response['page_content']['page-1']}
            
            content = planner.get_page_content("wiki-123", "page-1")
            
        assert "Welcome" in content
        assert "home page" in content
        assert "Features" in content
        mock_request.assert_called_once()
    
    def test_get_page_content_error_handling(self, capsys):
        """Test page content retrieval with error handling."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, '_make_api_request') as mock_request:
            mock_request.side_effect = requests.RequestException("Page not found")
            
            content = planner.get_page_content("wiki-123", "invalid-page")
            
        assert content == ''
        captured = capsys.readouterr()
        assert "Failed to retrieve content" in captured.out


@pytest.mark.unit
class TestContentComplexityAnalysis:
    """Test content complexity analysis functionality."""
    
    def test_analyze_content_complexity_simple(self, sample_markdown_content):
        """Test complexity analysis for simple content."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        simple_content = "# Hello World\n\nThis is a simple page with **bold** text."
        
        analysis = planner.analyze_content_complexity(simple_content)
        
        assert analysis['word_count'] == 11
        assert analysis['headers'] == 1
        assert analysis['bold_text'] == 1
        assert analysis['complexity_level'] == 'Low'
        assert analysis['complexity_score'] < 10
    
    def test_analyze_content_complexity_medium(self, sample_markdown_content):
        """Test complexity analysis for medium complexity content."""
        medium_content = """# Documentation
        
## Setup

Here's how to [install](setup.html) the software:

```bash
npm install
```

### Features

- Feature 1
- Feature 2
- Feature 3

| Name | Value |
|------|-------|
| Item | 123   |
"""
        
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        analysis = planner.analyze_content_complexity(medium_content)
        
        assert analysis['complexity_level'] == 'Medium'
        assert 10 <= analysis['complexity_score'] < 25
        assert analysis['headers'] >= 2
        assert analysis['links'] >= 1
        assert analysis['code_blocks'] >= 1
    
    def test_analyze_content_complexity_high(self):
        """Test complexity analysis for high complexity content."""
        complex_content = """# Complex Page

## Multiple Tables

| A | B | C |
|---|---|---|
| 1 | 2 | 3 |

| X | Y | Z |
|---|---|---|
| 4 | 5 | 6 |

| P | Q | R |
|---|---|---|
| 7 | 8 | 9 |

## Many Code Blocks

```python
code block 1
```

```javascript  
code block 2
```

```html
code block 3
```

## Images

![Image 1](img1.png)
![Image 2](img2.png)

## HTML Tags

<div>Custom HTML</div>
<span>More HTML</span>

## Links

[Link 1](url1) [Link 2](url2) [Link 3](url3)
"""
        
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        analysis = planner.analyze_content_complexity(complex_content)
        
        assert analysis['complexity_level'] == 'High'
        assert analysis['complexity_score'] >= 25
        assert analysis['tables'] >= 3
        assert analysis['code_blocks'] >= 3
        assert analysis['images'] >= 2
        assert analysis['html_tags'] >= 2
    
    def test_analyze_content_complexity_empty(self):
        """Test complexity analysis for empty content."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        analysis = planner.analyze_content_complexity("")
        
        assert analysis['word_count'] == 0
        assert analysis['complexity_score'] == 0
        assert analysis['complexity_level'] == 'Low'


@pytest.mark.unit
class TestWikiAnalysis:
    """Test comprehensive wiki analysis functionality."""
    
    def test_analyze_wiki_success(self, mock_azure_api_response, complex_wiki_structure, capsys):
        """Test successful wiki analysis."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis, \
             patch.object(planner, 'get_wiki_pages') as mock_get_pages, \
             patch.object(planner, 'get_page_content') as mock_get_content:
            
            mock_get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_get_pages.return_value = [
                {'id': page['id'], 'path': page['path']} 
                for page in complex_wiki_structure['pages']
            ]
            
            # Set up content responses
            def content_side_effect(wiki_id, page_id):
                for page in complex_wiki_structure['pages']:
                    if page['id'] == page_id:
                        return page['content']
                return ''
            
            mock_get_content.side_effect = content_side_effect
            
            analysis = planner.analyze_wiki("TestWiki")
            
        assert analysis['wiki_info']['name'] == 'TestWiki'
        assert analysis['total_pages'] == 3
        assert analysis['pages_with_content'] == 3
        assert 'complexity_distribution' in analysis
        assert 'content_stats' in analysis
        assert len(analysis['page_details']) == 3
        
        captured = capsys.readouterr()
        assert "Starting wiki analysis" in captured.out
        assert "Analyzing wiki: TestWiki" in captured.out
    
    def test_analyze_wiki_specific_wiki_not_found(self, mock_azure_api_response, capsys):
        """Test wiki analysis when specified wiki is not found."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis:
            mock_get_wikis.return_value = mock_azure_api_response['wikis']['value']
            
            analysis = planner.analyze_wiki("NonExistentWiki")
            
        assert analysis == {}
        captured = capsys.readouterr()
        assert "Wiki 'NonExistentWiki' not found" in captured.out
        assert "Available wikis: TestWiki" in captured.out
    
    def test_analyze_wiki_no_wikis_found(self, capsys):
        """Test wiki analysis when no wikis are found."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis:
            mock_get_wikis.return_value = []
            
            analysis = planner.analyze_wiki()
            
        assert analysis == {}
        captured = capsys.readouterr()
        assert "No wikis found" in captured.out
    
    def test_analyze_wiki_no_pages_found(self, mock_azure_api_response, capsys):
        """Test wiki analysis when no pages are found."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis, \
             patch.object(planner, 'get_wiki_pages') as mock_get_pages:
            
            mock_get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_get_pages.return_value = []
            
            analysis = planner.analyze_wiki()
            
        assert analysis == {}
        captured = capsys.readouterr()
        assert "No pages found in wiki" in captured.out
    
    def test_analyze_wiki_progress_tracking(self, mock_azure_api_response, capsys):
        """Test wiki analysis with progress tracking for large wikis."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        # Create 15 pages to trigger progress display
        large_page_list = [
            {'id': f'page-{i}', 'path': f'/Page{i}'}
            for i in range(1, 16)
        ]
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis, \
             patch.object(planner, 'get_wiki_pages') as mock_get_pages, \
             patch.object(planner, 'get_page_content') as mock_get_content:
            
            mock_get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_get_pages.return_value = large_page_list
            mock_get_content.return_value = "# Test Content\n\nSample page."
            
            analysis = planner.analyze_wiki()
            
        captured = capsys.readouterr()
        assert "Analyzing page 10/15" in captured.out


@pytest.mark.unit
class TestReportGeneration:
    """Test analysis report generation."""
    
    def test_generate_report_success(self):
        """Test successful report generation."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        # Mock analysis data
        analysis_data = {
            'wiki_info': {'name': 'TestWiki'},
            'total_pages': 10,
            'pages_with_content': 8,
            'total_complexity_score': 100,
            'complexity_distribution': {'Low': 5, 'Medium': 2, 'High': 1},
            'content_stats': {
                'total_words': 5000,
                'total_chars': 25000,
                'total_lines': 800,
                'total_headers': 50,
                'total_links': 30,
                'total_images': 5,
                'total_code_blocks': 15,
                'total_tables': 8
            },
            'largest_pages': [
                {'path': '/Documentation', 'word_count': 1200, 'complexity_level': 'High'}
            ],
            'most_complex_pages': [
                {
                    'path': '/API/Advanced',
                    'complexity_score': 45,
                    'complexity_level': 'High',
                    'issues': ['3 images (need manual handling)', '5 tables (complex conversion)']
                }
            ]
        }
        
        report = planner.generate_report(analysis_data)
        
        assert "# Azure DevOps Wiki Migration Analysis Report" in report
        assert "TestWiki" in report
        assert "Total Pages**: 10" in report
        assert "Pages with Content**: 8" in report
        assert "Low Complexity**: 5" in report
        assert "Medium Complexity**: 2" in report  
        assert "High Complexity**: 1" in report
        assert "5,000" in report  # Total words formatted
        assert "5 images" in report
        assert "15 code blocks" in report
        assert "/Documentation" in report
        assert "/API/Advanced" in report
        assert "3 images (need manual handling)" in report
    
    def test_generate_report_empty_analysis(self):
        """Test report generation with empty analysis."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        report = planner.generate_report({})
        
        assert "No analysis data available" in report
    
    def test_generate_report_no_content_pages(self):
        """Test report generation when no pages have content."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        analysis_data = {
            'wiki_info': {'name': 'EmptyWiki'},
            'total_pages': 5,
            'pages_with_content': 0
        }
        
        report = planner.generate_report(analysis_data)
        
        assert "No pages with content found" in report


@pytest.mark.unit
class TestTimeEstimation:
    """Test migration time estimation functionality."""
    
    def test_calculate_time_estimate_minutes(self):
        """Test time estimation for small migrations (minutes)."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        analysis = {
            'complexity_distribution': {'Low': 5, 'Medium': 0, 'High': 0},
            'content_stats': {'total_images': 0}
        }
        
        estimate = planner._calculate_time_estimate(analysis)
        
        assert estimate == "15 minutes"  # 5 * 3 minutes
    
    def test_calculate_time_estimate_hours(self):
        """Test time estimation for medium migrations (hours)."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        analysis = {
            'complexity_distribution': {'Low': 10, 'Medium': 5, 'High': 2},
            'content_stats': {'total_images': 10}
        }
        
        estimate = planner._calculate_time_estimate(analysis)
        
        # 10*3 + 5*12 + 2*45 + 10*7 = 30 + 60 + 90 + 70 = 250 minutes = 4.2 hours
        assert "4.2 hours" in estimate
    
    def test_calculate_time_estimate_days(self):
        """Test time estimation for large migrations (work days)."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        analysis = {
            'complexity_distribution': {'Low': 50, 'Medium': 30, 'High': 20},
            'content_stats': {'total_images': 50}
        }
        
        estimate = planner._calculate_time_estimate(analysis)
        
        # 50*3 + 30*12 + 20*45 + 50*7 = 150 + 360 + 900 + 350 = 1760 minutes
        # 1760/480 = 3.67 work days
        assert "work days" in estimate
        assert "3." in estimate  # Should be around 3.7 days


@pytest.mark.unit
class TestConfigurationLoading:
    """Test configuration loading functionality."""
    
    def test_load_config_success(self, mock_env_vars):
        """Test successful configuration loading."""
        with patch.dict(os.environ, mock_env_vars):
            org, project, pat, wiki_name = load_config()
            
        assert org == "test-org"
        assert project == "test-project"
        assert pat == "test-pat-token-123"
        assert wiki_name == "TestWiki"
    
    def test_load_config_missing_required(self, capsys):
        """Test configuration loading with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
        assert "AZURE_DEVOPS_ORGANIZATION" in captured.out
    
    def test_load_config_partial_missing(self, capsys):
        """Test configuration loading with some missing variables."""
        partial_env = {
            'AZURE_DEVOPS_ORGANIZATION': 'test-org',
            'AZURE_DEVOPS_PROJECT': 'test-project'
            # Missing PAT
        }
        
        with patch.dict(os.environ, partial_env, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "AZURE_DEVOPS_PAT" in captured.out


@pytest.mark.integration
class TestMainFunction:
    """Test main function integration."""
    
    def test_main_success_flow(self, mock_env_vars, mock_azure_api_response, temp_directory, monkeypatch):
        """Test successful main function execution."""
        monkeypatch.chdir(temp_directory)
        
        # Mock the entire workflow
        with patch.dict(os.environ, mock_env_vars), \
             patch('migration_planner.MigrationPlanner') as mock_planner_class, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.access', return_value=True):
            
            mock_planner = mock_planner_class.return_value
            mock_planner.analyze_wiki.return_value = {
                'wiki_info': {'name': 'TestWiki'},
                'pages_with_content': 10,
                'complexity_distribution': {'High': 2},
                'content_stats': {'total_images': 5}
            }
            mock_planner.generate_report.return_value = "Test Report Content"
            
            main()
            
        # Verify planner was created and methods called
        mock_planner_class.assert_called_once_with("test-org", "test-project", "test-pat-token-123")
        mock_planner.analyze_wiki.assert_called_once_with("TestWiki")
        mock_planner.generate_report.assert_called_once()
        
        # Verify file was written
        mock_file.assert_called_once_with("migration_analysis_report.md", "w", encoding='utf-8')
    
    def test_main_missing_dependencies(self, capsys):
        """Test main function with missing dependencies."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'requests'")):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Required package not installed" in captured.out
    
    def test_main_configuration_error(self, capsys):
        """Test main function with configuration error."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('migration_planner.load_config', side_effect=SystemExit(1)):
            
            with pytest.raises(SystemExit):
                main()
    
    def test_main_analysis_failure(self, mock_env_vars, capsys):
        """Test main function when analysis fails."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('migration_planner.MigrationPlanner') as mock_planner_class:
            
            mock_planner = mock_planner_class.return_value
            mock_planner.analyze_wiki.return_value = {}  # Empty analysis
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "No analysis results generated" in captured.out
    
    def test_main_file_write_permission_error(self, mock_env_vars, temp_directory, monkeypatch, capsys):
        """Test main function with file write permission error."""
        monkeypatch.chdir(temp_directory)
        
        with patch.dict(os.environ, mock_env_vars), \
             patch('migration_planner.MigrationPlanner') as mock_planner_class, \
             patch('os.access', return_value=False):  # No write permission
            
            mock_planner = mock_planner_class.return_value
            mock_planner.analyze_wiki.return_value = {'pages_with_content': 1}
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "No write permission" in captured.out
    
    def test_main_api_error(self, mock_env_vars, capsys):
        """Test main function with API error."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('migration_planner.MigrationPlanner', side_effect=requests.RequestException("API Error")):
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Azure DevOps API error" in captured.out


@pytest.mark.api
class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_analyze_wiki_with_page_content_errors(self, mock_azure_api_response, capsys):
        """Test wiki analysis when some pages fail to load content."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis, \
             patch.object(planner, 'get_wiki_pages') as mock_get_pages, \
             patch.object(planner, 'get_page_content') as mock_get_content:
            
            mock_get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_get_pages.return_value = mock_azure_api_response['pages']['value']
            
            def content_side_effect(wiki_id, page_id):
                if page_id == 'page-2':
                    raise Exception("Failed to load page")
                return "# Test content"
            
            mock_get_content.side_effect = content_side_effect
            
            analysis = planner.analyze_wiki()
            
        assert analysis['pages_with_content'] == 2  # Only 2 out of 3 succeeded
        captured = capsys.readouterr()
        assert "Error getting content" in captured.out
    
    def test_get_current_date(self):
        """Test current date formatting."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        with patch('migration_planner.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "August 07, 2025"
            
            date_str = planner._get_current_date()
            
        assert date_str == "August 07, 2025"
        mock_datetime.now.return_value.strftime.assert_called_once_with("%B %d, %Y")
    
    def test_analyze_wiki_large_pages_tracking(self, mock_azure_api_response):
        """Test that large pages are properly tracked."""
        planner = MigrationPlanner("test-org", "test-project", "test-pat")
        
        # Create content that results in >500 words
        large_content = "word " * 600  # 600 words
        
        with patch.object(planner, 'get_wikis') as mock_get_wikis, \
             patch.object(planner, 'get_wiki_pages') as mock_get_pages, \
             patch.object(planner, 'get_page_content') as mock_get_content:
            
            mock_get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_get_pages.return_value = [mock_azure_api_response['pages']['value'][0]]  # Just one page
            mock_get_content.return_value = large_content
            
            analysis = planner.analyze_wiki()
            
        assert len(analysis['largest_pages']) == 1
        assert analysis['largest_pages'][0]['word_count'] == 600
        assert analysis['largest_pages'][0]['path'] == '/Home'


if __name__ == '__main__':
    pytest.main([__file__])