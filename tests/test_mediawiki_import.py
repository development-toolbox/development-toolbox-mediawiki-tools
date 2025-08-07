#!/usr/bin/env python3
"""
Tests for mediawiki_import.py - MediaWiki Template Import Script.
"""

import os
import sys
import json
import glob
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
import requests

# Add the templates directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'templates'))
from mediawiki_import import MediaWikiImporter, load_config, main


@pytest.mark.unit
class TestMediaWikiImporter:
    """Test MediaWikiImporter class functionality."""
    
    def test_init_success(self):
        """Test successful MediaWikiImporter initialization."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        assert importer.wiki_url == "http://localhost:8080"
        assert importer.username == "testuser"
        assert importer.password == "testpass"
        assert importer.api_url == "http://localhost:8080/api.php"
    
    def test_init_url_normalization(self):
        """Test that URLs are properly normalized."""
        importer = MediaWikiImporter("http://localhost:8080/", "testuser", "testpass")
        
        assert importer.wiki_url == "http://localhost:8080"
        assert importer.api_url == "http://localhost:8080/api.php"


@pytest.mark.unit
class TestApiRequests:
    """Test MediaWiki API request handling."""
    
    def test_make_request_success_post(self, mock_mediawiki_api_response):
        """Test successful POST API request."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mediawiki_api_response['login_token']
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = importer._make_request("POST", action="query", meta="tokens")
            
        assert result == mock_mediawiki_api_response['login_token']
        mock_post.assert_called_once()
    
    def test_make_request_success_get(self, mock_mediawiki_api_response):
        """Test successful GET API request."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mediawiki_api_response['login_token']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = importer._make_request("GET", action="query", meta="tokens")
            
        assert result == mock_mediawiki_api_response['login_token']
        mock_get.assert_called_once()
    
    def test_make_request_timeout_retry(self, capsys):
        """Test API request with timeout and retry logic."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            mock_post.side_effect = [
                requests.exceptions.Timeout("Timed out"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = importer._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
    
    def test_make_request_connection_error_retry(self, capsys):
        """Test API request with connection error and retry."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            mock_post.side_effect = [
                requests.exceptions.ConnectionError("Connection failed"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = importer._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Connection error, retrying" in captured.out
    
    def test_make_request_authentication_error(self, capsys):
        """Test API request with authentication error."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post:
            auth_error_response = MagicMock()
            auth_error_response.status_code = 401
            auth_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=auth_error_response)
            mock_post.return_value = auth_error_response
            
            with pytest.raises(Exception, match="Authentication failed"):
                importer._make_request("POST", action="test")
                
        captured = capsys.readouterr()
        assert "Authentication failed" in captured.out
    
    def test_make_request_server_error_retry(self, capsys):
        """Test API request with server error and retry."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            # First request: 500 error, second request: success
            error_response = MagicMock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            success_response = MagicMock()
            success_response.json.return_value = {"success": True}
            success_response.raise_for_status.return_value = None
            
            mock_post.side_effect = [error_response, success_response]
            
            result = importer._make_request("POST", action="test")
            
        assert result == {"success": True}
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(5)  # Server error wait time
        
        captured = capsys.readouterr()
        assert "Server error, retrying" in captured.out
    
    def test_make_request_json_decode_error(self, capsys):
        """Test API request with JSON decode error."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="Invalid JSON response"):
                importer._make_request("POST", action="test")
                
        captured = capsys.readouterr()
        assert "Invalid JSON response" in captured.out
        assert "MediaWiki might be returning HTML error page" in captured.out


@pytest.mark.unit
class TestTokenHandling:
    """Test MediaWiki token handling functionality."""
    
    def test_get_login_token_success(self, mock_mediawiki_api_response, capsys):
        """Test successful login token retrieval."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = mock_mediawiki_api_response['login_token']
            
            token = importer.get_login_token()
            
        assert token == "test-login-token-456"
        
        captured = capsys.readouterr()
        assert "Login token obtained" in captured.out
    
    def test_get_login_token_failure(self, capsys):
        """Test login token retrieval failure."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = {"query": {"tokens": {}}}  # No login token
            
            with pytest.raises(SystemExit):
                importer.get_login_token()
                
        captured = capsys.readouterr()
        assert "Failed to get login token" in captured.out
    
    def test_get_edit_token_success(self, mock_mediawiki_api_response, capsys):
        """Test successful edit token retrieval."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = mock_mediawiki_api_response['edit_token']
            
            token = importer.get_edit_token()
            
        assert token == "test-edit-token-789"
        
        captured = capsys.readouterr()
        assert "Edit token obtained" in captured.out
    
    def test_get_edit_token_failure(self, capsys):
        """Test edit token retrieval failure."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = {"query": {"tokens": {}}}  # No edit token
            
            with pytest.raises(SystemExit):
                importer.get_edit_token()
                
        captured = capsys.readouterr()
        assert "Failed to get edit token" in captured.out


