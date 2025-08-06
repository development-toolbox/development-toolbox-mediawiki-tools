# Complete Azure DevOps to MediaWiki Migration Guide

This guide walks you through the entire process of migrating your Azure DevOps wiki to MediaWiki, from initial planning to final validation.

## 🎯 Overview

**Estimated Time**: 2-8 hours (depending on wiki size and complexity)
**Difficulty**: Intermediate
**Prerequisites**: Basic command line knowledge, admin access to both systems

## 📋 Phase 1: Pre-Migration Planning (30-60 minutes)

### Step 1.1: Set Up Your Migration Environment

1. **Clone the migration tools repository:**
   ```bash
   git clone https://github.com/development-toolbox/development-toolbox-mediawiki-tools.git
   cd development-toolbox-mediawiki-tools
   ```

2. **Set up Python environment:**
   ```bash
   # Install dependencies
   cd migration
   pip install -r requirements.txt
   ```

3. **Configure your environment:**
   ```bash
   # Copy environment template
   cp .env.template .env

   # Edit .env with your credentials
   notepad .env  # Windows
   nano .env     # Linux/Mac
   ```

4. **Required credentials:**
   - **Azure DevOps PAT**: Go to Azure DevOps → Settings → Personal Access Tokens → New Token
     - Scopes needed: `Wiki (Read)`
   - **MediaWiki credentials**: Admin user with page creation permissions

### Step 1.2: Analyze Your Current Wiki

1. **Run the pre-migration analysis:**
   ```bash
   python migration_planner.py
   ```

2. **Review the generated report:**
   - Open `migration_analysis_report.md`
   - Note pages requiring special attention
   - Estimate total migration time
   - Identify images and attachments that need manual handling

3. **Key things to look for:**
   - Number of pages with high complexity
   - Total number of images/attachments
   - Pages with tables or HTML content
   - Internal links that might break

### Step 1.3: Preview Content Conversion

1. **Run content preview tool:**
   ```bash
   python content_previewer.py
   ```

2. **Choose preview option:**
   - Select "Sample pages" for first-time migration
   - Select "Specific page" if you want to test a particular page

3. **Review the preview report:**
   - Open `content_preview_report.md`
   - Check if the conversion looks acceptable
   - Note any major formatting issues

✅ **Phase 1 Checkpoint**: You should now have a clear understanding of your migration scope and complexity.

---

## 🛠️ Phase 2: MediaWiki Preparation (30-45 minutes)

### Step 2.1: Set Up MediaWiki Test Environment

1. **Option A: Use Docker (Recommended for testing)**
   ```bash
   cd ../examples
   docker-compose up -d
   # MediaWiki will be available at http://localhost:8080
   ```

2. **Option B: Use existing MediaWiki**
   - Ensure you have admin access
   - Create a backup before testing

### Step 2.2: Configure MediaWiki

1. **Enable necessary extensions** (if not already enabled):
   - **SyntaxHighlight_GeSHi**: For code blocks
   - **ParserFunctions**: For advanced templates
   - **WikiEditor**: Better editing experience

2. **Test basic functionality:**
   - Create a test page with various formatting
   - Verify code highlighting works
   - Test table creation

### Step 2.3: Prepare for Images and Attachments

1. **Create directory for downloaded assets:**
   ```bash
   mkdir -p ../assets/images
   mkdir -p ../assets/attachments
   ```

2. **Plan image handling strategy:**
   - Will you migrate all images or just essential ones?
   - Do you need to optimize image sizes?
   - How will you handle internal image links?

✅ **Phase 2 Checkpoint**: Your MediaWiki is ready and you have a plan for handling multimedia content.

---

## 🚀 Phase 3: Test Migration (45-90 minutes)

### Step 3.1: Run Small Test Migration

1. **Start with low-complexity pages:**
   ```bash
   # Edit your .env to point to test MediaWiki
   python azure_devops_migrator.py
   ```

2. **If you want to test specific pages first:**
   - Modify the migration script to filter pages
   - Or manually test with content previewer first

### Step 3.2: Verify Test Results

1. **Check migrated content:**
   - Visit your test MediaWiki
   - Navigate to migrated pages
   - Verify formatting looks correct

2. **Common issues to check:**
   - Are headers formatted correctly?
   - Do tables display properly?
   - Are code blocks highlighted?
   - Do internal links work?

3. **Document any issues:**
   - Note pages that need manual adjustment
   - Identify patterns in conversion problems

### Step 3.3: Handle Images and Attachments

1. **Download images from Azure DevOps:**
   - This must be done manually (Azure DevOps API limitation)
   - Save images to your `assets/images/` directory
   - Note the original URLs for link replacement

2. **Upload images to MediaWiki:**
   ```bash
   # Use MediaWiki's Special:Upload or bulk upload tools
   # Document new image URLs for link updates
   ```

3. **Update image references:**
   - Find pages with broken image links
   - Replace with new MediaWiki image URLs
   - Test that images display correctly

✅ **Phase 3 Checkpoint**: You've successfully tested the migration process and resolved any major issues.

---

## 🎯 Phase 4: Production Migration (1-4 hours)

### Step 4.1: Prepare Production Environment

