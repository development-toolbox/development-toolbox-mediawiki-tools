#!/usr/bin/env python3
"""
Tests for validation_tool.py - Post-Migration Validation Tool for MediaWiki.
"""

import os
import sys
import json
import time
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from typing import List, Dict

import pytest
import requests

# Add the migration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'migration'))
from validation_tool import MigrationValidator, load_config, main


@pytest.mark.unit
class TestMigrationValidator:
    """Test MigrationValidator class functionality."""
    
    def test_init_success(self):
        """Test successful MigrationValidator initialization."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        assert validator.mediawiki_url == "http://localhost:8080"
        assert validator.username == "testuser"
        assert validator.password == "testpass"
        assert validator.api_url == "http://localhost:8080/api.php"
        assert not validator._logged_in
    
    def test_init_url_normalization(self):
        """Test that URLs are properly normalized."""
        validator = MigrationValidator("http://localhost:8080/", "testuser", "testpass")
        
        assert validator.mediawiki_url == "http://localhost:8080"
        assert validator.api_url == "http://localhost:8080/api.php"


@pytest.mark.unit
class TestApiRequests:
    """Test MediaWiki API request handling."""
    
    def test_make_request_success(self, mock_mediawiki_api_response):
        """Test successful MediaWiki API request."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mediawiki_api_response['login_token']
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = validator._make_request("POST", action="query", meta="tokens")
            
        assert result == mock_mediawiki_api_response['login_token']
        mock_post.assert_called_once()
    
    def test_make_request_get_method(self, mock_mediawiki_api_response):
        """Test successful GET API request."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mediawiki_api_response['all_pages']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = validator._make_request("GET", action="query", list="allpages")
            
        assert result == mock_mediawiki_api_response['all_pages']
        mock_get.assert_called_once()
    
    def test_make_request_timeout_retry(self, capsys):
        """Test API request with timeout and retry logic."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            mock_post.side_effect = [
                requests.exceptions.Timeout("Timed out"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = validator._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
    
    def test_make_request_connection_error_retry(self, capsys):
        """Test API request with connection error and retry."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            mock_post.side_effect = [
                requests.exceptions.ConnectionError("Connection failed"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = validator._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Connection error, retrying" in captured.out
    
    def test_make_request_server_error_retry(self, capsys):
        """Test API request with server error and retry."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            # First request: 500 error, second request: success
            error_response = MagicMock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            success_response = MagicMock()
            success_response.json.return_value = {"success": True}
            success_response.raise_for_status.return_value = None
            
            mock_post.side_effect = [error_response, success_response]
            
            result = validator._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(5)  # Server error wait time
        
        captured = capsys.readouterr()
        assert "Server error, retrying" in captured.out
    
    def test_make_request_json_decode_error(self, capsys):
        """Test API request with JSON decode error."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(json.JSONDecodeError):
                validator._make_request("POST", action="test")
                
        captured = capsys.readouterr()
        assert "Invalid JSON response from MediaWiki" in captured.out
        assert "MediaWiki might be returning HTML error page" in captured.out


@pytest.mark.unit
class TestLogin:
    """Test MediaWiki login functionality."""
    
    def test_login_success(self, mock_mediawiki_api_response, capsys):
        """Test successful MediaWiki login."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, '_make_request') as mock_request:
            mock_request.side_effect = [
                mock_mediawiki_api_response['login_token'],
                mock_mediawiki_api_response['login_success']
            ]
            
            validator.login()
            
        assert validator._logged_in is True
        assert mock_request.call_count == 2
        
        captured = capsys.readouterr()
        assert "Successfully logged into MediaWiki" in captured.out
    
    def test_login_already_logged_in(self):
        """Test login when already logged in."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        validator._logged_in = True
        
        with patch.object(validator, '_make_request') as mock_request:
            validator.login()
            
        mock_request.assert_not_called()
    
    def test_login_no_token(self):
        """Test login failure due to missing token."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, '_make_request') as mock_request:
            mock_request.return_value = {"query": {"tokens": {}}}  # No login token
            
            with pytest.raises(Exception, match="Failed to get login token"):
                validator.login()
    
    def test_login_failure(self, mock_mediawiki_api_response):
        """Test login failure with wrong credentials."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        failed_login_response = {
            'login': {
                'result': 'Failed'
            }
        }
        
        with patch.object(validator, '_make_request') as mock_request:
            mock_request.side_effect = [
                mock_mediawiki_api_response['login_token'],
                failed_login_response
            ]
            
            with pytest.raises(Exception, match="MediaWiki login failed: Failed"):
                validator.login()
                
        assert validator._logged_in is False


@pytest.mark.unit
class TestPageRetrieval:
    """Test page retrieval functionality."""
    
    def test_get_all_pages_success(self, mock_mediawiki_api_response):
        """Test successful retrieval of all pages."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'login'), \
             patch.object(validator, '_make_request') as mock_request:
            
            # Mock paginated response
            mock_request.side_effect = [
                {
                    'query': {
                        'allpages': mock_mediawiki_api_response['all_pages']['query']['allpages']
                    }
                    # No 'continue' key, so pagination stops
                }
            ]
            
            pages = validator.get_all_pages()
            
        assert len(pages) == 3
        assert pages[0]['title'] == 'Home'
        assert pages[1]['title'] == 'Documentation Setup'
        assert pages[2]['title'] == 'API Reference'
    
    def test_get_all_pages_with_pagination(self):
        """Test page retrieval with pagination."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'login'), \
             patch.object(validator, '_make_request') as mock_request:
            
            # Mock paginated responses
            mock_request.side_effect = [
                {
                    'query': {
                        'allpages': [
                            {'pageid': 1, 'title': 'Page1'},
                            {'pageid': 2, 'title': 'Page2'}
                        ]
                    },
                    'continue': {'apcontinue': 'Page3'}
                },
                {
                    'query': {
                        'allpages': [
                            {'pageid': 3, 'title': 'Page3'},
                            {'pageid': 4, 'title': 'Page4'}
                        ]
                    }
                    # No continue, pagination ends
                }
            ]
            
            pages = validator.get_all_pages()
            
        assert len(pages) == 4
        assert mock_request.call_count == 2
        
        # Verify pagination parameters
        second_call_args = mock_request.call_args_list[1][1]
        assert second_call_args['apcontinue'] == 'Page3'
    
    def test_get_page_content_success(self, mock_mediawiki_api_response):
        """Test successful page content retrieval."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'login'), \
             patch.object(validator, '_make_request') as mock_request:
            
            mock_request.return_value = mock_mediawiki_api_response['page_content']
            
            content = validator.get_page_content("Home")
            
        expected_content = mock_mediawiki_api_response['page_content']['query']['pages']['1']['revisions'][0]['*']
        assert content == expected_content
        assert "Welcome" in content
    
    def test_get_page_content_missing_page(self):
        """Test page content retrieval for missing page."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'login'), \
             patch.object(validator, '_make_request') as mock_request:
            
            # Mock response for non-existent page
            mock_request.return_value = {
                'query': {
                    'pages': {
                        '-1': {
                            'missing': True,
                            'title': 'NonExistentPage'
                        }
                    }
                }
            }
            
            content = validator.get_page_content("NonExistentPage")
            
        assert content == ""


@pytest.mark.unit
class TestPageAccessibility:
    """Test page accessibility checking."""
    
    def test_check_page_accessibility_success(self):
        """Test successful page accessibility check."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_page_content') as mock_get_content, \
             patch('requests.get') as mock_web_request:
            
            mock_get_content.return_value = "Page content here"
            mock_web_request.return_value = MagicMock(status_code=200)
            
            result = validator.check_page_accessibility("Test Page")
            
        assert result['api_accessible'] is True
        assert result['web_accessible'] is True
        assert result['content_length'] == 18
        assert result['status_code'] == 200
    
    def test_check_page_accessibility_api_failure(self):
        """Test page accessibility check with API failure."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_page_content') as mock_get_content, \
             patch('requests.get') as mock_web_request:
            
            mock_get_content.return_value = ""  # Empty content
            mock_web_request.return_value = MagicMock(status_code=200)
            
            result = validator.check_page_accessibility("Empty Page")
            
        assert result['api_accessible'] is False
        assert result['web_accessible'] is True
        assert result['content_length'] == 0
        assert result['status_code'] == 200
    
    def test_check_page_accessibility_web_failure(self):
        """Test page accessibility check with web failure."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_page_content') as mock_get_content, \
             patch('requests.get') as mock_web_request:
            
            mock_get_content.return_value = "Content"
            mock_web_request.return_value = MagicMock(status_code=404)
            
            result = validator.check_page_accessibility("Missing Web Page")
            
        assert result['api_accessible'] is True
        assert result['web_accessible'] is False
        assert result['content_length'] == 7
        assert result['status_code'] == 404
    
    def test_check_page_accessibility_exception_handling(self):
        """Test page accessibility check with exception."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_page_content') as mock_get_content:
            mock_get_content.side_effect = Exception("API Error")
            
            result = validator.check_page_accessibility("Error Page")
            
        assert result['api_accessible'] is False
        assert result['web_accessible'] is False
        assert result['content_length'] == 0
        assert 'error' in result
        assert result['error'] == "API Error"
        assert result['status_code'] == 0


@pytest.mark.unit
class TestContentQualityAnalysis:
    """Test content quality analysis functionality."""
    
    def test_analyze_content_quality_excellent(self, sample_mediawiki_content):
        """Test content quality analysis for excellent content."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        analysis = validator.analyze_content_quality("Test Page", sample_mediawiki_content)
        
        assert analysis['title'] == "Test Page"
        assert analysis['length'] == len(sample_mediawiki_content)
        assert analysis['word_count'] > 0
        assert analysis['quality_level'] == 'Excellent'
        assert analysis['quality_score'] >= 90
        assert len(analysis['issues']) == 0
    
    def test_analyze_content_quality_with_markdown_issues(self):
        """Test content quality analysis with unconverted markdown."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        # Content with unconverted markdown
        problematic_content = """= Title =

This has **bold** and *italic* markdown that wasn't converted.

```python
def test():
    pass
```

[Link](https://example.com)

# Header that should be MediaWiki format
"""
        
        analysis = validator.analyze_content_quality("Problematic Page", problematic_content)
        
        assert analysis['quality_level'] in ['Poor', 'Fair']
        assert analysis['quality_score'] < 90
        assert len(analysis['issues']) > 0
        
        # Check for specific markdown issues
        issue_texts = ' '.join(analysis['issues'])
        assert 'Bold markdown not converted' in issue_texts
        assert 'Italic markdown not converted' in issue_texts
        assert 'Code block markdown not converted' in issue_texts
        assert 'Link markdown not converted' in issue_texts
        assert 'Header markdown not converted' in issue_texts
    
    def test_analyze_content_quality_with_images(self):
        """Test content quality analysis with image issues."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        content_with_images = """= Page =

This has markdown images that weren't converted:

![Image 1](image1.png)
![Image 2](image2.jpg)

Regular content here.
"""
        
        analysis = validator.analyze_content_quality("Image Page", content_with_images)
        
        assert len(analysis['issues']) > 0
        assert any('markdown image syntax' in issue for issue in analysis['issues'])
    
    def test_analyze_content_quality_with_html_tags(self):
        """Test content quality analysis with HTML tags."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        content_with_html = """= Page =

This page has HTML tags:

<div class="custom">
<p>Some content</p>
<span>More content</span>
</div>

Regular content.
"""
        
        analysis = validator.analyze_content_quality("HTML Page", content_with_html)
        
        assert 'html_tags' in analysis
        assert analysis['html_tags'] == 4  # div, p, span, /div (closing tags count)
        assert len(analysis['warnings']) > 0
        assert any('HTML tags' in warning for warning in analysis['warnings'])
    
    def test_analyze_content_quality_short_content(self):
        """Test content quality analysis with very short content."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        short_content = "= Short =\n\nBrief."
        
        analysis = validator.analyze_content_quality("Short Page", short_content)
        
        assert len(analysis['warnings']) > 0
        assert any('Very short content' in warning for warning in analysis['warnings'])
        assert analysis['quality_score'] < 100  # Should be penalized
    
    def test_analyze_content_quality_internal_links(self):
        """Test content quality analysis with internal links."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        content_with_links = """= Page =

This page has internal links:

[[Main Page|Link to main]]
[[Documentation]]
[[Category:Test]]

Regular content.
"""
        
        analysis = validator.analyze_content_quality("Links Page", content_with_links)
        
        assert 'internal_links' in analysis
        assert analysis['internal_links'] == 3


@pytest.mark.unit
class TestInternalLinkValidation:
    """Test internal link validation functionality."""
    
    def test_validate_internal_links_success(self, capsys):
        """Test successful internal link validation."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        # Mock pages and their content
        pages = [
            {'title': 'Home'},
            {'title': 'Documentation'},
            {'title': 'API Reference'}
        ]
        
        page_contents = {
            'Home': '= Home =\n\nWelcome to [[Documentation]] and [[API Reference]].',
            'Documentation': '= Documentation =\n\nSee [[Home]] for overview.',
            'API Reference': '= API =\n\nRefer to [[Home]] page.'
        }
        
        with patch.object(validator, 'get_page_content') as mock_get_content:
            mock_get_content.side_effect = lambda title: page_contents.get(title, '')
            
            result = validator.validate_internal_links(pages, sample_size=3)
            
        assert result['total_links_checked'] == 4  # 2 + 1 + 1
        assert result['valid_links'] == 4
        assert result['broken_links'] == 0
        assert len(result['broken_link_details']) == 0
        assert len(result['pages_with_broken_links']) == 0
        
        captured = capsys.readouterr()
        assert "Validating internal links" in captured.out
    
    def test_validate_internal_links_with_broken_links(self, capsys):
        """Test internal link validation with broken links."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        pages = [
            {'title': 'Home'},
            {'title': 'Documentation'}
        ]
        
        page_contents = {
            'Home': '= Home =\n\nLinks: [[Documentation]], [[Missing Page]], [[Another Missing]].',
            'Documentation': '= Docs =\n\nSee [[Home]] and [[Non Existent]].'
        }
        
        with patch.object(validator, 'get_page_content') as mock_get_content:
            mock_get_content.side_effect = lambda title: page_contents.get(title, '')
            
            result = validator.validate_internal_links(pages, sample_size=2)
            
        assert result['total_links_checked'] == 5  # 3 + 2
        assert result['valid_links'] == 2  # Documentation->Home, Home->Documentation
        assert result['broken_links'] == 3  # Missing Page, Another Missing, Non Existent
        assert len(result['broken_link_details']) == 3
        assert len(result['pages_with_broken_links']) == 2
        
        # Check broken link details
        assert 'Home -> Missing Page' in result['broken_link_details']
        assert 'Home -> Another Missing' in result['broken_link_details']
        assert 'Documentation -> Non Existent' in result['broken_link_details']
    
    def test_validate_internal_links_with_pipe_syntax(self):
        """Test internal link validation with MediaWiki pipe syntax."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        pages = [
            {'title': 'Main Page'},
            {'title': 'User Guide'}
        ]
        
        page_contents = {
            'Main Page': '= Main =\n\nSee the [[User Guide|guide]] for details.',
        }
        
        with patch.object(validator, 'get_page_content') as mock_get_content:
            mock_get_content.side_effect = lambda title: page_contents.get(title, '')
            
            result = validator.validate_internal_links(pages, sample_size=1)
            
        assert result['total_links_checked'] == 1
        assert result['valid_links'] == 1
        assert result['broken_links'] == 0
    
    def test_validate_internal_links_with_errors(self, capsys):
        """Test internal link validation when page content retrieval fails."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        pages = [
            {'title': 'Error Page'},
            {'title': 'Good Page'}
        ]
        
        def content_side_effect(title):
            if title == 'Error Page':
                raise Exception("Failed to retrieve content")
            return '= Good =\n\nContent here.'
        
        with patch.object(validator, 'get_page_content') as mock_get_content:
            mock_get_content.side_effect = content_side_effect
            
            result = validator.validate_internal_links(pages, sample_size=2)
            
        # Should continue with other pages despite errors
        assert result['total_links_checked'] == 0  # No links in good page
        
        captured = capsys.readouterr()
        assert "Error checking links in Error Page" in captured.out


@pytest.mark.integration
class TestComprehensiveValidation:
    """Test comprehensive migration validation."""
    
    def test_run_comprehensive_validation_success(self, mock_mediawiki_api_response, sample_mediawiki_content, capsys):
        """Test successful comprehensive validation."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_all_pages') as mock_get_pages, \
             patch.object(validator, 'check_page_accessibility') as mock_check_access, \
             patch.object(validator, 'get_page_content') as mock_get_content, \
             patch.object(validator, 'validate_internal_links') as mock_validate_links, \
             patch('time.strftime', return_value='2025-08-07 10:00:00'):
            
            # Mock 3 pages
            mock_pages = [
                {'title': 'Home'},
                {'title': 'Documentation'},
                {'title': 'API Reference'}
            ]
            mock_get_pages.return_value = mock_pages
            
            # All pages accessible
            mock_check_access.return_value = {
                'api_accessible': True,
                'web_accessible': True,
                'content_length': 100
            }
            
            # Good quality content
            mock_get_content.return_value = sample_mediawiki_content
            
            # No broken links
            mock_validate_links.return_value = {
                'total_links_checked': 5,
                'valid_links': 5,
                'broken_links': 0,
                'broken_link_details': [],
                'pages_with_broken_links': []
            }
            
            result = validator.run_comprehensive_validation()
            
        assert result['timestamp'] == '2025-08-07 10:00:00'
        assert result['pages_found'] == 3
        assert result['pages_accessible'] == 3
        assert result['pages_with_issues'] == 0
        assert result['quality_distribution']['Excellent'] == 3
        assert len(result['page_details']) == 3
        assert result['summary']['accessibility_success_rate'] == 100.0
        assert result['summary']['quality_success_rate'] == 100.0
        assert len(result['recommendations']) > 0
        
        captured = capsys.readouterr()
        assert "Starting comprehensive migration validation" in captured.out
        assert "Found 3 pages to validate" in captured.out
    
    def test_run_comprehensive_validation_with_issues(self, capsys):
        """Test comprehensive validation with various issues."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_all_pages') as mock_get_pages, \
             patch.object(validator, 'check_page_accessibility') as mock_check_access, \
             patch.object(validator, 'get_page_content') as mock_get_content, \
             patch.object(validator, 'validate_internal_links') as mock_validate_links:
            
            # Mock 4 pages
            mock_pages = [
                {'title': 'Good Page'},
                {'title': 'Poor Page'},
                {'title': 'Inaccessible Page'},
                {'title': 'Another Good Page'}
            ]
            mock_get_pages.return_value = mock_pages
            
            # Mixed accessibility
            def access_side_effect(title):
                if title == 'Inaccessible Page':
                    return {
                        'api_accessible': False,
                        'web_accessible': False,
                        'content_length': 0,
                        'error': 'Page not found'
                    }
                return {
                    'api_accessible': True,
                    'web_accessible': True,
                    'content_length': 100
                }
            
            mock_check_access.side_effect = access_side_effect
            
            # Mixed content quality
            def content_side_effect(title):
                if title == 'Poor Page':
                    return '= Poor =\n\n**Unconverted** markdown and ![image](img.png)'
                return '= Good =\n\nGood MediaWiki content with [[valid links]].'
            
            mock_get_content.side_effect = content_side_effect
            
            # Some broken links
            mock_validate_links.return_value = {
                'total_links_checked': 10,
                'valid_links': 7,
                'broken_links': 3,
                'broken_link_details': ['Good Page -> Missing', 'Poor Page -> Another Missing', 'Another Good Page -> Gone'],
                'pages_with_broken_links': [
                    {'page': 'Good Page', 'broken_links': ['Missing']},
                    {'page': 'Poor Page', 'broken_links': ['Another Missing']},
                    {'page': 'Another Good Page', 'broken_links': ['Gone']}
                ]
            }
            
            result = validator.run_comprehensive_validation()
            
        assert result['pages_found'] == 4
        assert result['pages_accessible'] == 3  # One inaccessible
        assert result['pages_with_issues'] == 1  # Poor page has issues
        assert result['quality_distribution']['Poor'] == 1
        assert result['quality_distribution']['Excellent'] == 2  # Two good pages
        
        # Check summary calculations
        summary = result['summary']
        assert summary['accessibility_success_rate'] == 75.0  # 3/4 * 100
        assert summary['quality_success_rate'] == 66.7  # (3-1)/3 * 100, rounded
        assert summary['pages_with_issues'] == 1
        assert summary['link_validation']['broken_links'] == 3
        
        # Check recommendations
        recommendations = result['recommendations']
        assert any('Fix 1 inaccessible pages' in rec for rec in recommendations)
        assert any('Review 1 pages with content issues' in rec for rec in recommendations)
        assert any('Fix 3 broken internal links' in rec for rec in recommendations)
    
    def test_run_comprehensive_validation_with_expected_pages(self, mock_mediawiki_api_response, capsys):
        """Test comprehensive validation with expected pages list."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_all_pages') as mock_get_pages, \
             patch.object(validator, 'check_page_accessibility') as mock_check_access, \
             patch.object(validator, 'get_page_content') as mock_get_content, \
             patch.object(validator, 'validate_internal_links') as mock_validate_links:
            
            # Only 2 pages found
            mock_get_pages.return_value = [
                {'title': 'Home'},
                {'title': 'Documentation'}
            ]
            
            # But we expected 4 pages
            expected_pages = ['Home', 'Documentation', 'Missing Page 1', 'Missing Page 2']
            
            mock_check_access.return_value = {
                'api_accessible': True,
                'web_accessible': True,
                'content_length': 100
            }
            mock_get_content.return_value = '= Page =\n\nContent.'
            mock_validate_links.return_value = {
                'total_links_checked': 0,
                'valid_links': 0,
                'broken_links': 0,
                'broken_link_details': [],
                'pages_with_broken_links': []
            }
            
            result = validator.run_comprehensive_validation(expected_pages)
            
        assert 'missing_pages' in result
        assert len(result['missing_pages']) == 2
        assert 'Missing Page 1' in result['missing_pages']
        assert 'Missing Page 2' in result['missing_pages']
        
        # Check recommendations include missing pages
        recommendations = result['recommendations']
        assert any('Investigate 2 missing expected pages' in rec for rec in recommendations)
        
        captured = capsys.readouterr()
        assert "2 expected pages not found" in captured.out
    
    def test_run_comprehensive_validation_performance_limit(self, capsys):
        """Test that comprehensive validation limits pages for performance."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(validator, 'get_all_pages') as mock_get_pages, \
             patch.object(validator, 'check_page_accessibility') as mock_check_access, \
             patch.object(validator, 'get_page_content') as mock_get_content, \
             patch.object(validator, 'validate_internal_links') as mock_validate_links:
            
            # Create 150 pages (more than 100 limit)
            large_page_list = [
                {'title': f'Page{i}'}
                for i in range(1, 151)
            ]
            mock_get_pages.return_value = large_page_list
            
            mock_check_access.return_value = {
                'api_accessible': True,
                'web_accessible': True,
                'content_length': 50
            }
            mock_get_content.return_value = '= Page =\n\nShort content.'
            mock_validate_links.return_value = {
                'total_links_checked': 0,
                'valid_links': 0,
                'broken_links': 0,
                'broken_link_details': [],
                'pages_with_broken_links': []
            }
            
            result = validator.run_comprehensive_validation()
            
        assert result['pages_found'] == 150
        assert len(result['page_details']) == 100  # Limited to 100
        assert result['pages_accessible'] == 100
        
        captured = capsys.readouterr()
        assert "Validating page 100/100" in captured.out


@pytest.mark.unit
class TestReportGeneration:
    """Test validation report generation."""
    
    def test_generate_validation_report_success(self):
        """Test successful validation report generation."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        # Mock comprehensive validation results
        validation_results = {
            'timestamp': '2025-08-07 10:00:00',
            'mediawiki_url': 'http://localhost:8080',
            'pages_found': 10,
            'pages_accessible': 9,
            'pages_with_issues': 2,
            'total_issues': 5,
            'total_warnings': 3,
            'quality_distribution': {
                'Excellent': 6,
                'Good': 1,
                'Fair': 1,
                'Poor': 1
            },
            'page_details': [
                {
                    'title': 'Good Page',
                    'accessible': True,
                    'quality': {
                        'issues': [],
                        'warnings': [],
                        'quality_level': 'Excellent'
                    }
                },
                {
                    'title': 'Problem Page',
                    'accessible': True,
                    'quality': {
                        'issues': ['Markdown not converted', 'Image syntax issue'],
                        'warnings': ['HTML tags found'],
                        'quality_level': 'Poor'
                    }
                },
                {
                    'title': 'Inaccessible Page',
                    'accessible': False,
                    'error': 'Page not found'
                }
            ],
            'link_validation': {
                'total_links_checked': 20,
                'valid_links': 15,
                'broken_links': 5,
                'pages_with_broken_links': [
                    {
                        'page': 'Problem Page',
                        'broken_links': ['Missing Page', 'Another Missing']
                    }
                ]
            },
            'summary': {
                'total_pages': 10,
                'accessibility_success_rate': 90.0,
                'quality_success_rate': 77.8,
                'pages_with_issues': 2,
                'total_issues_found': 5,
                'link_validation': {
                    'broken_links': 5,
                    'total_links_checked': 20
                }
            },
            'recommendations': [
                'Fix 1 inaccessible pages - check page titles and permissions',
                'Review 2 pages with content issues',
                'Fix 5 broken internal links'
            ]
        }
        
        report = validator.generate_validation_report(validation_results)
        
        # Check report structure and content
        assert "# MediaWiki Migration Validation Report" in report
        assert "**Generated**: 2025-08-07 10:00:00" in report
        assert "**MediaWiki URL**: http://localhost:8080" in report
        
        # Check metrics
        assert "**Pages Found**: 10" in report
        assert "**Pages Accessible**: 9 (90.0%)" in report
        assert "**Pages with Issues**: 2" in report
        assert "**Quality Success Rate**: 77.8%" in report
        
        # Check quality distribution
        assert "**Excellent**: 6 pages (66.7%)" in report
        assert "**Good**: 1 pages (11.1%)" in report
        assert "**Fair**: 1 pages (11.1%)" in report
        assert "**Poor**: 1 pages (11.1%)" in report
        
        # Check link validation
        assert "### 🔗 Link Validation" in report
        assert "**Total Internal Links Checked**: 20" in report
        assert "**Valid Links**: 15" in report
        assert "**Broken Links**: 5" in report
        assert "**Link Success Rate**: 75.0%" in report
        
        # Check issues breakdown
        assert "## 🚨 Issues Found" in report
        assert "**Markdown not converted**: 1 pages" in report
        assert "**Image syntax issue**: 1 pages" in report
        
        # Check broken links details
        assert "### 🔗 Broken Links Details" in report
        assert "**Problem Page**:" in report
        assert "- Missing Page" in report
        assert "- Another Missing" in report
        
        # Check recommendations
        assert "## 🎯 Recommendations" in report
        assert "- Fix 1 inaccessible pages" in report
        assert "- Review 2 pages with content issues" in report
        assert "- Fix 5 broken internal links" in report
        
        # Check next steps
        assert "## 🚀 Next Steps" in report
        assert "### Immediate Actions" in report
        assert "### Ongoing Maintenance" in report
        assert "### Validation Commands" in report
        assert "python post_migration_validator.py" in report
    
    def test_generate_validation_report_with_missing_pages(self):
        """Test report generation with missing expected pages."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        validation_results = {
            'timestamp': '2025-08-07 10:00:00',
            'mediawiki_url': 'http://localhost:8080',
            'pages_found': 5,
            'pages_accessible': 5,
            'pages_with_issues': 0,
            'total_issues': 0,
            'total_warnings': 0,
            'quality_distribution': {'Excellent': 5, 'Good': 0, 'Fair': 0, 'Poor': 0},
            'page_details': [],
            'link_validation': {
                'total_links_checked': 0,
                'valid_links': 0,
                'broken_links': 0,
                'pages_with_broken_links': []
            },
            'missing_pages': [
                'Expected Page 1',
                'Expected Page 2',
                'Expected Page 3',
                'Page 4', 'Page 5', 'Page 6', 'Page 7', 'Page 8', 
                'Page 9', 'Page 10', 'Page 11', 'Page 12'  # More than 10 missing
            ],
            'summary': {
                'total_pages': 5,
                'accessibility_success_rate': 100.0,
                'quality_success_rate': 100.0,
                'pages_with_issues': 0,
                'total_issues_found': 0,
                'link_validation': {'broken_links': 0, 'total_links_checked': 0}
            },
            'recommendations': []
        }
        
        report = validator.generate_validation_report(validation_results)
        
        # Check missing pages section
        assert "### 📄 Missing Pages" in report
        assert "Expected but not found: 12 pages" in report
        assert "- Expected Page 1" in report
        assert "- Expected Page 2" in report
        assert "- Expected Page 3" in report
        assert "... and 2 more" in report  # Should show truncation for >10 missing
    
    def test_generate_validation_report_no_issues(self):
        """Test report generation when no issues are found."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        clean_validation_results = {
            'timestamp': '2025-08-07 10:00:00',
            'mediawiki_url': 'http://localhost:8080',
            'pages_found': 5,
            'pages_accessible': 5,
            'pages_with_issues': 0,
            'total_issues': 0,
            'total_warnings': 0,
            'quality_distribution': {'Excellent': 5, 'Good': 0, 'Fair': 0, 'Poor': 0},
            'page_details': [],
            'link_validation': {
                'total_links_checked': 10,
                'valid_links': 10,
                'broken_links': 0,
                'pages_with_broken_links': []
            },
            'summary': {
                'total_pages': 5,
                'accessibility_success_rate': 100.0,
                'quality_success_rate': 100.0,
                'pages_with_issues': 0,
                'total_issues_found': 0,
                'link_validation': {'broken_links': 0, 'total_links_checked': 10}
            },
            'recommendations': ['🎉 Migration validation looks excellent! No major issues found.']
        }
        
        report = validator.generate_validation_report(clean_validation_results)
        
        assert "🎉 No content issues found!" in report
        assert "Migration validation looks excellent!" in report
        assert "**Link Success Rate**: 100.0%" in report


