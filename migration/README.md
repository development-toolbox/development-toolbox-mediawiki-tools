# Migration Tools

Tools for migrating content to MediaWiki from various sources.

## 🚀 Available Migration Tools

### Azure DevOps Wiki Migrator
Complete migration of wiki pages from Azure DevOps to MediaWiki with automatic Markdown to MediaWiki conversion.

**Files:**
- `azure_devops_migrator.py` - Main migration script
- `migration_planner.py` - Pre-migration analysis tool
- `content_previewer.py` - Content preview and validation
- `validation_tool.py` - Post-migration validation
- `.env.template` - Configuration template
- `requirements.txt` - Python dependencies

## 📖 How-To Guides

### Quick Start with Interactive Setup

The easiest way to get started is using the interactive setup script:

```bash
# From the project root
python getting_started.py

# Select option: "📦 Azure DevOps Wiki Migration"
# The script will guide you through the complete setup
```

### Manual Setup Guide

#### 1. Environment Setup
```bash
# Navigate to migration directory
cd migration/

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
```

#### 2. Configure Environment Variables
Edit `.env` file with your credentials:

```bash
# Azure DevOps Configuration
AZURE_DEVOPS_ORG=your-organization
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_TOKEN=your-personal-access-token

# MediaWiki Configuration
MEDIAWIKI_URL=https://your-mediawiki.com/api.php
MEDIAWIKI_USERNAME=your-username
MEDIAWIKI_PASSWORD=your-password

# Optional: Batch size for processing
BATCH_SIZE=10
```

#### 3. Pre-Migration Analysis
Always run the migration planner first to understand complexity:

```bash
python migration_planner.py --wiki "YourWikiName"
```

**Output:** Creates `migration_analysis_report.md` with:
- Content complexity scoring
- Estimated migration time
- Risk assessment
- Recommended approach

#### 4. Content Preview
Preview how your content will convert before migration:

```bash
# Preview specific pages
python content_previewer.py --page "Home"
python content_previewer.py --page "Getting Started"

# Generate sample conversions for review
python content_previewer.py --sample-pages 5

# Preview all pages (for small wikis)
python content_previewer.py --all-pages
```

#### 5. Run Migration
Start with a small batch to test:

```bash
# Test migration with small batch
python azure_devops_migrator.py --wiki "YourWikiName" --batch-size 5

# Full migration (after testing)
python azure_devops_migrator.py --wiki "YourWikiName"
```

#### 6. Post-Migration Validation
Validate the migrated content:

```bash
python validation_tool.py --wiki "YourWikiName"
```

## 🔧 Advanced Configuration

### Batch Processing Options
```bash
# Process specific pages only
python azure_devops_migrator.py --wiki "Docs" --pages "Home,FAQ,Setup"

# Resume from specific page (if migration interrupted)
python azure_devops_migrator.py --wiki "Docs" --resume-from "Page Name"

# Dry run (preview only, no actual migration)
python azure_devops_migrator.py --wiki "Docs" --dry-run
```

### Content Filtering
```bash
# Skip pages matching patterns
python azure_devops_migrator.py --wiki "Docs" --exclude-pattern "Archive/*,Old/*"

# Only migrate pages modified after date
python azure_devops_migrator.py --wiki "Docs" --modified-after "2024-01-01"
```

## 📝 Migration Examples

### Example 1: Simple Wiki Migration
```bash
# 1. Analyze first
python migration_planner.py --wiki "ProjectDocs"

# 2. Preview a few pages
python content_previewer.py --page "Home"

# 3. Test with small batch
python azure_devops_migrator.py --wiki "ProjectDocs" --batch-size 3

# 4. Full migration
python azure_devops_migrator.py --wiki "ProjectDocs"
```

### Example 2: Large Wiki with Selective Migration
```bash
# 1. Analyze complexity
python migration_planner.py --wiki "LargeWiki"

# 2. Migrate only current documentation
python azure_devops_migrator.py --wiki "LargeWiki" \
    --exclude-pattern "Archive/*,Deprecated/*" \
    --modified-after "2024-01-01"

# 3. Validate specific sections
python validation_tool.py --wiki "LargeWiki" --pages "Home,Setup,FAQ"
```

### Example 3: Preview-Heavy Workflow
```bash
# 1. Generate comprehensive preview
python content_previewer.py --wiki "TestWiki" --all-pages --output-dir "./previews"

# 2. Review conversion quality in ./previews directory

# 3. Migrate only verified pages
python azure_devops_migrator.py --wiki "TestWiki" \
    --pages "$(cat verified_pages.txt)"
```

## 🛠️ Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Test Azure DevOps connection
python -c "
from azure_devops_migrator import test_azure_connection
test_azure_connection()
"

# Test MediaWiki connection
python -c "
from azure_devops_migrator import test_mediawiki_connection
test_mediawiki_connection()
"
```

#### Content Conversion Issues
```bash
# Preview specific problematic page
python content_previewer.py --page "ProblematicPage" --verbose

# Check conversion logs
tail -f migration.log
```

#### Performance Issues
```bash
# Use smaller batch size
python azure_devops_migrator.py --wiki "Docs" --batch-size 5

# Process during off-peak hours
python azure_devops_migrator.py --wiki "Docs" --rate-limit 1
```

### Getting Help

1. **Check Logs:** All operations create detailed logs in `migration.log`
2. **Use Verbose Mode:** Add `--verbose` flag to any command
3. **Preview First:** Always use `content_previewer.py` to identify issues
4. **Test Small:** Start with `--batch-size 1` for problematic content

## 📊 Output Files

### Migration Reports
- `migration_analysis_report.md` - Pre-migration analysis
- `migration_report.md` - Post-migration summary
- `conversion_issues.md` - Content that needs manual review
- `migration.log` - Detailed operation logs

### Preview Files
- `previews/` directory - HTML previews of converted content
- `conversion_samples.md` - Sample conversions for review

## 🔄 Best Practices

### Before Migration
1. **Always run migration planner first**
2. **Preview representative pages**
3. **Test with small batches**
4. **Backup your source content**
5. **Have MediaWiki admin access ready**

### During Migration
1. **Monitor the logs actively**
2. **Don't interrupt batch operations**
3. **Test with non-production MediaWiki first**
4. **Keep network connection stable**

### After Migration
1. **Run validation tool**
2. **Review conversion_issues.md**
3. **Manually handle images and attachments**
4. **Update internal links if needed**
5. **Train users on MediaWiki differences**

For more detailed information, see the main project documentation at [../docs/index.html](../docs/index.html).