@pytest.mark.unit
class TestLogin:
    """Test MediaWiki login functionality."""
    
    def test_login_success(self, mock_mediawiki_api_response, capsys):
        """Test successful MediaWiki login."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = mock_mediawiki_api_response['login_success']
            
            result = importer.login("test-login-token")
            
        assert result is True
        
        captured = capsys.readouterr()
        assert "Successfully logged in" in captured.out
    
    def test_login_failure(self, capsys):
        """Test MediaWiki login failure."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        failed_login_response = {
            'login': {
                'result': 'Failed'
            }
        }
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = failed_login_response
            
            result = importer.login("test-login-token")
            
        assert result is False
        
        captured = capsys.readouterr()
        assert "Login failed" in captured.out
        assert "Login result: Failed" in captured.out
    
    def test_login_wrong_result(self, capsys):
        """Test login with unexpected result."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        unexpected_login_response = {
            'login': {
                'result': 'NeedToken'
            }
        }
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = unexpected_login_response
            
            result = importer.login("test-login-token")
            
        assert result is False
        
        captured = capsys.readouterr()
        assert "Login result: NeedToken" in captured.out


@pytest.mark.unit
class TestTemplateImport:
    """Test template import functionality."""
    
    def test_import_template_success(self, mock_mediawiki_api_response, capsys):
        """Test successful template import."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = mock_mediawiki_api_response['edit_success']
            
            result = importer.import_template("TestTemplate", "Template content", "test-token")
            
        assert result is True
        
        captured = capsys.readouterr()
        assert "Importing Template:TestTemplate" in captured.out
        assert "Template:TestTemplate imported successfully" in captured.out
    
    def test_import_template_failure(self, capsys):
        """Test template import failure."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        failed_edit_response = {
            'edit': {
                'result': 'Failure'
            },
            'error': {
                'code': 'permission-denied',
                'info': 'Permission denied'
            }
        }
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = failed_edit_response
            
            result = importer.import_template("FailedTemplate", "Content", "test-token")
            
        assert result is False
        
        captured = capsys.readouterr()
        assert "Failed to import Template:FailedTemplate" in captured.out
        assert "Error: permission-denied" in captured.out
    
    def test_import_template_unknown_error(self, capsys):
        """Test template import with unknown error format."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        unknown_error_response = {
            'edit': {
                'result': 'Failure'
            }
            # No error details
        }
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = unknown_error_response
            
            result = importer.import_template("UnknownErrorTemplate", "Content", "test-token")
            
        assert result is False
        
        captured = capsys.readouterr()
        assert "Error: unknown error" in captured.out