@pytest.mark.unit
class TestSummaryAndRecommendationGeneration:
    """Test summary and recommendation generation."""
    
    def test_generate_summary_calculations(self):
        """Test summary generation with correct calculations."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        # Mock results for calculation testing
        results = {
            'pages_found': 20,
            'pages_accessible': 18,
            'pages_with_issues': 3,
            'total_issues': 7,
            'link_validation': {
                'broken_links': 5,
                'total_links_checked': 25
            }
        }
        
        summary = validator._generate_summary(results)
        
        assert summary['total_pages'] == 20
        assert summary['accessibility_success_rate'] == 90.0  # 18/20 * 100
        assert summary['quality_success_rate'] == 83.3  # (18-3)/18 * 100, rounded
        assert summary['pages_with_issues'] == 3
        assert summary['total_issues_found'] == 7
        assert summary['link_validation']['broken_links'] == 5
        assert summary['link_validation']['total_links_checked'] == 25
    
    def test_generate_summary_edge_cases(self):
        """Test summary generation with edge cases."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        # Edge case: no pages found
        empty_results = {
            'pages_found': 0,
            'pages_accessible': 0,
            'pages_with_issues': 0,
            'total_issues': 0,
            'link_validation': {'broken_links': 0, 'total_links_checked': 0}
        }
        
        summary = validator._generate_summary(empty_results)
        
        assert summary['accessibility_success_rate'] == 0
        assert summary['quality_success_rate'] == 0
    
    def test_generate_recommendations_comprehensive(self):
        """Test comprehensive recommendation generation."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        results_with_issues = {
            'pages_found': 20,
            'pages_accessible': 17,  # 3 inaccessible
            'pages_with_issues': 5,
            'quality_distribution': {'Poor': 2, 'Fair': 3, 'Good': 10, 'Excellent': 2},
            'link_validation': {'broken_links': 8},
            'missing_pages': ['Page1', 'Page2', 'Page3']
        }
        
        recommendations = validator._generate_recommendations(results_with_issues)
        
        # Should generate multiple recommendations
        assert len(recommendations) >= 4
        
        recommendation_text = ' '.join(recommendations)
        assert '3 inaccessible pages' in recommendation_text
        assert '5 pages with content issues' in recommendation_text
        assert '2 pages with poor quality scores' in recommendation_text
        assert '8 broken internal links' in recommendation_text
        assert '3 missing expected pages' in recommendation_text
        assert 'run validation again' in recommendation_text
    
    def test_generate_recommendations_no_issues(self):
        """Test recommendation generation when no issues found."""
        validator = MigrationValidator("http://localhost:8080", "testuser", "testpass")
        
        clean_results = {
            'pages_found': 10,
            'pages_accessible': 10,
            'pages_with_issues': 0,
            'quality_distribution': {'Poor': 0, 'Fair': 0, 'Good': 5, 'Excellent': 5},
            'link_validation': {'broken_links': 0}
        }
        
        recommendations = validator._generate_recommendations(clean_results)
        
        assert len(recommendations) == 1
        assert 'Migration validation looks excellent! No major issues found.' in recommendations[0]


@pytest.mark.unit
class TestConfigurationLoading:
    """Test configuration loading for validation tool."""
    
    def test_load_config_success(self, mock_env_vars):
        """Test successful configuration loading."""
        # Only need MediaWiki vars for validation tool
        mediawiki_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD']
        }
        
        with patch.dict(os.environ, mediawiki_env):
            wiki_url, username, password = load_config()
            
        assert wiki_url == "http://localhost:8080"
        assert username == "testuser"
        assert password == "testpass123"
    
    def test_load_config_missing_required(self, capsys):
        """Test configuration loading with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables!" in captured.out
        assert "WIKI_URL, WIKI_USERNAME, WIKI_PASSWORD" in captured.out


