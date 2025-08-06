# Contributing to MediaWiki Development Toolkit

Thank you for your interest in contributing to the MediaWiki Development Toolkit! This guide will help you get started with contributing to this project.

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+** (3.8+ recommended)
- **Git** (preferably with Git Bash on Windows)
- **Docker Desktop** (for local development environment)
- **Basic understanding** of MediaWiki and Azure DevOps

### Getting Started

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/development-toolbox-mediawiki-tools.git
   cd development-toolbox-mediawiki-tools
   ```

2. **Run the Getting Started Script**
   ```bash
   python getting_started.py
   ```

   This interactive script will:
   - ✅ Detect your environment (Git Bash, Windows, macOS, Linux)
   - ✅ Create a `.toolkit_env` file with your system configuration
   - ✅ Guide you through setup without affecting your system
   - ✅ Show you all available tools and options

3. **Install Dependencies**
   ```bash
   pip install -r migration/requirements.txt
   ```

## 🛠️ Development Environment

### Supported Environments

- **🚀 Git Bash on Windows** (Recommended for Windows users)
- **🐧 Linux** (All major distributions)
- **🍎 macOS** (Terminal or iTerm2)
- **🪟 Windows** (PowerShell/Command Prompt also supported)

### Environment Configuration

The toolkit uses a `.toolkit_env` file to avoid system conflicts:

```bash
# Your Python executable (automatically detected)
TOOLKIT_PYTHON_EXECUTABLE=/path/to/your/python

# Shell configuration
TOOLKIT_SHELL=/path/to/your/shell
TOOLKIT_OS=YourOS

# Docker setup
TOOLKIT_DOCKER_COMPOSE_CMD=auto

# Project paths
TOOLKIT_WORK_DIR=/path/to/project
```

## 📁 Project Structure

```
development-toolbox-mediawiki-tools/
├── getting_started.py          # 🚀 Interactive setup script
├── .toolkit_env               # 🔧 Environment configuration
├── migration/                 # 📦 Migration tools
│   ├── azure_devops_migrator.py
│   ├── migration_planner.py
│   ├── content_previewer.py
│   └── requirements.txt
├── docs/                      # 📚 Documentation
│   ├── index.html            # GitHub Pages site
│   └── *.md                  # Markdown documentation
├── examples/                  # 🐳 Docker environments
│   └── docker-compose.yml
└── templates/                 # 📄 MediaWiki templates
```

## 🎯 Areas for Contribution

### 1. **Migration Tools Enhancement**
- Improve Azure DevOps API integration
- Add support for more content types
- Enhance error handling and logging
- Performance optimizations

### 2. **Content Analysis Tools**
- Advanced content complexity analysis
- Automated content structure detection
- Migration time estimation algorithms
- Content quality assessment

### 3. **Documentation**
- User guides and tutorials
- API documentation
- Video tutorials
- Troubleshooting guides

### 4. **Testing**
- Unit tests for migration tools
- Integration tests for workflows
- Performance testing
- Cross-platform testing

### 5. **Platform Support**
- Windows-specific improvements
- macOS compatibility
- Linux distribution testing
- Container deployment options

## 🔧 Development Workflow

### 1. **Create a Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

### 2. **Make Your Changes**
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed
- Test on your platform

### 3. **Test Your Changes**
```bash
# Run the getting started script
python getting_started.py

# Test specific tools
python migration/migration_planner.py
python migration/content_previewer.py
```

### 4. **Update Documentation**
- Update relevant README files
- Add new documentation if needed
- Update the main documentation site

### 5. **Commit and Push**
```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 6. **Create Pull Request**
- Use descriptive title and description
- Reference any related issues
- Include testing notes
- Add screenshots if relevant

## 📝 Coding Standards

### Python Code Style
- **PEP 8** compliance
- **Type hints** for new functions
- **Docstrings** for all public functions
- **Error handling** with descriptive messages

### Example Function:
```python
def migrate_content(source_url: str, target_url: str) -> bool:
    """
    Migrate content from source to target MediaWiki.

    Args:
        source_url: Azure DevOps wiki URL
        target_url: Target MediaWiki URL

    Returns:
        bool: True if migration successful, False otherwise

    Raises:
        ConnectionError: If unable to connect to APIs
        ValidationError: If content validation fails
    """
    try:
        # Implementation here
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
```

### Documentation Style
- **Clear headings** with emojis for visual organization
- **Code examples** for all features
- **Cross-platform instructions** when relevant
- **Troubleshooting sections** for common issues

## 🧪 Testing Guidelines

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=migration
```

### Writing Tests
- **Unit tests** for individual functions
- **Integration tests** for complete workflows
- **Mock external APIs** in tests
- **Test error conditions** and edge cases

### Test Structure:
```python
def test_content_migration():
    """Test content migration functionality."""
    # Arrange
    source_content = "# Test Content"

    # Act
    result = migrate_content(source_content)

    # Assert
    assert result.success is True
    assert "Test Content" in result.content
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Operating system and version
   - Python version
   - Shell (bash, PowerShell, etc.)
   - Output from `getting_started.py`

2. **Steps to Reproduce**
   - Exact commands run
   - Configuration files used
   - Expected vs actual behavior

3. **Error Messages**
   - Full error output
   - Log files if available
   - Screenshots if relevant

4. **Additional Context**
   - Related issues or PRs
   - Workarounds tried
   - Impact assessment

## 💡 Feature Requests

For new features, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Provide examples** of desired functionality
4. **Consider implementation** complexity
5. **Discuss compatibility** with existing features

## 🌟 Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Credited in documentation**
- **Thanked in the community**

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Documentation**: Check the [online docs](https://development-toolbox.github.io/development-toolbox-mediawiki-tools)
- **Getting Started**: Run `python getting_started.py` for interactive help

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Happy Contributing!** 🎉

Your contributions help make MediaWiki migration easier for everyone. Whether you're fixing a typo, adding a feature, or improving documentation, every contribution matters!
