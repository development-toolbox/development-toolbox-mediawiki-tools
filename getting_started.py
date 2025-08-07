#!/usr/bin/env python3
"""
Getting Started Script for MediaWiki Development Toolkit
Interactive setup and tool selection guide

Author: Johan Sörell
Contact: https://github.com/J-SirL | https://se.linkedin.com/in/johansorell | automationblueprint.site
Date: 2025
Version: 1.0.0
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def show_platform_info():
    """Show platform-specific information"""
    system = platform.system()
    shell = os.environ.get('SHELL') or os.environ.get('COMSPEC') or 'unknown'

    print(f"🖥️  Detected OS: {system} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"🐚 Shell: {Path(shell).name if shell != 'unknown' else 'unknown'}")

    # Detect if running in Git Bash on Windows
    msystem = os.environ.get('MSYSTEM', '')
    if system == "Windows" and ("bash" in shell.lower() or "MSYS" in msystem):
        print("💡 Git Bash Environment:")
        print("   • Excellent choice for cross-platform development!")
        print("   • Unix-like commands available")
        print("   • Docker commands work normally")
        print("   • Interactive programs work seamlessly")
    elif system == "Windows":
        print("💡 Windows Tips:")
        print("   • Consider using Git Bash for better terminal experience")
        print("   • PowerShell and Command Prompt also supported")
        print("   • Docker Desktop required for local environment")
    elif system == "Darwin":
        print("💡 macOS Tips:")
        print("   • Use Terminal or iTerm2")
        print("   • Install Homebrew for package management")
        print("   • Docker Desktop available in App Store")
    else:
        print("💡 Linux Tips:")
        print("   • Most distributions supported")
        print("   • Install docker and docker-compose via package manager")
        print("   • May need to add user to docker group")
    print()

def print_banner():
    """Print welcome banner"""
    print("🚀 MediaWiki Development Toolkit - Getting Started")
    print("=" * 60)
    print("This toolkit provides multiple tools for MediaWiki development.")
    print("Choose what you'd like to do from the menu below.")
    print()

def create_toolkit_environment():
    """Create a toolkit-specific environment file to avoid system conflicts"""
    toolkit_env = Path(".toolkit_env")

    if toolkit_env.exists():
        print("✅ Toolkit environment file already exists")
        return True

    env_content = f"""# MediaWiki Development Toolkit Environment
# This file configures the toolkit without affecting your system

# Python Configuration
TOOLKIT_PYTHON_EXECUTABLE={sys.executable}
TOOLKIT_PYTHON_VERSION={sys.version.split()[0]}

# Shell Configuration
TOOLKIT_SHELL={os.environ.get('SHELL') or os.environ.get('COMSPEC') or 'unknown'}
TOOLKIT_OS={platform.system()}

# Docker Configuration
TOOLKIT_DOCKER_COMPOSE_CMD=auto

# Git Configuration
TOOLKIT_GIT_BASH={str("bash" in (os.environ.get('SHELL') or '').lower() or "MSYS" in (os.environ.get('MSYSTEM') or '')).lower()}