@pytest.mark.integration
class TestMainFunction:
    """Test main function integration."""
    
    def test_main_success_flow(self, mock_env_vars, temp_directory, monkeypatch, capsys):
        """Test successful main function execution."""
        monkeypatch.chdir(temp_directory)
        
        # Only need MediaWiki vars for validation tool
        mediawiki_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD']
        }
        
        with patch.dict(os.environ, mediawiki_env), \
             patch('validation_tool.MigrationValidator') as mock_validator_class, \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_validator = mock_validator_class.return_value
            
            # Mock successful validation results
            mock_validation_results = {
                'timestamp': '2025-08-07 10:00:00',
                'pages_found': 5,
                'pages_accessible': 5,
                'summary': {
                    'total_pages': 5,
                    'accessibility_success_rate': 100.0,
                    'quality_success_rate': 100.0,
                    'total_issues_found': 0,
                    'link_validation': {'broken_links': 0}
                }
            }
            mock_validator.run_comprehensive_validation.return_value = mock_validation_results
            mock_validator.generate_validation_report.return_value = "Test Validation Report"
            
            main()
            
        # Verify validator was created and methods called
        mock_validator_class.assert_called_once_with("http://localhost:8080", "testuser", "testpass123")
        mock_validator.run_comprehensive_validation.assert_called_once()
        mock_validator.generate_validation_report.assert_called_once()
        
        # Verify file was written
        mock_file.assert_called_once_with("migration_validation_report.md", "w", encoding='utf-8')
        
        captured = capsys.readouterr()
        assert "Validation complete!" in captured.out
        assert "Found 5 pages" in captured.out
        assert "100.0% accessibility success rate" in captured.out
        assert "100.0% quality success rate" in captured.out
    
    def test_main_with_issues_summary(self, mock_env_vars, temp_directory, monkeypatch, capsys):
        """Test main function with validation issues."""
        monkeypatch.chdir(temp_directory)
        
        mediawiki_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD']
        }
        
        with patch.dict(os.environ, mediawiki_env), \
             patch('validation_tool.MigrationValidator') as mock_validator_class, \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_validator = mock_validator_class.return_value
            
            # Mock validation results with issues
            mock_validation_results = {
                'summary': {
                    'total_pages': 10,
                    'accessibility_success_rate': 90.0,
                    'quality_success_rate': 80.0,
                    'total_issues_found': 5,
                    'link_validation': {'broken_links': 3}
                }
            }
            mock_validator.run_comprehensive_validation.return_value = mock_validation_results
            mock_validator.generate_validation_report.return_value = "Report with Issues"
            
            main()
            
        captured = capsys.readouterr()
        assert "Found 5 issues to review" in captured.out
        assert "Found 3 broken internal links" in captured.out
    
    def test_main_missing_dependencies(self, capsys):
        """Test main function with missing dependencies."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'requests'")):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Required package not installed" in captured.out
    
    def test_main_configuration_error(self, capsys):
        """Test main function with configuration error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables!" in captured.out
    
    def test_main_validation_error(self, mock_env_vars, capsys):
        """Test main function with validation error."""
        mediawiki_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD']
        }
        
        with patch.dict(os.environ, mediawiki_env), \
             patch('validation_tool.MigrationValidator', side_effect=Exception("Connection failed")):
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Validation failed" in captured.out


if __name__ == '__main__':
    pytest.main([__file__])