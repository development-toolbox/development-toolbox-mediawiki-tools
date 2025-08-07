#!/usr/bin/env python3
"""
Tests for azure_devops_migrator.py - Azure DevOps to MediaWiki Migration Script.
"""

import os
import sys
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open, call

import pytest
import requests

# Add the migration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'migration'))
from azure_devops_migrator import (
    AzureDevOpsWikiClient, MediaWikiClient, ContentConverter, ProgressTracker,
    WikiMigrator, load_config, main
)


@pytest.mark.unit
class TestAzureDevOpsWikiClient:
    """Test AzureDevOpsWikiClient functionality."""
    
    def test_init_success(self):
        """Test successful Azure DevOps client initialization."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        assert client.organization == "test-org"
        assert client.project == "test-project"
        assert client.pat == "test-pat"
        assert client.base_url == "https://dev.azure.com/test-org/test-project/_apis"
        assert "Basic" in client.session.headers['Authorization']
        assert "MediaWiki-Migration-Tool" in client.session.headers['User-Agent']
    
    def test_make_api_request_success(self, mock_azure_api_response):
        """Test successful API request."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_azure_api_response['wikis']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = client._make_api_request('GET', 'https://example.com/api')
            
        assert result == mock_azure_api_response['wikis']
        mock_get.assert_called_once_with('https://example.com/api', timeout=30)
    
    def test_make_api_request_timeout_retry(self, capsys):
        """Test API request with timeout and retry."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timed out"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = client._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
    
    def test_get_wikis_success(self, mock_azure_api_response):
        """Test successful wiki retrieval."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client, '_make_api_request') as mock_request:
            mock_request.return_value = mock_azure_api_response['wikis']
            
            wikis = client.get_wikis()
            
        assert len(wikis) == 1
        assert wikis[0]['name'] == 'TestWiki'
        mock_request.assert_called_once()
    
    def test_get_wikis_api_error(self, capsys):
        """Test wiki retrieval with API error."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client, '_make_api_request') as mock_request:
            mock_request.side_effect = requests.RequestException("API Error")
            
            with pytest.raises(requests.RequestException):
                client.get_wikis()
                
        captured = capsys.readouterr()
        assert "Failed to retrieve wikis" in captured.out
    
    def test_get_page_content_success(self, mock_azure_api_response):
        """Test successful page content retrieval."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client, '_make_api_request') as mock_request:
            mock_request.return_value = {'content': mock_azure_api_response['page_content']['page-1']}
            
            content = client.get_page_content("wiki-123", "page-1")
            
        assert "Welcome" in content
        assert "home page" in content
    
    def test_get_page_content_error_handling(self, capsys):
        """Test page content retrieval with error handling."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client, '_make_api_request') as mock_request:
            mock_request.side_effect = requests.RequestException("Content not found")
            
            content = client.get_page_content("wiki-123", "invalid-page")
            
        assert content == ''
        captured = capsys.readouterr()
        assert "Failed to retrieve content" in captured.out


@pytest.mark.unit
class TestMediaWikiClient:
    """Test MediaWikiClient functionality."""
    
    def test_init_success(self):
        """Test successful MediaWiki client initialization."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        assert client.wiki_url == "http://localhost:8080"
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.api_url == "http://localhost:8080/api.php"
        assert not client._logged_in
    
    def test_make_request_success(self, mock_mediawiki_api_response):
        """Test successful MediaWiki API request."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(client.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mediawiki_api_response['login_token']
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = client._make_request("POST", action="query", meta="tokens")
            
        assert result == mock_mediawiki_api_response['login_token']
        mock_post.assert_called_once()
    
    def test_make_request_timeout_retry(self, capsys):
        """Test MediaWiki API request with timeout and retry."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(client.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            mock_post.side_effect = [
                requests.exceptions.Timeout("Timed out"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = client._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
    
    def test_make_request_authentication_error(self, capsys):
        """Test MediaWiki API request with authentication error."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(client.session, 'post') as mock_post:
            auth_error_response = MagicMock()
            auth_error_response.status_code = 401
            auth_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=auth_error_response)
            mock_post.return_value = auth_error_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                client._make_request("POST", action="test")
                
        captured = capsys.readouterr()
        assert "authentication failed" in captured.out
    
    def test_login_success(self, mock_mediawiki_api_response, capsys):
        """Test successful MediaWiki login."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                mock_mediawiki_api_response['login_token'],
                mock_mediawiki_api_response['login_success']
            ]
            
            client.login()
            
        assert client._logged_in is True
        assert mock_request.call_count == 2
        
        captured = capsys.readouterr()
        assert "Successfully logged into MediaWiki" in captured.out
    
    def test_login_failure(self, mock_mediawiki_api_response, capsys):
        """Test MediaWiki login failure."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        failed_login_response = {
            'login': {
                'result': 'Failed',
                'reason': 'Invalid credentials'
            }
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                mock_mediawiki_api_response['login_token'],
                failed_login_response
            ]
            
            with pytest.raises(Exception, match="MediaWiki login failed"):
                client.login()
                
        assert client._logged_in is False
        captured = capsys.readouterr()
        assert "MediaWiki login failed" in captured.out
    
    def test_login_already_logged_in(self):
        """Test login when already logged in."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        client._logged_in = True
        
        with patch.object(client, '_make_request') as mock_request:
            client.login()
            
        mock_request.assert_not_called()
    
    def test_create_page_success(self, mock_mediawiki_api_response):
        """Test successful page creation."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(client, 'login'), \
             patch.object(client, '_make_request') as mock_request:
            
            mock_request.side_effect = [
                mock_mediawiki_api_response['edit_token'],
                mock_mediawiki_api_response['edit_success']
            ]
            
            result = client.create_page("Test Page", "Test content")
            
        assert result is True
        assert mock_request.call_count == 2
    
    def test_create_page_failure(self, mock_mediawiki_api_response, capsys):
        """Test page creation failure."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        failed_edit_response = {
            'edit': {
                'result': 'Failure'
            },
            'error': {
                'info': 'Permission denied'
            }
        }
        
        with patch.object(client, 'login'), \
             patch.object(client, '_make_request') as mock_request:
            
            mock_request.side_effect = [
                mock_mediawiki_api_response['edit_token'],
                failed_edit_response
            ]
            
            result = client.create_page("Test Page", "Test content")
            
        assert result is False
        captured = capsys.readouterr()
        assert "Failed to create page 'Test Page'" in captured.out


