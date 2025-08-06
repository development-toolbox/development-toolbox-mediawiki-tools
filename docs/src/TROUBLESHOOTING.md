# 🛠️ Troubleshooting Guide

Comprehensive troubleshooting guide for MediaWiki Migration Tools.

## 🚨 Common Issues and Solutions

### Authentication Problems

#### Issue: Azure DevOps Connection Failed
```
Error: Authentication failed for Azure DevOps API
```

**Solutions:**
1. **Verify Personal Access Token (PAT)**
   ```bash
   # Test your PAT
   curl -u :YOUR_PAT https://dev.azure.com/YOUR_ORG/_apis/projects
   ```

2. **Check PAT Permissions**
   Required scopes:
   - ✅ `Wiki (Read)`
   - ✅ `Project and Team (Read)`
   - ✅ `Work Items (Read)` (if migrating work item links)

3. **Validate Environment Variables**
   ```bash
   # Check .env file
   cat migration/.env

   # Test configuration
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv('migration/.env')
   print('Org:', os.getenv('AZURE_DEVOPS_ORG'))
   print('Project:', os.getenv('AZURE_DEVOPS_PROJECT'))
   print('Token set:', bool(os.getenv('AZURE_DEVOPS_TOKEN')))
   "
   ```

#### Issue: MediaWiki API Connection Failed
```
Error: Cannot connect to MediaWiki API
```

**Solutions:**
1. **Test MediaWiki API Endpoint**
   ```bash
   curl "https://your-mediawiki.com/api.php?action=query&meta=siteinfo&format=json"
   ```

2. **Verify Bot Credentials**
   - Create a bot user in MediaWiki
   - Grant appropriate permissions
   - Use bot credentials in `.env` file

3. **Check API Permissions**
   Required rights:
   - ✅ `edit` - Edit pages
   - ✅ `createpage` - Create new pages
   - ✅ `upload` - Upload files (for images)

### Content Conversion Issues

#### Issue: Complex Tables Not Converting Properly
```
Error: Table conversion failed or malformed output
```

**Solutions:**
1. **Preview Before Migration**
   ```bash
   python migration/content_previewer.py --page "TablePage" --verbose
   ```

2. **Manual Table Conversion**
   ```bash
   # Extract tables for manual review
   python migration/content_previewer.py --page "TablePage" \
       --extract-tables --output-dir "./manual_review"
   ```

3. **Simplify Source Tables**
   - Remove merged cells before migration
   - Avoid complex HTML formatting
   - Use standard Markdown table syntax

#### Issue: Code Blocks Missing Syntax Highlighting
```
Warning: Unknown language 'powershell' - using plain text
```

**Solutions:**
1. **Check Supported Languages**
   ```bash
   python -c "
   from migration.content_converter import get_supported_languages
   print('Supported languages:', get_supported_languages())
   "
   ```

2. **Language Mapping**
   Update language mappings in converter:
   ```python
   # migration/content_converter.py
   LANGUAGE_MAPPINGS = {
       'powershell': 'bash',
       'cmd': 'bash',
       'shell': 'bash'
   }
   ```

#### Issue: Images Not Displaying
```
Warning: Image migration requires manual handling
```

**Solutions:**
1. **Download Images from Azure DevOps**
   ```bash
   # Use the image extractor tool
   python migration/image_extractor.py --wiki "MyWiki" \
       --output-dir "./images"
   ```

2. **Bulk Upload to MediaWiki**
   ```bash
   python migration/image_uploader.py --input-dir "./images" \
       --mediawiki-url "https://your-wiki.com"
   ```

3. **Update Image References**
   ```bash
   python migration/link_updater.py --update-images
   ```

### Performance Issues

#### Issue: Migration Taking Too Long
```
Info: Processing page 50 of 500... (estimated 4 hours remaining)
```

**Solutions:**
1. **Optimize Batch Size**
   ```bash
   # For small pages (< 10KB each)
   python migration/azure_devops_migrator.py --wiki "MyWiki" --batch-size 50

   # For large pages (> 100KB each)
   python migration/azure_devops_migrator.py --wiki "MyWiki" --batch-size 5
   ```

2. **Use Content Filtering**
   ```bash
   # Skip archived content
   python migration/azure_devops_migrator.py --wiki "MyWiki" \
       --exclude-pattern "Archive/*,Old/*"

   # Migrate only recent content
   python migration/azure_devops_migrator.py --wiki "MyWiki" \
       --modified-after "2023-01-01"
   ```

3. **Parallel Processing (Experimental)**
   ```bash
   python migration/azure_devops_migrator.py --wiki "MyWiki" \
       --parallel-workers 3 --batch-size 10
   ```

#### Issue: Rate Limiting from APIs
```
Error: Rate limit exceeded (429) - retrying in 60 seconds
```

**Solutions:**
1. **Adjust Rate Limiting**
   ```bash
   python migration/azure_devops_migrator.py --wiki "MyWiki" \
       --rate-limit 3  # 3 seconds between requests
   ```

2. **Use Exponential Backoff**
   ```bash
   python migration/azure_devops_migrator.py --wiki "MyWiki" \
       --backoff-strategy exponential --max-retries 5
   ```

3. **Run During Off-Peak Hours**
   - Schedule migrations during low-traffic periods
   - Consider timezone differences for global teams

### Environment Issues

#### Issue: Python Path Problems on Windows
```
Error: 'python' is not recognized as an internal or external command
```

