# MediaWiki Development Toolkit

A comprehensive toolkit for MediaWiki management including migration, maintenance, synchronization, and automation tools. Get started quickly with our interactive setup script!

## 🚀 Quick Start

**New users: Start here!**

```bash
# Clone the repository
git clone https://github.com/development-toolbox/development-toolbox-mediawiki-tools.git
cd development-toolbox-mediawiki-tools

# Run the interactive getting started script
python getting_started.py
```

The getting started script will:
- ✅ **Detect your environment** (Git Bash, Windows, macOS, Linux)
- ✅ **Set up toolkit configuration** without affecting your system
- ✅ **Guide you through tool selection** with an interactive menu
- ✅ **Install dependencies** and configure environments
- ✅ **Provide platform-specific tips** and troubleshooting

### 🖥️ Supported Platforms

- **🚀 Git Bash on Windows** (Recommended for Windows developers)
- **🐧 Linux** (All major distributions)
- **🍎 macOS** (Terminal or iTerm2)
- **🪟 Windows** (PowerShell/Command Prompt)

## � Documentation

### 🌐 Main Documentation
- **[🔗 Live Documentation Site](https://development-toolbox.github.io/development-toolbox-mediawiki-tools)** - Interactive documentation with examples
- **[📖 How-To Guides](./docs/HOW-TO-GUIDES.md)** - Step-by-step guides for all migration scenarios
- **[�🛠️ Troubleshooting Guide](./docs/TROUBLESHOOTING.md)** - Comprehensive problem-solving guide
- **[🤝 Contributing Guide](./CONTRIBUTING.md)** - Development setup and contribution guidelines

### 📋 Quick Reference
| Migration Size | Guide | Time Estimate |
|---------------|-------|---------------|
| 10-50 pages | [Quick Migration](./docs/HOW-TO-GUIDES.md#quick-migration) | 15-30 minutes |
| 100-500 pages | [Department Migration](./docs/HOW-TO-GUIDES.md#department-migration) | 2-4 hours |
| 500+ pages | [Enterprise Migration](./docs/HOW-TO-GUIDES.md#enterprise-migration) | 1-2 days |

## 🛠️ Available Tools

### 🚀 [Migration Tools](./migration/)
- **Azure DevOps Wiki Migrator**: Complete wiki migration from Azure DevOps to MediaWiki
- **Migration Planner**: Pre-migration analysis and complexity assessment
- **Content Previewer**: Preview converted content before migration
- **Validation Tool**: Post-migration content validation and reporting
- **Template Importer**: Bulk import MediaWiki templates
- **Content format converters**: Markdown to MediaWiki syntax

**[📖 Detailed Migration Guide](./migration/README.md)**

### 📝 [Examples & Configurations](./examples/)
- **Docker Compose Setup**: Local MediaWiki development environment
- **Migration Scenarios**: Real-world migration examples and case studies
- **Configuration Templates**: Sample environment and configuration files
- **Conversion Examples**: Before/after content conversion samples
- **GitHub Actions Workflows**: CI/CD integration examples
- **Performance Benchmarks**: Expected migration times and optimization tips

**[📖 Comprehensive Examples Guide](./examples/README.md)**

### 🎨 [Template Management](./templates/)
- **Template Importer**: Bulk import and update MediaWiki templates
- **Template Validator**: Check template syntax and dependencies
- **Template Backup**: Export and version control templates

### 🔄 [Sync Tools](./sync/) *(Coming Soon)*
- **GitHub Actions Workflows**: Automated content synchronization
- **Content Folder Sync**: Keep wiki content in sync with repositories
- **Automated backups**: Scheduled wiki backups

### 🔧 [Maintenance Scripts](./maintenance/) *(Coming Soon)*
- **Database optimization**: Clean up and optimize MediaWiki database
- **Broken link checker**: Find and report broken internal/external links
- **Image optimization**: Compress and optimize uploaded images
- **Cache management**: Clear and refresh MediaWiki caches

### 📊 [Monitoring Tools](./monitoring/) *(Coming Soon)*
- **Health checks**: Monitor MediaWiki installation health
- **Usage analytics**: Track page views and user activity
- **Performance monitoring**: Database and response time monitoring

### 🚢 [Deployment Tools](./deployment/) *(Coming Soon)*
- **Update scripts**: Automated MediaWiki core and extension updates
- **Theme management**: Deploy and manage custom skins/themes
- **Extension management**: Install and configure MediaWiki extensions

## 🚀 Alternative Setup (Manual)

If you prefer manual setup or want to use specific tools directly:

1. **Choose your tool** from the sections below
2. **Navigate to the tool directory** (e.g., `cd migration/`)
3. **Follow the README** in that directory for setup instructions
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Configure**: Copy `.env.template` to `.env` and update settings
6. **Run the tool**: Follow the specific usage instructions

## 📁 Repository Structure

```
development-toolbox-mediawiki-tools/
├── getting_started.py   # 🚀 Interactive setup script
├── .toolkit_env        # 🔧 Environment configuration (auto-generated)
├── migration/          # Wiki migration tools
├── templates/          # Template management tools
├── maintenance/        # Maintenance and optimization scripts
├── sync/              # Synchronization and automation
├── monitoring/        # Health checks and analytics
├── deployment/        # Update and deployment tools
├── examples/          # Example configurations and workflows
├── docs/             # Additional documentation
├── CONTRIBUTING.md   # 🤝 Contribution guidelines
└── .github/          # GitHub Actions workflows
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Read our [Contributing Guide](CONTRIBUTING.md)** for detailed guidelines
2. **Run `python getting_started.py`** to set up your development environment
3. **Check the issues** for good first contributions
4. **Fork, code, test, and submit a PR**

### Quick Contributing Setup
```bash
# Fork and clone your fork
git clone https://github.com/your-username/development-toolbox-mediawiki-tools.git
cd development-toolbox-mediawiki-tools

# Set up development environment
python getting_started.py

# Create feature branch
git checkout -b feature/your-feature-name
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, testing guidelines, and more details.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

- 📚 Check the docs/ directory for detailed documentation
- 🐛 Report issues using GitHub Issues
- 💡 Feature requests welcome!

---

**Happy MediaWiki managing! 🎯**
