#!/usr/bin/env python3
"""
Tests for getting_started.py - Interactive setup and tool selection guide.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open, call
from io import StringIO

import pytest

# Add the project root to the path so we can import getting_started
sys.path.insert(0, str(Path(__file__).parent.parent))
import getting_started


@pytest.mark.unit
class TestPlatformInfo:
    """Test platform information detection and display."""
    
    def test_show_platform_info_windows_git_bash(self, capsys, monkeypatch):
        """Test platform info display for Windows Git Bash environment."""
        monkeypatch.setattr(platform, 'system', lambda: 'Windows')
        monkeypatch.setattr(platform, 'release', lambda: '10')
        monkeypatch.setattr(sys, 'version', '3.9.0 (default, Oct  9 2020, 15:07:54)')
        monkeypatch.setattr(sys, 'executable', r'C:\Python39\python.exe')
        monkeypatch.setenv('SHELL', '/usr/bin/bash')
        monkeypatch.setenv('MSYSTEM', 'MINGW64')
        
        getting_started.show_platform_info()
        
        captured = capsys.readouterr()
        assert "Windows 10" in captured.out
        assert "Python: 3.9.0" in captured.out
        assert "Git Bash Environment:" in captured.out
        assert "Unix-like commands available" in captured.out
    
    def test_show_platform_info_windows_cmd(self, capsys, monkeypatch):
        """Test platform info display for Windows Command Prompt."""
        monkeypatch.setattr(platform, 'system', lambda: 'Windows')
        monkeypatch.setattr(platform, 'release', lambda: '11')
        monkeypatch.setenv('COMSPEC', r'C:\Windows\system32\cmd.exe')
        monkeypatch.delenv('SHELL', raising=False)
        monkeypatch.delenv('MSYSTEM', raising=False)
        
        getting_started.show_platform_info()
        
        captured = capsys.readouterr()
        assert "Windows 11" in captured.out
        assert "Windows Tips:" in captured.out
        assert "Consider using Git Bash" in captured.out
    
    def test_show_platform_info_macos(self, capsys, monkeypatch):
        """Test platform info display for macOS."""
        monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
        monkeypatch.setattr(platform, 'release', lambda: '21.6.0')
        monkeypatch.setenv('SHELL', '/bin/zsh')
        
        getting_started.show_platform_info()
        
        captured = capsys.readouterr()
        assert "Darwin 21.6.0" in captured.out
        assert "macOS Tips:" in captured.out
        assert "Use Terminal or iTerm2" in captured.out
    
    def test_show_platform_info_linux(self, capsys, monkeypatch):
        """Test platform info display for Linux."""
        monkeypatch.setattr(platform, 'system', lambda: 'Linux')
        monkeypatch.setattr(platform, 'release', lambda: '5.15.0')
        monkeypatch.setenv('SHELL', '/bin/bash')
        
        getting_started.show_platform_info()
        
        captured = capsys.readouterr()
        assert "Linux 5.15.0" in captured.out
        assert "Linux Tips:" in captured.out
        assert "docker and docker-compose" in captured.out


@pytest.mark.unit
class TestToolkitEnvironment:
    """Test toolkit environment file creation and loading."""
    
    def test_create_toolkit_environment_success(self, temp_directory, monkeypatch):
        """Test successful creation of toolkit environment file."""
        monkeypatch.chdir(temp_directory)
        monkeypatch.setattr(sys, 'executable', '/usr/bin/python3')
        monkeypatch.setenv('SHELL', '/bin/bash')
        monkeypatch.setattr('platform.system', lambda: 'Linux')
        
        result = getting_started.create_toolkit_environment()
        
        assert result is True
        toolkit_env = temp_directory / '.toolkit_env'
        assert toolkit_env.exists()
        
        content = toolkit_env.read_text()
        assert 'TOOLKIT_PYTHON_EXECUTABLE=/usr/bin/python3' in content
        assert 'TOOLKIT_OS=Linux' in content
        assert 'TOOLKIT_SHELL=/bin/bash' in content
    
    def test_create_toolkit_environment_already_exists(self, temp_directory, monkeypatch, capsys):
        """Test when toolkit environment file already exists."""
        monkeypatch.chdir(temp_directory)
        
        # Create existing file
        toolkit_env = temp_directory / '.toolkit_env'
        toolkit_env.write_text("existing content")
        
        result = getting_started.create_toolkit_environment()
        
        assert result is True
        captured = capsys.readouterr()
        assert "already exists" in captured.out
    
    def test_create_toolkit_environment_permission_error(self, temp_directory, monkeypatch):
        """Test toolkit environment creation with permission error."""
        monkeypatch.chdir(temp_directory)
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = getting_started.create_toolkit_environment()
            
        assert result is False
    
    def test_load_toolkit_environment_success(self, temp_directory, monkeypatch):
        """Test successful loading of toolkit environment."""
        monkeypatch.chdir(temp_directory)
        
        # Create env file with test content
        toolkit_env = temp_directory / '.toolkit_env'
        toolkit_env.write_text("""# Test Environment