@pytest.mark.unit
class TestContentConverter:
    """Test ContentConverter functionality."""
    
    def test_markdown_to_mediawiki_headers(self):
        """Test markdown to MediaWiki header conversion."""
        markdown = """# Main Title
## Sub Title
### Sub Sub Title
#### Level 4
##### Level 5"""
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "= Main Title =" in result
        assert "== Sub Title ==" in result
        assert "=== Sub Sub Title ===" in result
        assert "==== Level 4 ====" in result
        assert "===== Level 5 =====" in result
    
    def test_markdown_to_mediawiki_formatting(self):
        """Test markdown to MediaWiki text formatting conversion."""
        markdown = "This has **bold** and *italic* and __bold__ and _italic_ text."
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "'''bold'''" in result
        assert "''italic''" in result
        # Should handle both ** and __ for bold, * and _ for italic
        assert result.count("'''") >= 4  # Two bold instances
        assert result.count("''") >= 8   # Two italic instances + bold markers
    
    def test_markdown_to_mediawiki_links(self):
        """Test markdown to MediaWiki link conversion."""
        markdown = "Check out [this link](https://example.com) and [another](page.html)."
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "[https://example.com this link]" in result
        assert "[page.html another]" in result
    
    def test_markdown_to_mediawiki_code_blocks(self):
        """Test markdown to MediaWiki code block conversion."""
        markdown = '''Here is some `inline code` and a code block:

```python
def hello():
    print("Hello, World!")
```

More text.'''
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "<code>inline code</code>" in result
        assert '<syntaxhighlight lang="python">' in result
        assert 'def hello():' in result
        assert '</syntaxhighlight>' in result
    
    def test_markdown_to_mediawiki_lists(self):
        """Test markdown to MediaWiki list conversion."""
        markdown = """Unordered list:
- Item 1
- Item 2
  - Nested item

Ordered list:
1. First item
2. Second item
3. Third item"""
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "* Item 1" in result
        assert "* Item 2" in result
        assert "# First item" in result
        assert "# Second item" in result
    
    def test_sanitize_page_title(self):
        """Test page title sanitization."""
        test_cases = [
            ("my-page.md", "My Page"),
            ("setup_guide.md", "Setup Guide"),
            ("API-Reference", "Api Reference"),  # title() changes API to Api
            ("user_manual", "User Manual"),
            ("complex-file-name-with-many-parts.md", "Complex File Name With Many Parts")
        ]
        
        for input_title, expected_output in test_cases:
            result = ContentConverter.sanitize_page_title(input_title)
            assert result == expected_output


