# MediaWiki Tools

A comprehensive toolkit for MediaWiki management including migration, maintenance, synchronization, and automation tools.

## 🛠️ Available Tools

### 🚀 [Migration Tools](./migration/)
- **Azure DevOps Wiki Migrator**: Complete wiki migration from Azure DevOps to MediaWiki
- **Template Importer**: Bulk import MediaWiki templates
- **Content format converters**: Markdown to MediaWiki syntax

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

## 🚀 Quick Start

1. **Choose your tool** from the sections above
2. **Navigate to the tool directory** (e.g., `cd migration/`)
3. **Follow the README** in that directory for setup instructions
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Configure**: Copy `.env.template` to `.env` and update settings
6. **Run the tool**: Follow the specific usage instructions

## 📁 Repository Structure

```
development-toolbox-mediawiki-tools/
├── migration/           # Wiki migration tools
├── templates/          # Template management tools
├── maintenance/        # Maintenance and optimization scripts
├── sync/              # Synchronization and automation
├── monitoring/        # Health checks and analytics
├── deployment/        # Update and deployment tools
├── examples/          # Example configurations and workflows
├── docs/             # Additional documentation
└── .github/          # GitHub Actions workflows
```

## 🤝 Contributing

We welcome contributions! Please see individual tool directories for specific contribution guidelines.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

- 📚 Check the docs/ directory for detailed documentation
- 🐛 Report issues using GitHub Issues
- 💡 Feature requests welcome!

---

**Happy MediaWiki managing! 🎯**