TOOLKIT_PYTHON_EXECUTABLE=/usr/bin/python3
TOOLKIT_OS=Linux
TOOLKIT_SHELL=/bin/bash
# Comment line
EMPTY_VALUE=
""")
        
        env_vars = getting_started.load_toolkit_environment()
        
        assert env_vars['TOOLKIT_PYTHON_EXECUTABLE'] == '/usr/bin/python3'
        assert env_vars['TOOLKIT_OS'] == 'Linux'
        assert env_vars['TOOLKIT_SHELL'] == '/bin/bash'
        assert 'EMPTY_VALUE' in env_vars
        assert env_vars['EMPTY_VALUE'] == ''
    
    def test_load_toolkit_environment_missing_file(self, temp_directory, monkeypatch):
        """Test loading when toolkit environment file is missing."""
        monkeypatch.chdir(temp_directory)
        
        env_vars = getting_started.load_toolkit_environment()
        
        assert env_vars == {}
    
    def test_load_toolkit_environment_permission_error(self, temp_directory, monkeypatch, capsys):
        """Test loading with permission error."""
        monkeypatch.chdir(temp_directory)
        
        # Create file but mock permission error
        toolkit_env = temp_directory / '.toolkit_env'
        toolkit_env.write_text("test content")
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            env_vars = getting_started.load_toolkit_environment()
            
        assert env_vars == {}
        captured = capsys.readouterr()
        assert "Permission denied" in captured.out


@pytest.mark.unit  
class TestPythonExecutable:
    """Test Python executable detection."""
    
    def test_get_python_executable_from_toolkit_env(self, temp_directory, monkeypatch):
        """Test getting Python executable from toolkit environment."""
        monkeypatch.chdir(temp_directory)
        
        # Create toolkit env with Python executable
        toolkit_env = temp_directory / '.toolkit_env'
        toolkit_env.write_text("TOOLKIT_PYTHON_EXECUTABLE=/custom/python3")
        
        # Mock the path existence check
        with patch('pathlib.Path.exists', return_value=True):
            python_exec = getting_started.get_python_executable()
            
        assert python_exec == '/custom/python3'
    
    def test_get_python_executable_current_interpreter(self, monkeypatch):
        """Test getting current Python interpreter as fallback."""
        monkeypatch.setattr(sys, 'executable', '/usr/bin/python3.9')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('getting_started.load_toolkit_environment', return_value={}):
            python_exec = getting_started.get_python_executable()
            
        assert python_exec == '/usr/bin/python3.9'
    
    def test_get_python_executable_command_search(self, monkeypatch):
        """Test Python executable search via subprocess."""
        with patch('getting_started.load_toolkit_environment', return_value={}), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('subprocess.run') as mock_run:
            
            # Mock successful python3 command
            mock_run.return_value = MagicMock(returncode=0)
            
            python_exec = getting_started.get_python_executable()
            
        assert python_exec == 'python3'
        mock_run.assert_called_once_with(['python3', '--version'],
                                        capture_output=True, text=True, timeout=5)
    
    def test_get_python_executable_fallback(self, monkeypatch):
        """Test fallback to 'python' when all else fails."""
        with patch('getting_started.load_toolkit_environment', return_value={}), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('subprocess.run', side_effect=FileNotFoundError()):
            
            python_exec = getting_started.get_python_executable()
            
        assert python_exec == 'python'


@pytest.mark.unit
class TestScriptExecution:
    """Test Python script execution functionality."""
    
    def test_run_python_script_success(self, temp_directory, monkeypatch):
        """Test successful Python script execution."""
        monkeypatch.chdir(temp_directory)
        
        # Create a test script
        test_script = temp_directory / 'test_script.py'
        test_script.write_text('print("Hello, World!")')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = getting_started.run_python_script('test_script.py')
            
        assert result is True
        mock_run.assert_called_once()
    
    def test_run_python_script_with_working_dir(self, temp_directory):
        """Test script execution with working directory."""
        # Create working directory and script
        work_dir = temp_directory / 'work'
        work_dir.mkdir()
        test_script = work_dir / 'script.py'
        test_script.write_text('print("Test")')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = getting_started.run_python_script('script.py', str(work_dir))
            
        assert result is True
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert kwargs['cwd'] == str(work_dir)
    
    def test_run_python_script_missing_script(self, temp_directory, monkeypatch, capsys):
        """Test execution when script file is missing."""
        monkeypatch.chdir(temp_directory)
        
        result = getting_started.run_python_script('nonexistent.py')
        
        assert result is False
        captured = capsys.readouterr()
        assert "Script not found" in captured.out
    
    def test_run_python_script_missing_working_dir(self, capsys):
        """Test execution when working directory is missing."""
        result = getting_started.run_python_script('script.py', '/nonexistent/dir')
        
        assert result is False
        captured = capsys.readouterr()
        assert "Working directory not found" in captured.out
    
    def test_run_python_script_execution_failure(self, temp_directory, monkeypatch):
        """Test script execution failure."""
        monkeypatch.chdir(temp_directory)
        
        # Create test script
        test_script = temp_directory / 'failing_script.py'
        test_script.write_text('import sys; sys.exit(1)')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            
            result = getting_started.run_python_script('failing_script.py')
            
        assert result is False


@pytest.mark.unit
class TestDockerCompose:
    """Test Docker Compose functionality."""
    
    def test_run_docker_compose_success(self, temp_directory):
        """Test successful Docker Compose execution."""
        # Create docker-compose.yml
        compose_file = temp_directory / 'docker-compose.yml'
        compose_file.write_text("""