@pytest.mark.unit
class TestProgressTracker:
    """Test ProgressTracker functionality."""
    
    def test_init_new_tracker(self, temp_directory, monkeypatch):
        """Test ProgressTracker initialization without existing checkpoint."""
        monkeypatch.chdir(temp_directory)
        
        tracker = ProgressTracker('.test_checkpoint')
        
        assert len(tracker.progress['processed_pages']) == 0
        assert len(tracker.progress['failed_pages']) == 0
        assert len(tracker.progress['skipped_pages']) == 0
        assert 'start_time' in tracker.progress
    
    def test_init_with_existing_checkpoint(self, temp_directory, monkeypatch, capsys):
        """Test ProgressTracker initialization with existing checkpoint."""
        monkeypatch.chdir(temp_directory)
        
        # Create existing checkpoint data
        checkpoint_data = {
            'processed_pages': {'page1', 'page2'},
            'failed_pages': {'page3': {'error': 'Test error', 'timestamp': 123456}},
            'skipped_pages': {'page4': 'Empty content'},
            'start_time': 123456789
        }
        
        checkpoint_file = temp_directory / '.test_checkpoint'
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        tracker = ProgressTracker('.test_checkpoint')
        
        assert len(tracker.progress['processed_pages']) == 2
        assert len(tracker.progress['failed_pages']) == 1
        assert len(tracker.progress['skipped_pages']) == 1
        assert 'page1' in tracker.progress['processed_pages']
        
        captured = capsys.readouterr()
        assert "Resuming migration from checkpoint (2 pages completed)" in captured.out
    
    def test_mark_processed(self, temp_directory, monkeypatch):
        """Test marking pages as processed."""
        monkeypatch.chdir(temp_directory)
        
        tracker = ProgressTracker('.test_checkpoint')
        
        with patch.object(tracker, 'save_checkpoint') as mock_save:
            # Mark first 9 pages (shouldn't trigger save)
            for i in range(9):
                tracker.mark_processed(f'page{i}')
            
            mock_save.assert_not_called()
            
            # Mark 10th page (should trigger save)
            tracker.mark_processed('page10')
            
            mock_save.assert_called_once()
        
        assert len(tracker.progress['processed_pages']) == 10
        assert tracker.should_skip('page5') is True
        assert tracker.should_skip('new_page') is False
    
    def test_mark_failed(self, temp_directory, monkeypatch):
        """Test marking pages as failed."""
        monkeypatch.chdir(temp_directory)
        
        tracker = ProgressTracker('.test_checkpoint')
        
        with patch.object(tracker, 'save_checkpoint') as mock_save, \
             patch('time.time', return_value=1234567890):
            
            tracker.mark_failed('failing_page', 'Test error message')
            
        mock_save.assert_called_once()
        assert 'failing_page' in tracker.progress['failed_pages']
        assert tracker.progress['failed_pages']['failing_page']['error'] == 'Test error message'
        assert tracker.progress['failed_pages']['failing_page']['timestamp'] == 1234567890
    
    def test_mark_skipped(self, temp_directory, monkeypatch):
        """Test marking pages as skipped."""
        monkeypatch.chdir(temp_directory)
        
        tracker = ProgressTracker('.test_checkpoint')
        
        tracker.mark_skipped('empty_page', 'No content')
        
        assert 'empty_page' in tracker.progress['skipped_pages']
        assert tracker.progress['skipped_pages']['empty_page'] == 'No content'
    
    def test_save_and_load_checkpoint(self, temp_directory, monkeypatch):
        """Test checkpoint saving and loading."""
        monkeypatch.chdir(temp_directory)
        
        tracker1 = ProgressTracker('.test_checkpoint')
        tracker1.mark_processed('page1')
        tracker1.mark_failed('page2', 'Error')
        tracker1.save_checkpoint()
        
        # Create new tracker from same checkpoint
        tracker2 = ProgressTracker('.test_checkpoint')
        
        assert 'page1' in tracker2.progress['processed_pages']
        assert 'page2' in tracker2.progress['failed_pages']
    
    def test_cleanup_success(self, temp_directory, monkeypatch, capsys):
        """Test successful checkpoint cleanup."""
        monkeypatch.chdir(temp_directory)
        
        # Create checkpoint file
        checkpoint_file = temp_directory / '.test_checkpoint'
        checkpoint_file.write_text("test data")
        
        tracker = ProgressTracker('.test_checkpoint')
        tracker.cleanup()
        
        assert not checkpoint_file.exists()
        
        captured = capsys.readouterr()
        assert "Migration completed successfully" in captured.out