# Paths (customize these as needed)
TOOLKIT_WORK_DIR={Path.cwd()}
TOOLKIT_MIGRATION_DIR={Path.cwd() / 'migration'}
TOOLKIT_DOCS_DIR={Path.cwd() / 'docs'}
TOOLKIT_EXAMPLES_DIR={Path.cwd() / 'examples'}
"""

    try:
        # Check parent directory exists and is writable
        parent_dir = toolkit_env.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            
        # Check if we have write permissions
        if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
            print(f"❌ No write permission to directory: {parent_dir}")
            return False
            
        with open(toolkit_env, 'w', encoding='utf-8') as f:
            f.write(env_content)
            f.flush()  # Ensure data is written
            
        print("✅ Created toolkit environment file (.toolkit_env)")
        print("📝 You can customize settings in .toolkit_env if needed")
        return True
        
    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {toolkit_env}")
        print("💡 Try running with administrator privileges or choose a different directory")
        return False
    except OSError as e:
        if e.errno == 28:  # No space left on device
            print("❌ Insufficient disk space to create toolkit environment file")
        else:
            print(f"❌ System error creating toolkit environment: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error creating toolkit environment: {e}")
        print("💡 Please check file permissions and available disk space")
        return False

def load_toolkit_environment():
    """Load toolkit environment settings"""
    toolkit_env = Path(".toolkit_env")
    if not toolkit_env.exists():
        return {}

    env_vars = {}
    try:
        with open(toolkit_env, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                    
    except FileNotFoundError:
        print("ℹ️  No toolkit environment file found, using defaults")
    except PermissionError:
        print("⚠️  Permission denied reading toolkit environment file")
    except UnicodeDecodeError:
        print("⚠️  Toolkit environment file has invalid encoding, using defaults")
    except Exception as e:
        print(f"⚠️  Could not load toolkit environment: {e}")
        print("💡 You can recreate the file by running the setup again")

    return env_vars

def get_python_executable():
    """Get the correct Python executable for the current platform"""
    # First try toolkit environment
    toolkit_env = load_toolkit_environment()
    if 'TOOLKIT_PYTHON_EXECUTABLE' in toolkit_env:
        python_exec = toolkit_env['TOOLKIT_PYTHON_EXECUTABLE']
        if Path(python_exec).exists():
            return python_exec

    # Try to use the same Python executable that's running this script
    python_exec = sys.executable
    if python_exec and Path(python_exec).exists():
        return python_exec

    # Fallback to common Python command names
    python_commands = ['python3', 'python']
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return cmd
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return 'python'  # Last resort fallback

def run_python_script(script_path, working_dir=None):
    """Run a Python script in a cross-platform way"""
    python_exec = get_python_executable()
    script_path = Path(script_path)

    if working_dir:
        working_dir = Path(working_dir)
        if not working_dir.exists():
            print(f"❌ Working directory not found: {working_dir}")
            return False
        script_full_path = working_dir / script_path
    else:
        script_full_path = script_path

    if not script_full_path.exists():
        print(f"❌ Script not found: {script_full_path}")
        return False

    try:
        # Use the full path to Python executable for Git Bash compatibility
        cmd = [python_exec, str(script_path)]
        print(f"🐍 Running: {python_exec} {script_path}")

        result = subprocess.run(cmd,
                              cwd=str(working_dir) if working_dir else None,
                              check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run script: {e}")
        print(f"🔧 Python executable: {python_exec}")
        print(f"🔧 Script path: {script_path}")
        print(f"🔧 Working dir: {working_dir}")
        return False

def run_docker_compose(working_dir, command="up -d"):
    """Run docker-compose command in a cross-platform way"""
    working_dir = Path(working_dir)
    if not working_dir.exists():
        print(f"❌ Working directory not found: {working_dir}")
        return False

    # Check toolkit environment for preferred docker command
    toolkit_env = load_toolkit_environment()
    docker_cmd_pref = toolkit_env.get('TOOLKIT_DOCKER_COMPOSE_CMD', 'auto')

    # Try different docker-compose command variations
    if docker_cmd_pref == 'docker-compose':
        docker_commands = [['docker-compose'] + command.split()]
    elif docker_cmd_pref == 'docker_compose':
        docker_commands = [['docker', 'compose'] + command.split()]
    else:  # auto detection
        docker_commands = [
            ['docker', 'compose'] + command.split(),  # Docker Compose V2
            ['docker-compose'] + command.split()      # Docker Compose V1
        ]

    for cmd in docker_commands:
        try:
            print(f"🐳 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=str(working_dir), check=False)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            continue

    print("❌ Docker Compose not found. Please install Docker Desktop.")
    print("💡 Git Bash users: Docker commands should work normally")
    return False

def open_url_cross_platform(url):
    """Open URL in default browser cross-platform"""
    try:
        if platform.system() == "Darwin":      # macOS
            subprocess.run(["open", url])
        elif platform.system() == "Windows":   # Windows
            subprocess.run(["start", url], shell=True)
        else:                                  # Linux and others
            subprocess.run(["xdg-open", url])
        return True
    except Exception as e:
        print(f"❌ Could not open URL automatically: {e}")
        print(f"🌐 Please open manually: {url}")
        return False

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required. You have:", sys.version)
        sys.exit(1)
    print("✅ Python version check passed")

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import requests
        print("✅ requests package found")
    except ImportError:
        print("❌ requests package not found")
        print("📦 Install with: pip install -r migration/requirements.txt")
        return False

    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv package found")
    except ImportError:
        print("❌ python-dotenv package not found")
        print("📦 Install with: pip install -r migration/requirements.txt")
        return False

    return True

def setup_environment():
    """Set up environment configuration"""
    env_template = Path("migration/.env.template")
    env_file = Path("migration/.env")

    if not env_template.exists():
        print("❌ Environment template not found at migration/.env.template")
        return False

    if env_file.exists():
        print("⚠️  Environment file already exists at migration/.env")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("✅ Using existing environment file")
            return True

    try:
        # Ensure destination directory exists
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check source file exists and is readable
        if not env_template.is_file():
            print(f"❌ Template file not found: {env_template}")
            return False
            
        # Check destination is writable
        if env_file.parent.exists() and not os.access(env_file.parent, os.W_OK):
            print(f"❌ No write permission to directory: {env_file.parent}")
            return False
            
        shutil.copy2(env_template, env_file)  # copy2 preserves metadata
        print("✅ Environment template copied to migration/.env")
        print("📝 Please edit migration/.env with your credentials")
        return True
        
    except PermissionError:
        print(f"❌ Permission denied: Cannot copy to {env_file}")
        print("💡 Try running with appropriate permissions")
        return False
    except shutil.SameFileError:
        print("⚠️  Source and destination are the same file")
        return True  # File already exists in correct location
    except OSError as e:
        if e.errno == 28:  # No space left on device
            print("❌ Insufficient disk space to copy environment template")
        else:
            print(f"❌ System error copying environment template: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error copying environment template: {e}")
        print(f"💡 Try manually copying {env_template} to {env_file}")
        return False

def run_analysis():
    """Run migration analysis"""
    print("\n🔍 Running Migration Analysis...")
    print("This will analyze your Azure DevOps wiki and generate a report.")

    response = input("Do you want to run the analysis now? (Y/n): ")
    if response.lower() == 'n':
        print("ℹ️  You can run analysis later with: python migration/migration_planner.py")
        return

    # Check if .env is configured
    env_file = Path("migration/.env")
    if not env_file.exists():
        print("❌ Environment file not found. Please run setup first.")
        return

    # Check if required variables are set
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "your_organization_here" in content or "your_token_here" in content:
                print("❌ Please configure your credentials in migration/.env first")
                print("📝 Edit the file and replace placeholder values with your actual credentials")
                return
                
    except FileNotFoundError:
        print("❌ Environment file not found. Please run setup first.")
        return
    except PermissionError:
        print("❌ Permission denied reading environment file")
        return
    except UnicodeDecodeError:
        print("❌ Environment file has invalid encoding")
        print("💡 Please recreate the .env file with UTF-8 encoding")
        return
    except Exception as e:
        print(f"❌ Error reading environment file: {e}")
        return

    try:
        print("🚀 Starting migration analysis...")
        success = run_python_script("migration_planner.py", "migration")
        if success:
            print("✅ Analysis complete! Check migration_analysis_report.md for results.")
        else:
            print("❌ Analysis failed. Please check the error messages above.")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def show_main_menu():
    """Show main toolkit menu"""
    print("🛠️  Available Tools:")
    print("1. 📦 Azure DevOps Wiki Migration")
    print("2. 🔍 Content Analysis & Planning")
    print("3. 👁️  Content Preview & Validation")
    print("4. 🐳 Local MediaWiki Development Environment")
    print("5. 📚 View Documentation")
    print("6. ❓ Help & Support")
    print("0. 🚪 Exit")
    print()

def handle_migration_setup():
    """Handle Azure DevOps migration setup"""
    print("\n📦 Azure DevOps Wiki Migration Setup")
    print("=" * 45)

    # Step 1: Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n📦 Please install dependencies first:")
        print("pip install -r migration/requirements.txt")
        return

    # Step 2: Set up environment
    print("\n🔍 Setting up environment...")
    if not setup_environment():
        return

    # Step 3: Optional analysis
    if Path("migration/.env").exists():
        run_analysis()

    print("\n✅ Migration setup complete!")
    print("📚 Next: Review migration_analysis_report.md")

def handle_content_analysis():
    """Handle content analysis tools"""
    print("\n🔍 Content Analysis & Planning")
    print("=" * 35)
    print("Available analysis tools:")
    print("1. 📊 Migration Complexity Analysis")
    print("2. 📝 Content Structure Review")
    print("3. 📈 Size & Time Estimation")
    print()

    choice = input("Select analysis tool (1-3) or Enter to return: ")
    if choice == "1":
        run_analysis()
    elif choice == "2":
        print("📝 Content structure analysis will be available in future versions")
    elif choice == "3":
        print("📈 Size estimation will be available in future versions")

def handle_content_preview():
    """Handle content preview tools"""
    print("\n👁️  Content Preview & Validation")
    print("=" * 35)

    if not Path("migration/content_previewer.py").exists():
        print("❌ Content previewer not found")
        return

    print("🚀 Starting content previewer...")
    success = run_python_script("content_previewer.py", "migration")
    if not success:
        print("❌ Preview failed. Please check the error messages above.")

def handle_dev_environment():
    """Handle development environment setup"""
    print("\n🐳 Local MediaWiki Development Environment")
    print("=" * 45)

    docker_compose = Path("examples/docker-compose.yml")
    if not docker_compose.exists():
        print("❌ Docker Compose file not found at examples/docker-compose.yml")
        return

    print("📋 Docker Compose configuration found!")
    print("🚀 To start your local MediaWiki environment:")
    print("   cd examples")
    print("   docker-compose up -d")
    print()
    print("📂 Your MediaWiki will be available at: http://localhost:8080")
    print("📊 Database: MySQL on localhost:3306")

    response = input("Do you want to start the environment now? (y/N): ")
    if response.lower() == 'y':
        success = run_docker_compose("examples", "up -d")
        if success:
            print("✅ Environment started successfully!")
            print("📂 MediaWiki: http://localhost:8080")
            print("📊 Database: MySQL on localhost:3306")
        else:
            print("❌ Failed to start environment. Please check Docker installation.")

def handle_documentation():
    """Handle documentation viewing"""
    while True:
        print("\n📚 Documentation")
        print("=" * 20)
        print("Available documentation:")
        print("1. 🌐 Online Documentation (GitHub Pages)")
        print("2. 📄 Local HTML Documentation")
        print("3. 📝 README Files")
        print("0. 🔙 Return to main menu")
        print()

        choice = input("Select documentation (0-3): ")

        if choice == "0" or choice == "":
            break
        elif choice == "1":
            url = "https://development-toolbox.github.io/development-toolbox-mediawiki-tools"
            print("🌐 Opening online documentation...")
            if not open_url_cross_platform(url):
                print(f"URL: {url}")
        elif choice == "2":
            handle_local_html_docs()
        elif choice == "3":
            handle_readme_files()
        else:
            print("❌ Invalid choice. Please select 0-3.")

        if choice != "0":
            input("\nPress Enter to continue...")

def handle_local_html_docs():
    """Handle local HTML documentation viewing"""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("❌ Local documentation not found")
        return

    html_files = list(docs_dir.glob("*.html"))
    if not html_files:
        print("❌ No HTML documentation files found")
        return

    print("\n� Local HTML Documentation")
    print("=" * 30)
    for i, html_file in enumerate(html_files, 1):
        print(f"{i}. {html_file.name}")
    print("0. 🔙 Return to documentation menu")
    print()

    try:
        choice = input("Select file to view (0-{0}): ".format(len(html_files)))
        if choice == "0" or choice == "":
            return

        file_index = int(choice) - 1
        if 0 <= file_index < len(html_files):
            selected_file = html_files[file_index]
            file_url = f"file://{selected_file.absolute()}"
            print(f"🌐 Opening {selected_file.name}...")
            if not open_url_cross_platform(file_url):
                print(f"File location: {selected_file.absolute()}")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Please enter a valid number")

def handle_readme_files():
    """Handle README file viewing with interactive menu"""
    readme_files = list(Path(".").glob("**/README.md"))
    if not readme_files:
        print("❌ No README files found")
        return

    # Sort files for consistent ordering
    readme_files.sort()

    while True:
        print("\n📝 README Files")
        print("=" * 20)
        for i, readme in enumerate(readme_files, 1):
            # Show relative path from project root
            rel_path = readme.relative_to(Path("."))
            print(f"{i:2d}. {rel_path}")
        print(" 0. 🔙 Return to documentation menu")
        print()

        try:
            choice = input("Select README to view (0-{0}): ".format(len(readme_files)))
            if choice == "0" or choice == "":
                break

            file_index = int(choice) - 1
            if 0 <= file_index < len(readme_files):
                selected_file = readme_files[file_index]
                display_readme_content(selected_file)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")

def display_readme_content(readme_path):
    """Display README content with pagination"""
    try:
        # Check file exists and is readable
        if not readme_path.is_file():
            print(f"❌ File not found: {readme_path}")
            return
            
        if not os.access(readme_path, os.R_OK):
            print(f"❌ No read permission for: {readme_path}")
            return
            
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.strip():
            print(f"ℹ️  File is empty: {readme_path}")
            return

        print(f"\n📖 {readme_path.relative_to(Path('.'))}")
        print("=" * 60)

        # Split content into lines for pagination
        lines = content.split('\n')
        lines_per_page = 30
        total_pages = (len(lines) + lines_per_page - 1) // lines_per_page
        current_page = 0

        while current_page < total_pages:
            start_line = current_page * lines_per_page
            end_line = min(start_line + lines_per_page, len(lines))

            # Display current page
            for line in lines[start_line:end_line]:
                print(line)

            # Show pagination info
            if total_pages > 1:
                print(f"\n📄 Page {current_page + 1} of {total_pages}")
                if current_page < total_pages - 1:
                    action = input("Press Enter for next page, 'q' to quit, 'b' for back: ").lower()
                    if action == 'q':
                        break
                    elif action == 'b' and current_page > 0:
                        current_page -= 1
                        continue
                    else:
                        current_page += 1
                else:
                    input("📄 End of file. Press Enter to continue...")
                    break
            else:
                input("\n📄 Press Enter to continue...")
                break

    except FileNotFoundError:
        print(f"❌ File not found: {readme_path}")
    except PermissionError:
        print(f"❌ Permission denied reading: {readme_path}")
    except UnicodeDecodeError:
        print(f"❌ Cannot decode file (invalid encoding): {readme_path}")
        print("💡 File may not be a text file or uses unsupported encoding")
    except OSError as e:
        print(f"❌ System error reading file: {e}")
        print(f"File location: {readme_path.absolute()}")
    except Exception as e:
        print(f"❌ Unexpected error reading file: {e}")
        print(f"File location: {readme_path.absolute()}")

def handle_help():
    """Handle help and support"""
    print("\n❓ Help & Support")
    print("=" * 20)
    print("🐛 Report Issues: https://github.com/development-toolbox/development-toolbox-mediawiki-tools/issues")
    print("📖 Documentation: https://development-toolbox.github.io/development-toolbox-mediawiki-tools")
    print("💬 Discussions: https://github.com/development-toolbox/development-toolbox-mediawiki-tools/discussions")
    print()
    print("🔧 General Troubleshooting:")
    print("• Check Python version (3.7+ required)")
    print("• Install dependencies: pip install -r migration/requirements.txt")
    print("• Verify environment configuration in migration/.env")
    print("• Check Docker installation for local environment")
    print("• Review .toolkit_env for custom settings")
    print()

    system = platform.system()
    shell = os.environ.get('SHELL') or os.environ.get('COMSPEC') or 'unknown'
    msystem = os.environ.get('MSYSTEM', '')
    is_git_bash = "bash" in shell.lower() or "MSYS" in msystem

    if system == "Windows" and is_git_bash:
        print("🚀 Git Bash on Windows:")
        print("• You're using an excellent development environment!")
        print("• All Unix-like commands work normally")
        print("• Docker commands work without modification")
        print("• Python path is handled automatically by toolkit")
        print("• Use regular pip/python commands")
    elif system == "Windows":
        print("🪟 Windows-specific:")
        print("• Consider switching to Git Bash for better experience")
        print("• Use 'py' command if 'python' doesn't work")
        print("• Install Docker Desktop from docker.com")
        print("• PowerShell and Command Prompt also supported")
    elif system == "Darwin":
        print("🍎 macOS-specific:")
        print("• Use 'python3' if 'python' doesn't work")
        print("• Install Docker Desktop from docker.com")
        print("• Use Terminal or iTerm2")
    else:
        print("🐧 Linux-specific:")
        print("• Install docker: sudo apt install docker.io docker-compose")
        print("• Add user to docker group: sudo usermod -aG docker $USER")
        print("• Use package manager for Python: apt/yum/pacman")

def main():
    """Main toolkit workflow"""
    print_banner()

    # Create toolkit environment if it doesn't exist
    print("🔧 Setting up toolkit environment...")
    create_toolkit_environment()
    print()

    # Show platform information
    show_platform_info()

    # Check Python version first
    print("🔍 Checking Python version...")
    check_python_version()
    print()

    while True:
        show_main_menu()
        choice = input("Select an option (0-6): ")

        if choice == "0":
            print("👋 Thanks for using MediaWiki Development Toolkit!")
            break
        elif choice == "1":
            handle_migration_setup()
        elif choice == "2":
            handle_content_analysis()
        elif choice == "3":
            handle_content_preview()
        elif choice == "4":
            handle_dev_environment()
        elif choice == "5":
            handle_documentation()
        elif choice == "6":
            handle_help()
        else:
            print("❌ Invalid choice. Please select 0-6.")

        print("\n" + "="*60)

if __name__ == "__main__":
    main()