version: '3.8'
services:
  test:
    image: hello-world
""")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = getting_started.run_docker_compose(str(temp_directory), 'up -d')
            
        assert result is True
        mock_run.assert_called_once()
    
    def test_run_docker_compose_v2_fallback(self, temp_directory):
        """Test Docker Compose V2 to V1 fallback."""
        with patch('subprocess.run') as mock_run:
            # First call fails (V2), second succeeds (V1)
            mock_run.side_effect = [
                MagicMock(returncode=1),  # docker compose fails
                MagicMock(returncode=0)   # docker-compose succeeds
            ]
            
            result = getting_started.run_docker_compose(str(temp_directory), 'up -d')
            
        assert result is True
        assert mock_run.call_count == 2
    
    def test_run_docker_compose_missing_dir(self, capsys):
        """Test Docker Compose with missing directory."""
        result = getting_started.run_docker_compose('/nonexistent/dir', 'up -d')
        
        assert result is False
        captured = capsys.readouterr()
        assert "Working directory not found" in captured.out
    
    def test_run_docker_compose_not_found(self, temp_directory, capsys):
        """Test when Docker Compose is not installed."""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = getting_started.run_docker_compose(str(temp_directory), 'up -d')
            
        assert result is False
        captured = capsys.readouterr()
        assert "Docker Compose not found" in captured.out


@pytest.mark.unit
class TestEnvironmentSetup:
    """Test environment configuration setup."""
    
    def test_setup_environment_success(self, temp_directory, monkeypatch, capsys):
        """Test successful environment setup."""
        monkeypatch.chdir(temp_directory)
        
        # Create migration directory and template
        migration_dir = temp_directory / 'migration'
        migration_dir.mkdir()
        
        template_file = migration_dir / '.env.template'
        template_file.write_text("""# Environment Template