@pytest.mark.unit
class TestWikiMigrator:
    """Test WikiMigrator functionality."""
    
    def test_init(self):
        """Test WikiMigrator initialization."""
        azure_client = MagicMock()
        mediawiki_client = MagicMock()
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        assert migrator.azure_client == azure_client
        assert migrator.mediawiki_client == mediawiki_client
        assert migrator.converter is not None
    
    def test_migrate_wiki_no_wikis_found(self, capsys):
        """Test migration when no wikis are found."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = []
        mediawiki_client = MagicMock()
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        success_count, failed_count = migrator.migrate_wiki()
        
        assert success_count == 0
        assert failed_count == 0
        
        captured = capsys.readouterr()
        assert "No wikis found" in captured.out
    
    def test_migrate_wiki_specific_wiki_not_found(self, capsys):
        """Test migration when specified wiki is not found."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = [
            {'id': 'wiki-1', 'name': 'OtherWiki'}
        ]
        mediawiki_client = MagicMock()
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        success_count, failed_count = migrator.migrate_wiki("SpecificWiki")
        
        assert success_count == 0
        assert failed_count == 0
        
        captured = capsys.readouterr()
        assert "Wiki 'SpecificWiki' not found" in captured.out
        assert "Available wikis: OtherWiki" in captured.out
    
    def test_migrate_wiki_no_pages_found(self, capsys):
        """Test migration when no pages are found in wiki."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = [
            {'id': 'wiki-1', 'name': 'TestWiki'}
        ]
        azure_client.get_wiki_pages.return_value = []
        mediawiki_client = MagicMock()
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        success_count, failed_count = migrator.migrate_wiki()
        
        assert success_count == 0
        assert failed_count == 0
        
        captured = capsys.readouterr()
        assert "No pages found in the wiki" in captured.out
    
    def test_migrate_wiki_successful_migration(self, mock_azure_api_response, capsys):
        """Test successful wiki migration."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = mock_azure_api_response['wikis']['value']
        azure_client.get_wiki_pages.return_value = mock_azure_api_response['pages']['value'][:1]  # Just one page
        azure_client.get_page_content.return_value = "# Test Page\n\nThis is test content."
        
        mediawiki_client = MagicMock()
        mediawiki_client.create_page.return_value = True
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        with patch('azure_devops_migrator.ProgressTracker') as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.should_skip.return_value = False
            
            success_count, failed_count = migrator.migrate_wiki()
        
        assert success_count == 1
        assert failed_count == 0
        
        mock_tracker.mark_processed.assert_called_once()
        mediawiki_client.create_page.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Successfully migrated" in captured.out
    
    def test_migrate_wiki_with_errors(self, mock_azure_api_response, capsys):
        """Test wiki migration with various error conditions."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = mock_azure_api_response['wikis']['value']
        azure_client.get_wiki_pages.return_value = [
            {'id': 'page1', 'path': '/Page1'},
            {'id': 'page2', 'path': '/Page2'},
            {'id': 'page3', 'path': '/Page3'}
        ]
        
        # Different error conditions for different pages
        def content_side_effect(wiki_id, page_id):
            if page_id == 'page1':
                return "# Good Page\n\nContent here."
            elif page_id == 'page2':
                raise Exception("Content retrieval failed")
            else:  # page3
                return ""  # Empty content
        
        azure_client.get_page_content.side_effect = content_side_effect
        
        mediawiki_client = MagicMock()
        mediawiki_client.create_page.return_value = True
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        with patch('azure_devops_migrator.ProgressTracker') as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.should_skip.return_value = False
            
            success_count, failed_count = migrator.migrate_wiki()
        
        assert success_count == 1  # Only page1 succeeds
        assert failed_count == 1   # page2 fails, page3 is skipped
        
        # Verify tracking calls
        mock_tracker.mark_processed.assert_called_once()
        mock_tracker.mark_failed.assert_called_once()
        mock_tracker.mark_skipped.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Skipping empty page" in captured.out
        assert "Failed to retrieve content" in captured.out
    
    def test_migrate_wiki_resume_functionality(self, mock_azure_api_response, capsys):
        """Test migration resume functionality."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = mock_azure_api_response['wikis']['value']
        azure_client.get_wiki_pages.return_value = [
            {'id': 'page1', 'path': '/Page1'},
            {'id': 'page2', 'path': '/Page2'}
        ]
        azure_client.get_page_content.return_value = "# Test content"
        
        mediawiki_client = MagicMock()
        mediawiki_client.create_page.return_value = True
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        with patch('azure_devops_migrator.ProgressTracker') as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            
            # First page already processed, second page not processed
            def should_skip_side_effect(page_id):
                return page_id == 'page1'
            
            mock_tracker.should_skip.side_effect = should_skip_side_effect
            
            success_count, failed_count = migrator.migrate_wiki()
        
        assert success_count == 2  # page1 skipped but counted as success, page2 processed
        assert failed_count == 0
        
        # Only page2 should be processed
        mock_tracker.mark_processed.assert_called_once_with('page2')
        
        captured = capsys.readouterr()
        assert "Skipping already processed page" in captured.out
    
    def test_migrate_wiki_keyboard_interrupt(self, mock_azure_api_response, capsys):
        """Test migration handling of keyboard interrupt."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = mock_azure_api_response['wikis']['value']
        azure_client.get_wiki_pages.return_value = [
            {'id': 'page1', 'path': '/Page1'}
        ]
        azure_client.get_page_content.side_effect = KeyboardInterrupt()
        
        mediawiki_client = MagicMock()
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        with patch('azure_devops_migrator.ProgressTracker') as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.should_skip.return_value = False
            
            with pytest.raises(KeyboardInterrupt):
                migrator.migrate_wiki()
        
        mock_tracker.save_checkpoint.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Migration interrupted by user" in captured.out
        assert "Resume later by running the same command" in captured.out


@pytest.mark.unit
class TestConfigurationLoading:
    """Test configuration loading functionality."""
    
    def test_load_config_success(self, mock_env_vars):
        """Test successful configuration loading."""
        with patch.dict(os.environ, mock_env_vars):
            org, project, pat, wiki_url, username, password, wiki_name = load_config()
            
        assert org == "test-org"
        assert project == "test-project"
        assert pat == "test-pat-token-123"
        assert wiki_url == "http://localhost:8080"
        assert username == "testuser"
        assert password == "testpass123"
        assert wiki_name == "TestWiki"
    
    def test_load_config_missing_required(self, capsys):
        """Test configuration loading with missing required variables."""
        partial_env = {
            'AZURE_DEVOPS_ORGANIZATION': 'test-org',
            'AZURE_DEVOPS_PROJECT': 'test-project'
            # Missing other required vars
        }
        
        with patch.dict(os.environ, partial_env, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
    
    def test_load_config_validation_errors(self, capsys):
        """Test configuration validation with invalid values."""
        invalid_env = {
            'AZURE_DEVOPS_ORGANIZATION': 'test-org',
            'AZURE_DEVOPS_PROJECT': '',  # Empty project
            'AZURE_DEVOPS_PAT': 'short',  # Too short
            'WIKI_URL': 'invalid-url',    # Invalid URL format
            'WIKI_USERNAME': 'testuser',
            'WIKI_PASSWORD': 'testpass'
        }
        
        with patch.dict(os.environ, invalid_env, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "Azure DevOps project name cannot be empty" in captured.out
    
    def test_load_config_warnings(self, mock_env_vars, capsys):
        """Test configuration loading with warnings."""
        warning_env = mock_env_vars.copy()
        warning_env['AZURE_DEVOPS_ORGANIZATION'] = 'org@with#special!'
        warning_env['AZURE_DEVOPS_PAT'] = 'short'
        
        with patch.dict(os.environ, warning_env):
            org, project, pat, wiki_url, username, password, wiki_name = load_config()
            
        # Should still succeed but with warnings
        assert org == 'org@with#special!'
        
        captured = capsys.readouterr()
        assert "organization name looks suspicious" in captured.out
        assert "Personal Access Token seems too short" in captured.out


@pytest.mark.integration
class TestMainFunction:
    """Test main function integration."""
    
    def test_main_success_flow(self, mock_env_vars, mock_azure_api_response, mock_mediawiki_api_response, capsys):
        """Test successful main function execution."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('azure_devops_migrator.AzureDevOpsWikiClient') as mock_azure_class, \
             patch('azure_devops_migrator.MediaWikiClient') as mock_mediawiki_class:
            
            # Setup Azure client mock
            mock_azure_client = mock_azure_class.return_value
            mock_azure_client.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_azure_client.get_wiki_pages.return_value = mock_azure_api_response['pages']['value'][:1]
            mock_azure_client.get_page_content.return_value = "# Test Page\n\nContent here."
            
            # Setup MediaWiki client mock
            mock_mediawiki_client = mock_mediawiki_class.return_value
            mock_mediawiki_client.create_page.return_value = True
            
            # Mock progress tracker to avoid file I/O
            with patch('azure_devops_migrator.ProgressTracker') as mock_tracker_class:
                mock_tracker = mock_tracker_class.return_value
                mock_tracker.should_skip.return_value = False
                
                main()
            
        # Verify clients were created with correct parameters
        mock_azure_class.assert_called_once_with("test-org", "test-project", "test-pat-token-123")
        mock_mediawiki_class.assert_called_once_with("http://localhost:8080", "testuser", "testpass123")
        
        captured = capsys.readouterr()
        assert "Migration complete!" in captured.out
        assert "Successfully migrated: 1 pages" in captured.out
        assert "Visit your MediaWiki at: http://localhost:8080" in captured.out
    
    def test_main_configuration_error(self, capsys):
        """Test main function with configuration error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
    
    def test_main_migration_error(self, mock_env_vars, capsys):
        """Test main function with migration error."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('azure_devops_migrator.AzureDevOpsWikiClient', side_effect=Exception("Connection failed")):
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Migration failed" in captured.out


