# Example MediaWiki Tools Configuration

This directory contains example configurations and real-world setups for various MediaWiki tools and migration scenarios.

## 📁 Directory Structure

```
examples/
├── docker-compose.yml              # Local MediaWiki development environment
├── sample-templates/               # Example MediaWiki templates
├── workflows/                      # Example GitHub Actions workflows
├── migration-scenarios/            # Real-world migration examples
├── configuration-samples/          # Sample configuration files
└── conversion-examples/            # Before/after conversion samples
```

## 🐳 Local Development Environment

### Quick Start with Docker
```bash
# Start local MediaWiki instance
docker-compose up -d

# Access at: http://localhost:8080
# Admin credentials: admin/admin123

# Stop environment
docker-compose down
```

### Environment Features
- **MediaWiki 1.39** with common extensions
- **MySQL 8.0** database
- **Persistent volumes** for data retention
- **Pre-configured** with development settings
- **Sample content** for testing migrations

## 🔄 Migration Scenarios

### Scenario 1: Small Team Wiki (10-50 pages)
**Use Case:** Development team wiki with documentation, procedures, and guides.

```bash
# 1. Quick analysis
python ../migration/migration_planner.py --wiki "TeamDocs"

# 2. Preview key pages
python ../migration/content_previewer.py --page "Home"
python ../migration/content_previewer.py --page "Development Setup"

# 3. Simple migration
python ../migration/azure_devops_migrator.py --wiki "TeamDocs"
```

**Expected Results:**
- Migration time: 15-30 minutes
- Manual review needed: 5-10 pages
- Common issues: Images, complex tables

### Scenario 2: Department Wiki (100-500 pages)
**Use Case:** Large department wiki with multiple contributors and complex content.

```bash
# 1. Comprehensive analysis
python ../migration/migration_planner.py --wiki "DeptWiki" --detailed

# 2. Batch preview
python ../migration/content_previewer.py --sample-pages 20

# 3. Phased migration
python ../migration/azure_devops_migrator.py --wiki "DeptWiki" \
    --batch-size 25 \
    --exclude-pattern "Archive/*"

# 4. Validation
python ../migration/validation_tool.py --wiki "DeptWiki"
```

**Expected Results:**
- Migration time: 2-4 hours
- Manual review needed: 20-50 pages
- Common issues: Legacy content, broken links, complex formatting

### Scenario 3: Enterprise Wiki (500+ pages)
**Use Case:** Organization-wide wiki with historical content and complex structure.

```bash
# 1. Strategic analysis
python ../migration/migration_planner.py --wiki "EnterpriseWiki" \
    --detailed --export-analysis

# 2. Content categorization
python ../migration/content_previewer.py --all-pages \
    --categorize --output-dir "./analysis"

# 3. Selective migration (current content only)
python ../migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --modified-after "2023-01-01" \
    --exclude-pattern "Archive/*,Deprecated/*,Draft/*" \
    --batch-size 10

# 4. Legacy content (separate process)
python ../migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --include-pattern "Archive/*" \
    --target-namespace "Archive" \
    --batch-size 5
```

**Expected Results:**
- Migration time: 1-2 days
- Manual review needed: 100+ pages
- Common issues: Outdated content, complex templates, broken workflows

## 📝 Configuration Examples

### Basic `.env` Configuration
```env
# Azure DevOps
AZURE_DEVOPS_ORG=mycompany
AZURE_DEVOPS_PROJECT=MyProject
AZURE_DEVOPS_TOKEN=abcd1234567890

# MediaWiki
MEDIAWIKI_URL=https://wiki.mycompany.com/api.php
MEDIAWIKI_USERNAME=migration_bot
MEDIAWIKI_PASSWORD=secure_password

# Settings
BATCH_SIZE=10
RATE_LIMIT_DELAY=1
LOG_LEVEL=INFO
```