1. **Back up your current MediaWiki** (if existing):
   ```bash
   # Database backup
   mysqldump -u username -p wiki_db > mediawiki_backup.sql

   # Files backup
   tar -czf mediawiki_files_backup.tar.gz /path/to/mediawiki/
   ```

2. **Update .env for production:**
   - Change WIKI_URL to production MediaWiki
   - Use production credentials
   - Double-check all settings

### Step 4.2: Execute Full Migration

1. **Run the complete migration:**
   ```bash
   python azure_devops_migrator.py > migration.log 2>&1
   ```

2. **Monitor progress:**
   - Watch the console output
   - Check `migration.log` if any errors occur
   - Note pages that fail to migrate

3. **Handle failed pages:**
   - Review failed pages manually
   - Often caused by special characters in titles
   - May need manual creation with sanitized titles

### Step 4.3: Post-Migration Content Review

1. **Review high-complexity pages:**
   - Visit each page identified in your analysis
   - Verify tables, code blocks, and formatting
   - Fix any issues manually

2. **Update internal links:**
   - Search for broken internal links
   - Update page references if page titles changed
   - Consider creating redirect pages for old URLs

3. **Upload remaining images:**
   - Complete image uploads started in testing phase
   - Update all image references in migrated content
   - Verify all images display correctly

✅ **Phase 4 Checkpoint**: Your complete wiki has been migrated to MediaWiki.

---

## ✅ Phase 5: Validation & Cleanup (30-60 minutes)

### Step 5.1: Content Validation

1. **Spot-check migrated content:**
   - Review a sample of pages from each complexity level
   - Verify formatting, links, and functionality
   - Test search functionality

2. **Run validation script** (if available):
   ```bash
   python ../monitoring/wiki_health_check.py  # Coming soon
   ```

### Step 5.2: User Access Setup

1. **Configure user accounts:**
   - Import user accounts or set up new ones
   - Configure user groups and permissions
   - Test user access and editing capabilities

2. **Set up authentication:**
   - Configure SSO if needed
   - Set up user groups matching your organization
   - Test login and permissions

### Step 5.3: Final Documentation

1. **Create user migration guide:**
   - Document key differences between Azure DevOps wiki and MediaWiki
   - Provide editing guidelines
   - Share new wiki URL and access instructions

2. **Document any manual changes:**
   - List pages that needed manual adjustment
   - Note any ongoing maintenance requirements
   - Create troubleshooting guide for common issues

✅ **Phase 5 Checkpoint**: Migration complete and validated!

---

## 🎉 Phase 6: Go-Live & Support (Ongoing)

### Step 6.1: Announce the Migration

1. **Communicate to stakeholders:**
   - Send announcement with new wiki URL
   - Provide basic usage instructions
   - Share timeline for Azure DevOps wiki shutdown (if applicable)

2. **Provide training if needed:**
   - MediaWiki editing differences
   - New search and navigation features
   - How to create and edit pages

### Step 6.2: Monitor and Support

1. **Monitor usage:**
   - Watch for user issues or confusion
   - Check wiki performance and availability
   - Monitor search functionality

2. **Ongoing maintenance:**
   - Regular backups
   - MediaWiki updates
   - User account management

---

## 🚨 Common Issues & Troubleshooting

### Authentication Issues

**Problem**: Cannot connect to Azure DevOps or MediaWiki
**Solutions**:
- Verify Personal Access Token has correct permissions
- Check if MediaWiki API is enabled
- For SSO: Use bot passwords or API tokens
- Test API access manually with curl

### Content Conversion Issues

**Problem**: Tables or formatting look wrong
**Solutions**:
- Check MediaWiki extensions are installed
- Verify table syntax conversion
- May need manual adjustment for complex tables

**Problem**: Code blocks not highlighted
**Solutions**:
- Install SyntaxHighlight_GeSHi extension
- Check language names in code blocks
- May need to update language identifiers

### Performance Issues

**Problem**: Migration is very slow
**Solutions**:
- Add delays between requests
- Process pages in smaller batches
- Check network connectivity and API rate limits

### Image Issues

**Problem**: Images not displaying
**Solutions**:
- Images must be uploaded manually to MediaWiki
- Update image URLs in page content after upload
- Check MediaWiki upload permissions

---

## 📊 Success Metrics

After migration, you should have:
- ✅ All pages migrated with acceptable formatting
- ✅ Internal links working correctly
- ✅ Images and attachments accessible
- ✅ Users able to access and edit content
- ✅ Search functionality working
- ✅ Backup and recovery procedures in place

---

## 🔗 Additional Resources

- **MediaWiki Documentation**: https://www.mediawiki.org/wiki/Documentation
- **Migration Tools Repository**: https://github.com/development-toolbox/development-toolbox-mediawiki-tools
- **Azure DevOps Wiki API**: https://docs.microsoft.com/en-us/rest/api/azure/devops/wiki/

---

## 📞 Getting Help

If you encounter issues during migration:

1. **Check the troubleshooting section** above
2. **Review generated reports** for specific guidance
3. **Test individual components** to isolate issues
4. **Use the preview tools** to understand conversion behavior
5. **Create GitHub issues** in the tools repository for bugs

**Remember**: Take your time, test thoroughly, and don't hesitate to run additional previews if something doesn't look right!

---

*This guide is part of the development-toolbox-mediawiki-tools project*