@pytest.mark.unit
class TestTemplateDirectoryImport:
    """Test template directory import functionality."""
    
    def test_import_templates_from_directory_success(self, temp_template_files, mock_mediawiki_api_response, capsys):
        """Test successful import of templates from directory."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch.object(importer, 'import_template') as mock_import_template:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            mock_import_template.return_value = True
            
            success_count, failed_count = importer.import_templates_from_directory(str(temp_template_files))
            
        assert success_count == 2  # InfoBox.mediawiki and CodeBlock.wiki
        assert failed_count == 0
        
        # Verify login flow was called
        mock_get_login_token.assert_called_once()
        mock_login.assert_called_once_with("test-login-token")
        mock_get_edit_token.assert_called_once()
        
        # Verify templates were imported
        assert mock_import_template.call_count == 2
        
        captured = capsys.readouterr()
        assert "Found 2 template files" in captured.out
    
    def test_import_templates_from_directory_missing_dir(self, capsys):
        """Test import from non-existent directory."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with pytest.raises(SystemExit):
            importer.import_templates_from_directory("/nonexistent/directory")
            
        captured = capsys.readouterr()
        assert "Template directory not found" in captured.out
    
    def test_import_templates_from_directory_no_templates(self, temp_directory, capsys):
        """Test import from directory with no template files."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        empty_dir = temp_directory / 'empty'
        empty_dir.mkdir()
        
        success_count, failed_count = importer.import_templates_from_directory(str(empty_dir))
        
        assert success_count == 0
        assert failed_count == 0
        
        captured = capsys.readouterr()
        assert "No template files found" in captured.out
        assert "Template files should have .mediawiki or .wiki extension" in captured.out
    
    def test_import_templates_from_directory_login_failure(self, temp_template_files, capsys):
        """Test import when login fails."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = False  # Login fails
            
            with pytest.raises(SystemExit):
                importer.import_templates_from_directory(str(temp_template_files))
    
    def test_import_templates_from_directory_mixed_results(self, temp_template_files, mock_mediawiki_api_response, capsys):
        """Test import with mixed success/failure results."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch.object(importer, 'import_template') as mock_import_template:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            
            # First template succeeds, second fails
            mock_import_template.side_effect = [True, False]
            
            success_count, failed_count = importer.import_templates_from_directory(str(temp_template_files))
            
        assert success_count == 1
        assert failed_count == 1
    
    def test_import_templates_from_directory_file_read_error(self, temp_directory, capsys):
        """Test import when template file reading fails."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        # Create template directory with a file
        template_dir = temp_directory / 'templates'
        template_dir.mkdir()
        template_file = template_dir / 'ErrorTemplate.mediawiki'
        template_file.write_text("Template content")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch('builtins.open', mock_open()) as mock_file_open:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            mock_file_open.side_effect = Exception("File read error")
            
            success_count, failed_count = importer.import_templates_from_directory(str(template_dir))
            
        assert success_count == 0
        assert failed_count == 1
        
        captured = capsys.readouterr()
        assert "Error processing ErrorTemplate.mediawiki: File read error" in captured.out
    
    def test_import_templates_template_prefix_removal(self, temp_directory):
        """Test that 'Template_' prefix is properly removed from filenames."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        # Create template with Template_ prefix
        template_dir = temp_directory / 'templates'
        template_dir.mkdir()
        template_file = template_dir / 'Template_InfoBox.mediawiki'
        template_file.write_text("InfoBox template content")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch.object(importer, 'import_template') as mock_import_template:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            mock_import_template.return_value = True
            
            success_count, failed_count = importer.import_templates_from_directory(str(template_dir))
            
        # Verify template was imported with prefix removed
        mock_import_template.assert_called_once_with("InfoBox", "InfoBox template content", "test-edit-token")
        assert success_count == 1
        assert failed_count == 0


@pytest.mark.unit
class TestConfigurationLoading:
    """Test configuration loading for template importer."""
    
    def test_load_config_success(self, mock_env_vars):
        """Test successful configuration loading."""
        # Template importer uses different env vars
        template_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD'],
            'TEMPLATE_DIR': 'test-templates'
        }
        
        with patch.dict(os.environ, template_env):
            wiki_url, username, password, template_dir = load_config()
            
        assert wiki_url == "http://localhost:8080"
        assert username == "testuser"
        assert password == "testpass123"
        assert template_dir == "test-templates"
    
    def test_load_config_default_template_dir(self, mock_env_vars):
        """Test configuration loading with default template directory."""
        template_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD']
            # No TEMPLATE_DIR - should use default
        }
        
        with patch.dict(os.environ, template_env, clear=True):
            wiki_url, username, password, template_dir = load_config()
            
        assert template_dir == "internal-wiki/templates"  # Default value
    
    def test_load_config_missing_required(self, capsys):
        """Test configuration loading with missing required variables."""
        partial_env = {
            'WIKI_URL': 'http://localhost:8080',
            'WIKI_USERNAME': 'testuser'
            # Missing WIKI_PASSWORD
        }
        
        with patch.dict(os.environ, partial_env, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
        assert "WIKI_URL" in captured.out
        assert "WIKI_USERNAME" in captured.out
        assert "WIKI_PASSWORD" in captured.out


@pytest.mark.integration
class TestMainFunction:
    """Test main function integration."""
    
    def test_main_success_flow(self, mock_env_vars, temp_template_files, mock_mediawiki_api_response, capsys):
        """Test successful main function execution."""
        template_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD'],
            'TEMPLATE_DIR': str(temp_template_files)
        }
        
        with patch.dict(os.environ, template_env), \
             patch('mediawiki_import.MediaWikiImporter') as mock_importer_class:
            
            mock_importer = mock_importer_class.return_value
            mock_importer.import_templates_from_directory.return_value = (2, 0)  # 2 success, 0 failed
            
            main()
            
        # Verify importer was created with correct parameters
        mock_importer_class.assert_called_once_with("http://localhost:8080", "testuser", "testpass123")
        mock_importer.import_templates_from_directory.assert_called_once_with(str(temp_template_files))
        
        captured = capsys.readouterr()
        assert "Import complete!" in captured.out
        assert "Successfully imported: 2 templates" in captured.out
        assert "Visit your MediaWiki at: http://localhost:8080" in captured.out
    
    def test_main_with_failures(self, mock_env_vars, temp_template_files, capsys):
        """Test main function with some import failures."""
        template_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD'],
            'TEMPLATE_DIR': str(temp_template_files)
        }
        
        with patch.dict(os.environ, template_env), \
             patch('mediawiki_import.MediaWikiImporter') as mock_importer_class:
            
            mock_importer = mock_importer_class.return_value
            mock_importer.import_templates_from_directory.return_value = (1, 1)  # 1 success, 1 failed
            
            main()
            
        captured = capsys.readouterr()
        assert "Successfully imported: 1 templates" in captured.out
        assert "Failed to import: 1 templates" in captured.out
    
    def test_main_configuration_error(self, capsys):
        """Test main function with configuration error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
    
    def test_main_import_error(self, mock_env_vars, capsys):
        """Test main function with import error."""
        template_env = {
            'WIKI_URL': mock_env_vars['WIKI_URL'],
            'WIKI_USERNAME': mock_env_vars['WIKI_USERNAME'],
            'WIKI_PASSWORD': mock_env_vars['WIKI_PASSWORD'],
            'TEMPLATE_DIR': 'test-templates'
        }
        
        with patch.dict(os.environ, template_env), \
             patch('mediawiki_import.MediaWikiImporter', side_effect=Exception("Connection failed")):
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Import failed" in captured.out