### Advanced `.env` Configuration
```env
# Azure DevOps
AZURE_DEVOPS_ORG=enterprise
AZURE_DEVOPS_PROJECT=Documentation
AZURE_DEVOPS_TOKEN=pat_token_here

# MediaWiki
MEDIAWIKI_URL=https://wiki.enterprise.com/api.php
MEDIAWIKI_USERNAME=azure_migrator
MEDIAWIKI_PASSWORD=complex_password

# Advanced Settings
BATCH_SIZE=5
RATE_LIMIT_DELAY=2
MAX_RETRIES=3
TIMEOUT=30

# Content Filtering
EXCLUDE_PATTERNS=Archive/*,Draft/*,Temp/*
INCLUDE_PATTERNS=Documentation/*,Procedures/*
MODIFIED_AFTER=2023-01-01

# Output Options
LOG_LEVEL=DEBUG
EXPORT_FAILED_PAGES=true
GENERATE_REPORT=true
BACKUP_ORIGINAL=true
```

## 🔄 Conversion Examples

### Example 1: Simple Text Formatting
**Azure DevOps Markdown:**
```markdown
# Project Setup Guide

Welcome to our **awesome project**! This guide covers *essential* setup steps.

## Prerequisites
- Python 3.8+
- Git
- `virtualenv` package

```bash
pip install virtualenv
virtualenv venv
source venv/bin/activate
```

> **Note:** Always use virtual environments for development.
```

**Converted MediaWiki:**
```mediawiki
= Project Setup Guide =

Welcome to our '''awesome project'''! This guide covers ''essential'' setup steps.

== Prerequisites ==
* Python 3.8+
* Git
* <code>virtualenv</code> package

<syntaxhighlight lang="bash">
pip install virtualenv
virtualenv venv
source venv/bin/activate
</syntaxhighlight>

{{Note|Always use virtual environments for development.}}
```

### Example 2: Complex Table with Links
**Azure DevOps Markdown:**
```markdown
| Tool | Purpose | Documentation |
|------|---------|---------------|
| [Migration Planner](/docs/migration-planner) | Analysis | [Guide](/docs/planning-guide) |
| [Content Previewer](/docs/content-previewer) | Preview | [Guide](/docs/preview-guide) |
| [Validator](/docs/validator) | Validation | [Guide](/docs/validation-guide) |
```

**Converted MediaWiki:**
```mediawiki
{| class="wikitable"
|-
! Tool !! Purpose !! Documentation
|-
| [[Migration Planner]] || Analysis || [[Planning Guide]]
|-
| [[Content Previewer]] || Preview || [[Preview Guide]]
|-
| [[Validator]] || Validation || [[Validation Guide]]
|}
```

### Example 3: Code Blocks with Multiple Languages
**Azure DevOps Markdown:**
```markdown
## API Configuration

### Python
```python
import requests

config = {
    'api_url': 'https://api.example.com',
    'token': 'your-token'
}

response = requests.get(config['api_url'],
                       headers={'Authorization': f"Bearer {config['token']}"})
```

### JavaScript
```javascript
const config = {
    apiUrl: 'https://api.example.com',
    token: 'your-token'
};

fetch(config.apiUrl, {
    headers: {
        'Authorization': `Bearer ${config.token}`
    }
});
```
```

**Converted MediaWiki:**
```mediawiki
== API Configuration ==

=== Python ===
<syntaxhighlight lang="python">
import requests

config = {
    'api_url': 'https://api.example.com',
    'token': 'your-token'
}

response = requests.get(config['api_url'],
                       headers={'Authorization': f"Bearer {config['token']}"})
</syntaxhighlight>

=== JavaScript ===
<syntaxhighlight lang="javascript">
const config = {
    apiUrl: 'https://api.example.com',
    token: 'your-token'
};

fetch(config.apiUrl, {
    headers: {
        'Authorization': `Bearer ${config.token}`
    }
});
</syntaxhighlight>
```

