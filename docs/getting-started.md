# 🚀 Getting Started with MediaWiki Development Toolkit

Welcome to the MediaWiki Development Toolkit! This guide will help you get started quickly with our interactive setup script and guide you through using the various tools.

## Quick Start (Recommended)

The fastest way to get started is with our interactive setup script:

```bash
# Clone the repository
git clone https://github.com/development-toolbox/development-toolbox-mediawiki-tools.git
cd development-toolbox-mediawiki-tools

# Run the interactive getting started script
python getting_started.py
```

## What the Getting Started Script Does

### 🔍 Environment Detection
The script automatically detects your platform and provides tailored advice:

- **🚀 Git Bash on Windows** (Recommended for Windows developers)
- **🐧 Linux** (All major distributions supported)
- **🍎 macOS** (Terminal or iTerm2)
- **🪟 Windows** (PowerShell/Command Prompt)

### ⚙️ Configuration Setup
Creates a `.toolkit_env` file with your system configuration without affecting your global environment:

```bash
# Example .toolkit_env content
TOOLKIT_PYTHON_EXECUTABLE=/path/to/your/python
TOOLKIT_SHELL=/path/to/your/shell
TOOLKIT_OS=YourOS
TOOLKIT_GIT_BASH=true/false
TOOLKIT_DOCKER_COMPOSE_CMD=auto
```

### 🛠️ Interactive Tool Menu
Choose what you want to do from the main menu:

1. **📦 Azure DevOps Wiki Migration** - Complete migration workflow
2. **🔍 Content Analysis & Planning** - Analyze migration complexity
3. **👁️ Content Preview & Validation** - Preview converted content
4. **🐳 Local MediaWiki Development Environment** - Docker setup
5. **📚 View Documentation** - Access all documentation
6. **❓ Help & Support** - Platform-specific troubleshooting

## Platform-Specific Features

### Git Bash on Windows
If you're using Git Bash (recommended), the script will:
- ✅ Recognize your excellent development environment choice
- ✅ Handle Windows Python paths correctly in Unix-like environment
- ✅ Provide Unix-style command guidance
- ✅ Configure Docker commands to work seamlessly

### Other Platforms
- **macOS**: Provides Homebrew and Docker Desktop guidance
- **Linux**: Package manager specific instructions
- **Windows CMD/PowerShell**: Windows-specific Python and Docker setup

## Tool-Specific Setup

### Azure DevOps Wiki Migration
1. Select option 1 from the main menu
2. Script will check dependencies and install if needed
3. Guided environment configuration setup
4. Optional migration analysis to assess complexity

### Content Analysis
1. Select option 2 from the main menu
2. Choose from available analysis tools:
   - Migration complexity analysis
   - Content structure review (coming soon)
   - Size & time estimation (coming soon)

### Content Preview
1. Select option 3 from the main menu
2. Preview how your Azure DevOps content will look in MediaWiki
3. Validate conversion quality before migration

### Local Development Environment
1. Select option 4 from the main menu
2. Automated Docker Compose setup for local MediaWiki testing
3. Includes database and MediaWiki instance
4. Available at http://localhost:8080 after setup

## Alternative Manual Setup

If you prefer manual setup or want to use specific tools directly:

```bash
# Navigate to specific tool directory
cd migration/

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env with your Azure DevOps credentials

# Run specific tools
python migration_planner.py
python azure_devops_migrator.py
python content_previewer.py
```

## Environment Configuration

### Azure DevOps Setup
Create `migration/.env` with your credentials:

```bash
# Azure DevOps Configuration
AZURE_DEVOPS_ORG=your_organization
AZURE_DEVOPS_PROJECT=your_project
AZURE_DEVOPS_TOKEN=your_personal_access_token

# MediaWiki Configuration
MEDIAWIKI_API_URL=http://your-mediawiki/api.php
MEDIAWIKI_USERNAME=your_username
MEDIAWIKI_PASSWORD=your_password
```

### Docker Environment
For local testing, the script can automatically set up:

```bash
# Start local MediaWiki environment
cd examples/
docker-compose up -d

# Access at:
# MediaWiki: http://localhost:8080
# Database: localhost:3306
```

## Common Workflows

### First-Time Migration
1. Run `python getting_started.py`
2. Select "Azure DevOps Wiki Migration"
3. Follow guided setup for dependencies and configuration
4. Run analysis to understand migration complexity
5. Set up local MediaWiki environment for testing
6. Preview content conversion
7. Execute migration with monitoring

### Development and Contribution
1. Run `python getting_started.py`
2. Select "Local MediaWiki Development Environment"
3. Set up Docker environment for testing
4. Select "View Documentation" to access development guides
5. Check CONTRIBUTING.md for detailed development guidelines

### Content Analysis Only
1. Run `python getting_started.py`
2. Select "Content Analysis & Planning"
3. Choose "Migration Complexity Analysis"
4. Review generated analysis report

## Troubleshooting

### Python Issues
The script automatically handles Python path detection, but if you encounter issues:

```bash
# Check your Python installation
python --version

# Check toolkit environment
cat .toolkit_env

# Manual Python path override
# Edit .toolkit_env and set TOOLKIT_PYTHON_EXECUTABLE
```

### Docker Issues
```bash
# Check Docker installation
docker --version
docker-compose --version

# For Git Bash users, commands work normally
# For other Windows users, ensure Docker Desktop is running
```

### Platform-Specific Help
Run `python getting_started.py` and select option 6 (Help & Support) for platform-specific troubleshooting advice.

## Next Steps

After setup:

1. **Read Documentation**: Check the `docs/` directory for detailed guides
2. **Review Examples**: Look at `examples/` for configuration templates
3. **Join Community**: Check GitHub discussions for questions and ideas
4. **Contribute**: See CONTRIBUTING.md for development guidelines

## Support

- **🐛 Issues**: Report bugs via GitHub Issues
- **💬 Discussions**: Ask questions in GitHub Discussions
- **📖 Documentation**: Full documentation at GitHub Pages
- **🆘 Interactive Help**: Run `python getting_started.py` option 6

---

**Happy migrating!** 🎯

The getting started script is designed to make your experience as smooth as possible, regardless of your platform or experience level.