@pytest.mark.api
class TestApiEdgeCases:
    """Test API edge cases and error scenarios."""
    
    def test_make_request_all_retries_exhausted(self, capsys):
        """Test API request when all retries are exhausted."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            # All attempts fail with timeout
            mock_post.side_effect = [
                requests.exceptions.Timeout("Timeout 1"),
                requests.exceptions.Timeout("Timeout 2"),
                requests.exceptions.Timeout("Timeout 3")
            ]
            
            with pytest.raises(Exception, match="Request timeout"):
                importer._make_request("POST", action="test")
                
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # No sleep after final attempt
        
        captured = capsys.readouterr()
        assert "API request timed out after 3 attempts" in captured.out
    
    def test_make_request_connection_failure_exhausted(self, capsys):
        """Test API request when connection failures are exhausted."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post:
            mock_post.side_effect = [
                requests.exceptions.ConnectionError("Conn 1"),
                requests.exceptions.ConnectionError("Conn 2"),
                requests.exceptions.ConnectionError("Conn 3")
            ]
            
            with pytest.raises(Exception, match="Connection failed"):
                importer._make_request("POST", action="test")
                
        captured = capsys.readouterr()
        assert "API connection failed" in captured.out
        assert "Check MediaWiki URL and network connectivity" in captured.out
    
    def test_make_request_http_error_403(self, capsys):
        """Test API request with 403 Forbidden error."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        with patch.object(importer.session, 'post') as mock_post:
            forbidden_response = MagicMock()
            forbidden_response.status_code = 403
            forbidden_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=forbidden_response)
            mock_post.return_value = forbidden_response
            
            with pytest.raises(Exception, match="HTTP error: 403"):
                importer._make_request("POST", action="test")
                
        captured = capsys.readouterr()
        assert "API request failed" in captured.out
    
    def test_import_template_with_special_characters(self, mock_mediawiki_api_response):
        """Test template import with special characters in content."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        special_content = """<div class="special-template">
{{{{1|Default value with "quotes" and 'apostrophes'}}}}
<!-- Template comment with Unicode: 🚀 ✨ -->
{| class="wikitable"
|-
! Header with | pipe
|-
| Data & more
|}
</div>"""
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = mock_mediawiki_api_response['edit_success']
            
            result = importer.import_template("SpecialTemplate", special_content, "test-token")
            
        assert result is True
        
        # Verify the content was passed correctly
        call_args = mock_request.call_args[1]
        assert call_args['text'] == special_content
        assert call_args['title'] == "Template:SpecialTemplate"


@pytest.mark.slow
class TestPerformanceAndLargeTemplates:
    """Test performance with large template sets."""
    
    def test_import_large_template_set(self, temp_directory, capsys):
        """Test importing a large set of templates."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        # Create a large number of template files
        template_dir = temp_directory / 'large_templates'
        template_dir.mkdir()
        
        for i in range(50):
            template_file = template_dir / f'Template{i:02d}.mediawiki'
            template_content = f"= Template {i} =\n\nThis is template number {i}.\n\n{{{{1|default{i}}}}}"
            template_file.write_text(template_content)
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch.object(importer, 'import_template') as mock_import_template:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            mock_import_template.return_value = True
            
            success_count, failed_count = importer.import_templates_from_directory(str(template_dir))
            
        assert success_count == 50
        assert failed_count == 0
        assert mock_import_template.call_count == 50
        
        captured = capsys.readouterr()
        assert "Found 50 template files" in captured.out
    
    def test_import_very_large_template_content(self):
        """Test importing a template with very large content."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        # Create a very large template (simulating a complex template)
        large_content_parts = [
            "{{#switch: {{{type|info}}}",
            "| info = <div class='infobox'>",
            "| warning = <div class='warningbox'>",
            "| error = <div class='errorbox'>"
        ]
        
        # Add many template parameters
        for i in range(100):
            large_content_parts.append(f"| param{i} = {{{{param{i}|default{i}}}}}")
        
        large_content_parts.extend([
            "}}</div>",
            "[[Category:Templates]]"
        ])
        
        large_content = '\n'.join(large_content_parts)
        
        with patch.object(importer, '_make_request') as mock_request:
            mock_request.return_value = {'edit': {'result': 'Success'}}
            
            result = importer.import_template("LargeTemplate", large_content, "test-token")
            
        assert result is True
        
        # Verify content was handled correctly
        call_args = mock_request.call_args[1]
        assert len(call_args['text']) > 1000  # Should be large
        assert 'param50' in call_args['text']  # Should contain generated params


@pytest.mark.unit
class TestFileHandling:
    """Test template file handling edge cases."""
    
    def test_import_templates_mixed_file_extensions(self, temp_directory):
        """Test importing templates with mixed file extensions."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        template_dir = temp_directory / 'mixed_templates'
        template_dir.mkdir()
        
        # Create files with different extensions
        (template_dir / 'Template1.mediawiki').write_text("MediaWiki template")
        (template_dir / 'Template2.wiki').write_text("Wiki template")
        (template_dir / 'Template3.txt').write_text("Text file (should be ignored)")
        (template_dir / 'README.md').write_text("Readme file (should be ignored)")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch.object(importer, 'import_template') as mock_import_template:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            mock_import_template.return_value = True
            
            success_count, failed_count = importer.import_templates_from_directory(str(template_dir))
            
        assert success_count == 2  # Only .mediawiki and .wiki files
        assert failed_count == 0
        assert mock_import_template.call_count == 2
    
    def test_import_templates_empty_files(self, temp_directory, capsys):
        """Test importing empty template files."""
        importer = MediaWikiImporter("http://localhost:8080", "testuser", "testpass")
        
        template_dir = temp_directory / 'empty_templates'
        template_dir.mkdir()
        
        # Create empty and non-empty files
        (template_dir / 'EmptyTemplate.mediawiki').write_text("")
        (template_dir / 'ValidTemplate.mediawiki').write_text("Valid content")
        
        with patch.object(importer, 'get_login_token') as mock_get_login_token, \
             patch.object(importer, 'login') as mock_login, \
             patch.object(importer, 'get_edit_token') as mock_get_edit_token, \
             patch.object(importer, 'import_template') as mock_import_template:
            
            mock_get_login_token.return_value = "test-login-token"
            mock_login.return_value = True
            mock_get_edit_token.return_value = "test-edit-token"
            mock_import_template.return_value = True
            
            success_count, failed_count = importer.import_templates_from_directory(str(template_dir))
            
        assert success_count == 2  # Both files processed (empty is still valid)
        assert failed_count == 0
        
        # Verify empty content was handled
        import_calls = mock_import_template.call_args_list
        empty_call = next((call for call in import_calls if call[0][1] == ""), None)
        valid_call = next((call for call in import_calls if call[0][1] == "Valid content"), None)
        
        assert empty_call is not None
        assert valid_call is not None


if __name__ == '__main__':
    pytest.main([__file__])