## 🚀 Workflow Examples

### GitHub Actions Workflow for Automated Migration
```yaml
# .github/workflows/wiki-migration.yml
name: Wiki Migration

on:
  workflow_dispatch:
    inputs:
      wiki_name:
        description: 'Azure DevOps Wiki name to migrate'
        required: true
      batch_size:
        description: 'Batch size for migration'
        default: '10'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r migration/requirements.txt

    - name: Run migration analysis
      env:
        AZURE_DEVOPS_TOKEN: ${{ secrets.AZURE_DEVOPS_TOKEN }}
        MEDIAWIKI_PASSWORD: ${{ secrets.MEDIAWIKI_PASSWORD }}
      run: |
        python migration/migration_planner.py --wiki "${{ github.event.inputs.wiki_name }}"

    - name: Execute migration
      env:
        AZURE_DEVOPS_TOKEN: ${{ secrets.AZURE_DEVOPS_TOKEN }}
        MEDIAWIKI_PASSWORD: ${{ secrets.MEDIAWIKI_PASSWORD }}
      run: |
        python migration/azure_devops_migrator.py \
          --wiki "${{ github.event.inputs.wiki_name }}" \
          --batch-size "${{ github.event.inputs.batch_size }}"

    - name: Upload migration report
      uses: actions/upload-artifact@v3
      with:
        name: migration-report
        path: migration_report.md
```

## 🛠️ Testing Examples

### Unit Test Setup
```python
# tests/test_migration.py
import unittest
from migration.azure_devops_migrator import ContentConverter

class TestContentConverter(unittest.TestCase):
    def setUp(self):
        self.converter = ContentConverter()

    def test_header_conversion(self):
        markdown = "# Main Title\n## Subtitle"
        expected = "= Main Title =\n== Subtitle =="
        result = self.converter.convert_markdown(markdown)
        self.assertEqual(result, expected)

    def test_code_block_conversion(self):
        markdown = "```python\nprint('hello')\n```"
        expected = "<syntaxhighlight lang=\"python\">\nprint('hello')\n</syntaxhighlight>"
        result = self.converter.convert_markdown(markdown)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test
```bash
#!/bin/bash
# tests/integration_test.sh

echo "Starting integration test..."

# Test environment setup
python getting_started.py --test-mode

# Test migration planner
python migration/migration_planner.py --wiki "TestWiki" --dry-run

# Test content preview
python migration/content_previewer.py --page "TestPage" --dry-run

# Test migration
python migration/azure_devops_migrator.py --wiki "TestWiki" --dry-run --batch-size 1

echo "Integration test completed!"
```

## 📊 Performance Benchmarks

### Migration Speed Examples
- **Small Wiki (10 pages):** ~2 minutes
- **Medium Wiki (100 pages):** ~20 minutes
- **Large Wiki (500 pages):** ~2 hours
- **Enterprise Wiki (1000+ pages):** ~4-6 hours

### Optimization Tips
1. **Use appropriate batch sizes:** 5-10 for large wikis, 20-50 for small wikis
2. **Filter out unnecessary content:** Archives, drafts, deprecated content
3. **Run during off-peak hours:** Less API rate limiting
4. **Use fast network connection:** Reduces transfer time
5. **Monitor system resources:** Ensure adequate memory and CPU

## 🔍 Troubleshooting Examples

### Common Error Scenarios

#### Authentication Failure
```bash
# Test credentials
python -c "
import os
from migration.azure_devops_migrator import test_connections
test_connections()
"
```

#### Rate Limiting
```bash
# Use slower processing
python migration/azure_devops_migrator.py --wiki "MyWiki" \
    --rate-limit 2 --batch-size 5
```

#### Content Conversion Issues
```bash
# Debug specific page
python migration/content_previewer.py --page "ProblematicPage" \
    --verbose --debug-mode
```

For more examples and detailed documentation, visit [../docs/index.html](../docs/index.html).