AZURE_DEVOPS_ORGANIZATION=your_organization_here
AZURE_DEVOPS_PROJECT=your_project_here
AZURE_DEVOPS_PAT=your_token_here
""")
        
        result = getting_started.setup_environment()
        
        assert result is True
        
        env_file = migration_dir / '.env'
        assert env_file.exists()
        assert env_file.read_text() == template_file.read_text()
        
        captured = capsys.readouterr()
        assert "Environment template copied" in captured.out
    
    def test_setup_environment_file_exists_overwrite(self, temp_directory, monkeypatch):
        """Test environment setup when file exists and user chooses to overwrite."""
        monkeypatch.chdir(temp_directory)
        
        migration_dir = temp_directory / 'migration'
        migration_dir.mkdir()
        
        # Create template and existing env file
        template_file = migration_dir / '.env.template'
        template_file.write_text("NEW_CONTENT=true")
        
        env_file = migration_dir / '.env'
        env_file.write_text("OLD_CONTENT=true")
        
        with patch('builtins.input', return_value='y'):
            result = getting_started.setup_environment()
            
        assert result is True
        assert "NEW_CONTENT=true" in env_file.read_text()
    
    def test_setup_environment_file_exists_keep(self, temp_directory, monkeypatch, capsys):
        """Test environment setup when file exists and user chooses to keep it."""
        monkeypatch.chdir(temp_directory)
        
        migration_dir = temp_directory / 'migration'
        migration_dir.mkdir()
        
        template_file = migration_dir / '.env.template'
        template_file.write_text("NEW_CONTENT=true")
        
        env_file = migration_dir / '.env'
        env_file.write_text("OLD_CONTENT=true")
        
        with patch('builtins.input', return_value='n'):
            result = getting_started.setup_environment()
            
        assert result is True
        assert "OLD_CONTENT=true" in env_file.read_text()
        
        captured = capsys.readouterr()
        assert "Using existing environment file" in captured.out
    
    def test_setup_environment_missing_template(self, temp_directory, monkeypatch, capsys):
        """Test environment setup when template is missing."""
        monkeypatch.chdir(temp_directory)
        
        result = getting_started.setup_environment()
        
        assert result is False
        captured = capsys.readouterr()
        assert "Environment template not found" in captured.out


@pytest.mark.unit
class TestDependencyChecking:
    """Test dependency checking functionality."""
    
    def test_check_python_version_success(self, monkeypatch, capsys):
        """Test successful Python version check."""
        monkeypatch.setattr(sys, 'version_info', (3, 9, 0))
        
        getting_started.check_python_version()
        
        captured = capsys.readouterr()
        assert "Python version check passed" in captured.out
    
    def test_check_python_version_failure(self, monkeypatch):
        """Test Python version check failure."""
        monkeypatch.setattr(sys, 'version_info', (3, 6, 0))
        
        with pytest.raises(SystemExit):
            getting_started.check_python_version()
    
    def test_check_dependencies_success(self, capsys):
        """Test successful dependency check."""
        with patch.dict('sys.modules', {'requests': MagicMock(), 'dotenv': MagicMock()}):
            result = getting_started.check_dependencies()
            
        assert result is True
        captured = capsys.readouterr()
        assert "requests package found" in captured.out
        assert "python-dotenv package found" in captured.out
    
    def test_check_dependencies_missing_requests(self, capsys):
        """Test dependency check with missing requests."""
        with patch.dict('sys.modules', {'dotenv': MagicMock()}), \
             patch('builtins.__import__', side_effect=lambda name, *args: 
                   MagicMock() if name == 'dotenv' else ImportError()):
            
            result = getting_started.check_dependencies()
            
        assert result is False
        captured = capsys.readouterr()
        assert "requests package not found" in captured.out


@pytest.mark.integration  
class TestUserInteractionFlows:
    """Test user interaction and menu flows."""
    
    def test_handle_migration_setup_full_flow(self, temp_directory, monkeypatch):
        """Test complete migration setup flow."""
        monkeypatch.chdir(temp_directory)
        
        # Create required directory structure
        migration_dir = temp_directory / 'migration'
        migration_dir.mkdir()
        
        template_file = migration_dir / '.env.template'
        template_file.write_text("AZURE_DEVOPS_ORGANIZATION=test")
        
        with patch('getting_started.check_dependencies', return_value=True), \
             patch('getting_started.run_analysis'), \
             patch('builtins.input', return_value='n'):  # Don't run analysis
            
            getting_started.handle_migration_setup()
            
        # Verify environment file was created
        env_file = migration_dir / '.env'
        assert env_file.exists()
    
    def test_handle_dev_environment_start(self, temp_directory, monkeypatch):
        """Test development environment startup."""
        monkeypatch.chdir(temp_directory)
        
        # Create examples directory with docker-compose.yml
        examples_dir = temp_directory / 'examples'
        examples_dir.mkdir()
        
        compose_file = examples_dir / 'docker-compose.yml'
        compose_file.write_text("version: '3.8'\nservices:\n  test:\n    image: hello-world")
        
        with patch('builtins.input', return_value='y'), \
             patch('getting_started.run_docker_compose', return_value=True) as mock_docker:
            
            getting_started.handle_dev_environment()
            
        mock_docker.assert_called_once_with('examples', 'up -d')


@pytest.mark.cli
class TestCLIIntegration:
    """Test command-line interface integration."""
    
    def test_open_url_cross_platform_macos(self):
        """Test URL opening on macOS."""
        with patch('platform.system', return_value='Darwin'), \
             patch('subprocess.run') as mock_run:
            
            result = getting_started.open_url_cross_platform('https://example.com')
            
        assert result is True
        mock_run.assert_called_once_with(['open', 'https://example.com'])
    
    def test_open_url_cross_platform_windows(self):
        """Test URL opening on Windows."""
        with patch('platform.system', return_value='Windows'), \
             patch('subprocess.run') as mock_run:
            
            result = getting_started.open_url_cross_platform('https://example.com')
            
        assert result is True
        mock_run.assert_called_once_with(['start', 'https://example.com'], shell=True)
    
    def test_open_url_cross_platform_linux(self):
        """Test URL opening on Linux."""
        with patch('platform.system', return_value='Linux'), \
             patch('subprocess.run') as mock_run:
            
            result = getting_started.open_url_cross_platform('https://example.com')
            
        assert result is True
        mock_run.assert_called_once_with(['xdg-open', 'https://example.com'])
    
    def test_open_url_cross_platform_failure(self, capsys):
        """Test URL opening failure handling."""
        with patch('platform.system', return_value='Linux'), \
             patch('subprocess.run', side_effect=Exception("Command failed")):
            
            result = getting_started.open_url_cross_platform('https://example.com')
            
        assert result is False
        captured = capsys.readouterr()
        assert "Could not open URL automatically" in captured.out
        assert "https://example.com" in captured.out


@pytest.mark.unit
class TestFileOperations:
    """Test file and directory operations."""
    
    def test_display_readme_content_pagination(self, temp_directory, monkeypatch):
        """Test README content display with pagination."""
        readme_file = temp_directory / 'README.md'
        
        # Create content that will require pagination
        lines = ['# Test README'] + [f'Line {i}' for i in range(1, 100)]
        readme_file.write_text('\n'.join(lines))
        
        monkeypatch.chdir(temp_directory)
        
        with patch('builtins.input', side_effect=['', 'q']):  # Next page, then quit
            getting_started.display_readme_content(readme_file)
    
    def test_display_readme_content_missing_file(self, temp_directory, capsys):
        """Test README display with missing file."""
        missing_file = temp_directory / 'missing.md'
        
        getting_started.display_readme_content(missing_file)
        
        captured = capsys.readouterr()
        assert "File not found" in captured.out
    
    def test_handle_readme_files_empty_list(self, temp_directory, monkeypatch, capsys):
        """Test README handling when no files found."""
        monkeypatch.chdir(temp_directory)
        
        getting_started.handle_readme_files()
        
        captured = capsys.readouterr()
        assert "No README files found" in captured.out


@pytest.mark.slow
class TestMainWorkflow:
    """Test main application workflow."""
    
    def test_main_workflow_exit(self, temp_directory, monkeypatch):
        """Test main workflow with immediate exit."""
        monkeypatch.chdir(temp_directory)
        monkeypatch.setattr(sys, 'version_info', (3, 9, 0))
        
        with patch('builtins.input', return_value='0'):  # Exit immediately
            getting_started.main()
    
    def test_main_workflow_invalid_choice(self, temp_directory, monkeypatch, capsys):
        """Test main workflow with invalid menu choice."""
        monkeypatch.chdir(temp_directory)
        monkeypatch.setattr(sys, 'version_info', (3, 9, 0))
        
        with patch('builtins.input', side_effect=['9', '0']):  # Invalid choice, then exit
            getting_started.main()
            
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out


if __name__ == '__main__':
    pytest.main([__file__])