**Solutions:**
1. **Use Full Python Path**
   ```bash
   # Find Python installation
   where python

   # Use full path
   C:\Users\YourUser\AppData\Local\Programs\Python\Python39\python.exe getting_started.py
   ```

2. **Update PATH Environment Variable**
   ```bash
   # Add Python to PATH (PowerShell as Administrator)
   $env:PATH += ";C:\Users\YourUser\AppData\Local\Programs\Python\Python39"
   ```

3. **Use Getting Started Script**
   ```bash
   # The script handles Python path detection automatically
   python getting_started.py
   ```

#### Issue: Git Bash Not Detected Properly
```
Warning: Could not detect Git Bash environment
```

**Solutions:**
1. **Verify Git Bash Installation**
   ```bash
   # In Git Bash, check version
   git --version
   bash --version
   ```

2. **Run with Explicit Shell**
   ```bash
   # Force Git Bash detection
   SHELL=/usr/bin/bash python getting_started.py
   ```

3. **Manual Environment Setup**
   ```bash
   # Set environment variables manually
   export TOOLKIT_SHELL="bash"
   export TOOLKIT_OS="Windows"
   python getting_started.py
   ```

### Docker Environment Issues

#### Issue: Docker Compose Fails to Start
```
Error: Cannot connect to Docker daemon
```

**Solutions:**
1. **Verify Docker Installation**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Start Docker Desktop**
   - Ensure Docker Desktop is running
   - Check system tray for Docker icon

3. **Alternative Local Setup**
   ```bash
   # Use XAMPP or similar for local MediaWiki
   python getting_started.py  # Select alternative setup
   ```

#### Issue: MediaWiki Container Memory Issues
```
Error: Container killed due to memory limit
```

**Solutions:**
1. **Increase Docker Memory Limit**
   ```yaml
   # docker-compose.yml
   services:
     mediawiki:
       mem_limit: 2g
       memswap_limit: 2g
   ```

2. **Optimize MediaWiki Configuration**
   ```php
   // LocalSettings.php
   $wgMaxShellMemory = 1024000;  // 1GB
   $wgMemoryLimit = "256M";
   ```

## 🔍 Debugging Techniques

### Enable Verbose Logging
```bash
# Maximum verbosity
python migration/azure_devops_migrator.py --wiki "MyWiki" \
    --log-level DEBUG --verbose

# Log to file
python migration/azure_devops_migrator.py --wiki "MyWiki" \
    --log-file "debug.log"
```

### Test Individual Components
```bash
# Test content conversion only
python migration/content_previewer.py --page "TestPage" --debug

# Test API connections
python migration/connection_tester.py

# Test configuration
python migration/config_validator.py
```

### Analyze Failed Pages
```bash
# Generate failure report
python migration/failure_analyzer.py --input "migration_report.md"

# Retry specific pages
python migration/azure_devops_migrator.py --wiki "MyWiki" \
    --pages "FailedPage1,FailedPage2" --verbose
```

## 📊 Performance Monitoring

### Monitor Migration Progress
```bash
# Real-time progress monitoring
tail -f migration.log | grep "Progress:"

# Generate progress report
python migration/progress_reporter.py --input "migration.log"
```

### Resource Usage
```bash
# Monitor system resources
htop  # Linux/macOS
taskmgr  # Windows

# Monitor Python memory usage
python migration/memory_profiler.py --wiki "MyWiki"
```

## 🆘 Getting Help

### Collect Diagnostic Information
```bash
# Generate diagnostic report
python migration/diagnostic_tool.py --output "diagnostic_report.txt"

# This includes:
# - System information
# - Python environment
# - Configuration validation
# - Recent error logs
# - Performance metrics
```

### Report Issues
When reporting issues, include:

1. **Diagnostic Report**
   ```bash
   python migration/diagnostic_tool.py --output "diagnostic_report.txt"
   ```

2. **Error Logs**
   ```bash
   # Last 100 lines of migration log
   tail -100 migration.log
   ```

3. **Sample Content**
   - Provide examples of content that failed to convert
   - Include source Azure DevOps URLs (if public)

4. **Environment Details**
   - Operating system and version
   - Python version
   - Shell environment (Git Bash, PowerShell, etc.)

### Emergency Recovery
If migration fails partway through:

1. **Don't Panic** - Progress is saved automatically
2. **Check Logs** - Review migration.log for last successful page
3. **Resume Migration** - Use `--resume-from` parameter
4. **Contact Support** - Include diagnostic report

```bash
# Emergency recovery
python migration/azure_devops_migrator.py --wiki "MyWiki" \
    --resume-from "Last Successful Page" \
    --log-level DEBUG
```

## 📞 Support Channels

- **📖 Documentation:** [../docs/index.html](../docs/index.html)
- **🐛 GitHub Issues:** [Report Issues](https://github.com/development-toolbox/development-toolbox-mediawiki-tools/issues)
- **💬 Discussions:** [GitHub Discussions](https://github.com/development-toolbox/development-toolbox-mediawiki-tools/discussions)
- **📧 Email Support:** [Contact Team](mailto:support@development-toolbox.com)

## 🔄 Continuous Improvement

Help us improve the tools by:

1. **Reporting Bugs** - Even small issues help
2. **Suggesting Features** - What would make migration easier?
3. **Contributing Examples** - Share your successful migration patterns
4. **Documentation Updates** - Help improve these guides

Thank you for using MediaWiki Migration Tools! 🚀