@pytest.mark.api
class TestRetryLogicAndErrorHandling:
    """Test retry logic and comprehensive error handling."""
    
    def test_azure_client_comprehensive_retry_scenarios(self, capsys):
        """Test comprehensive retry scenarios for Azure DevOps client."""
        client = AzureDevOpsWikiClient("test-org", "test-project", "test-pat")
        
        with patch.object(client.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Test all retry scenarios
            error_responses = [
                requests.exceptions.Timeout("Timeout 1"),
                requests.exceptions.ConnectionError("Connection 1"),
                requests.exceptions.HTTPError(response=MagicMock(status_code=429, headers={'Retry-After': '5'})),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            mock_get.side_effect = error_responses
            
            result = client._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        assert mock_get.call_count == 4
        assert mock_sleep.call_count == 3  # Two regular retries + one rate limit
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
        assert "Connection error, retrying" in captured.out
        assert "Rate limited, waiting 5s" in captured.out
    
    def test_mediawiki_client_server_error_retry(self, capsys):
        """Test MediaWiki client server error retry logic."""
        client = MediaWikiClient("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(client.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            # First request: 500 error, second request: success
            error_response = MagicMock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            success_response = MagicMock()
            success_response.json.return_value = {"success": True}
            success_response.raise_for_status.return_value = None
            
            mock_post.side_effect = [error_response, success_response]
            
            result = client._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(5)  # Server error wait time
        
        captured = capsys.readouterr()
        assert "Server error, retrying" in captured.out
    
    def test_content_converter_edge_cases(self):
        """Test ContentConverter with edge cases and complex content."""
        converter = ContentConverter()
        
        # Test content with mixed markdown and special characters
        complex_content = """# Title with "quotes" and 'apostrophes'
        
## Code with special characters

```bash
echo "Hello $USER" && ls -la | grep ".*\\.py$"
```

### Links with special characters
[Link with spaces](https://example.com/path with spaces?param=value&other=123)

### Nested formatting
This is **bold with *italic* inside** and some `code with **bold**` inside.

### Complex table
| Column "A" | Column 'B' | Column `C` |
|------------|------------|------------|
| Data & more| Data < less| Data > more|

### Mixed list formats
- Item with **bold**
  - Sub-item with `code`
    - Deep nesting
1. Numbered with [link](url)
2. Another with *emphasis*
"""
        
        result = converter.markdown_to_mediawiki(complex_content)
        
        # Verify basic conversions work
        assert "= Title with" in result
        assert "== Code with special characters ==" in result
        assert '<syntaxhighlight lang="bash">' in result
        assert "[https://example.com/path with spaces?param=value&other=123 Link with spaces]" in result
        assert "'''bold with ''italic'' inside'''" in result
        assert "{| class=\"wikitable\"" in result
        assert "* Item with '''bold'''" in result
        assert "# Numbered with" in result


@pytest.mark.slow
class TestPerformanceAndLargeData:
    """Test performance with large datasets and stress scenarios."""
    
    def test_large_wiki_migration_progress_tracking(self, capsys):
        """Test migration progress tracking with large number of pages."""
        azure_client = MagicMock()
        azure_client.get_wikis.return_value = [
            {'id': 'wiki-1', 'name': 'LargeWiki'}
        ]
        
        # Create 100 pages
        large_page_list = [
            {'id': f'page-{i}', 'path': f'/Page{i}'}
            for i in range(1, 101)
        ]
        
        azure_client.get_wiki_pages.return_value = large_page_list
        azure_client.get_page_content.return_value = "# Test content\n\nSample page content here."
        
        mediawiki_client = MagicMock()
        mediawiki_client.create_page.return_value = True
        
        migrator = WikiMigrator(azure_client, mediawiki_client)
        
        with patch('azure_devops_migrator.ProgressTracker') as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.should_skip.return_value = False
            
            success_count, failed_count = migrator.migrate_wiki()
        
        assert success_count == 100
        assert failed_count == 0
        
        # Verify progress tracking was used efficiently
        assert mock_tracker.mark_processed.call_count == 100
        # Checkpoint should be saved every 10 pages
        assert mock_tracker.save_checkpoint.call_count >= 9  # At least 9 checkpoint saves
        
        captured = capsys.readouterr()
        # Should show progress for this many pages
        assert "Found 100 pages to migrate" in captured.out


if __name__ == '__main__':
    pytest.main([__file__])