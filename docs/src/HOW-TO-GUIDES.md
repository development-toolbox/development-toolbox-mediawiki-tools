# 📚 How-To Guides

Complete collection of step-by-step guides for MediaWiki migration scenarios.

## 🎯 Quick Reference

| Scenario | Wiki Size | Complexity | Time Estimate | Guide |
|----------|-----------|------------|---------------|--------|
| Small Team | 10-50 pages | Low | 15-30 min | [Quick Migration](#quick-migration) |
| Department | 100-500 pages | Medium | 2-4 hours | [Department Migration](#department-migration) |
| Enterprise | 500+ pages | High | 1-2 days | [Enterprise Migration](#enterprise-migration) |

## 🚀 Quick Migration (10-50 pages)

**Best for:** Small team wikis, simple documentation, proof-of-concept migrations.

### Prerequisites
- ✅ Azure DevOps access with wiki read permissions
- ✅ MediaWiki admin access
- ✅ Python 3.7+ installed
- ✅ Stable internet connection

### Step 1: Environment Setup (5 minutes)
```bash
# Clone the repository
git clone https://github.com/development-toolbox/development-toolbox-mediawiki-tools.git
cd development-toolbox-mediawiki-tools

# Interactive setup (recommended)
python getting_started.py
# Select: "📦 Azure DevOps Wiki Migration"
```

### Step 2: Quick Analysis (2 minutes)
```bash
# Analyze your wiki complexity
python migration/migration_planner.py --wiki "TeamDocs"

# Expected output: Low complexity score, minimal issues
```

### Step 3: Content Preview (3 minutes)
```bash
# Preview key pages to verify conversion quality
python migration/content_previewer.py --page "Home"
python migration/content_previewer.py --page "Setup Guide"

# Generate sample previews
python migration/content_previewer.py --sample-pages 5
```

### Step 4: Execute Migration (10-20 minutes)
```bash
# Run the migration
python migration/azure_devops_migrator.py --wiki "TeamDocs"

# Monitor progress in real-time
tail -f migration.log
```

### Step 5: Validation (2 minutes)
```bash
# Validate migrated content
python migration/validation_tool.py --wiki "TeamDocs"

# Check for any issues
cat conversion_issues.md
```

### Success Checklist
- ✅ All pages migrated successfully
- ✅ Formatting preserved
- ✅ Links working correctly
- ✅ No critical errors in logs
- ✅ Users can access new wiki

---

## 🏢 Department Migration (100-500 pages)

**Best for:** Large teams, complex content structure, multiple content types.

### Prerequisites
- ✅ All Quick Migration prerequisites
- ✅ Development MediaWiki instance for testing
- ✅ Backup of source content
- ✅ 4-6 hour time block

### Phase 1: Strategic Planning (30 minutes)

#### 1.1 Comprehensive Analysis
```bash
# Detailed analysis with export
python migration/migration_planner.py --wiki "DeptWiki" \
    --detailed --export-analysis --output "analysis_report.json"

# Review the generated report
cat migration_analysis_report.md
```

#### 1.2 Content Categorization
```bash
# Categorize all content
python migration/content_previewer.py --all-pages \
    --categorize --output-dir "./content_analysis"

# Review categorization results
ls -la content_analysis/
```

#### 1.3 Migration Strategy
Based on analysis results:
- **High Priority:** Current documentation, frequently accessed pages
- **Medium Priority:** Reference materials, procedures
- **Low Priority:** Archive content, deprecated pages

### Phase 2: Test Migration (45 minutes)

#### 2.1 Setup Test Environment
```bash
# Start local MediaWiki for testing
docker-compose up -d

# Verify test environment
curl http://localhost:8080/api.php
```

#### 2.2 Test with Sample Content
```bash
# Test migration with high-priority pages only
python migration/azure_devops_migrator.py --wiki "DeptWiki" \
    --pages "Home,Getting Started,FAQ,Procedures" \
    --target-url "http://localhost:8080/api.php" \
    --dry-run

# Review test results
python migration/validation_tool.py --wiki "DeptWiki" \
    --target-url "http://localhost:8080/api.php"
```

### Phase 3: Production Migration (2-3 hours)

#### 3.1 High Priority Content
```bash
# Migrate current, high-priority content first
python migration/azure_devops_migrator.py --wiki "DeptWiki" \
    --modified-after "2023-01-01" \
    --exclude-pattern "Archive/*,Draft/*" \
    --batch-size 25
```

#### 3.2 Medium Priority Content
```bash
# Migrate reference materials
python migration/azure_devops_migrator.py --wiki "DeptWiki" \
    --include-pattern "Reference/*,Procedures/*" \
    --batch-size 20
```

#### 3.3 Archive Content (Optional)
```bash
# Migrate archive content to separate namespace
python migration/azure_devops_migrator.py --wiki "DeptWiki" \
    --include-pattern "Archive/*" \
    --target-namespace "Archive" \
    --batch-size 10
```

### Phase 4: Validation and Cleanup (30 minutes)

#### 4.1 Comprehensive Validation
```bash
# Validate all migrated content
python migration/validation_tool.py --wiki "DeptWiki" \
    --comprehensive --output "validation_report.md"
```

#### 4.2 Issue Resolution
```bash
# Identify pages requiring manual review
cat conversion_issues.md

# Retry failed pages
python migration/azure_devops_migrator.py --wiki "DeptWiki" \
    --retry-failed --verbose
```

### Success Metrics for Department Migration
- **Content Coverage:** >95% of pages migrated
- **Link Integrity:** >90% of internal links working
- **Formatting Quality:** >90% of formatting preserved
- **User Satisfaction:** >85% positive feedback

---

## 🌐 Enterprise Migration (500+ pages)

**Best for:** Organization-wide wikis, legacy content, complex governance requirements.

### Prerequisites
- ✅ All Department Migration prerequisites
- ✅ Enterprise MediaWiki environment
- ✅ Dedicated migration team
- ✅ 1-2 week time allocation
- ✅ Stakeholder alignment
- ✅ Change management plan

### Phase 1: Strategic Assessment (1 day)

#### 1.1 Enterprise Analysis
```bash
# Comprehensive enterprise analysis
python migration/migration_planner.py --wiki "EnterpriseWiki" \
    --detailed --export-analysis --complexity-scoring \
    --output "enterprise_analysis.json"

# Generate executive summary
python migration/report_generator.py --input "enterprise_analysis.json" \
    --format executive-summary --output "executive_summary.pdf"
```

#### 1.2 Content Audit
```bash
# Full content audit
python migration/content_auditor.py --wiki "EnterpriseWiki" \
    --deep-analysis --export-inventory \
    --output-dir "./content_inventory"

# Analyze content ownership and governance
python migration/governance_analyzer.py --wiki "EnterpriseWiki"
```

#### 1.3 Risk Assessment
```bash
# Identify high-risk content
python migration/risk_analyzer.py --wiki "EnterpriseWiki" \
    --output "risk_assessment.md"

# Generate mitigation strategies
python migration/mitigation_planner.py --input "risk_assessment.md"
```

### Phase 2: Pilot Migration (2-3 days)

#### 2.1 Select Pilot Content
- Choose 50-100 representative pages
- Include various content types and complexities
- Select both current and legacy content

```bash
# Create pilot page list
echo "Home
Getting Started
API Documentation
Legacy Archive Page
Complex Table Page" > pilot_pages.txt

# Execute pilot migration
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --pages-file "pilot_pages.txt" \
    --target-namespace "Pilot" \
    --verbose --detailed-logging
```

#### 2.2 Pilot Validation
```bash
# Comprehensive pilot validation
python migration/validation_tool.py --wiki "EnterpriseWiki" \
    --namespace "Pilot" --comprehensive \
    --user-acceptance-testing --output "pilot_report.md"
```

#### 2.3 Stakeholder Review
- Conduct stakeholder demos
- Gather feedback and requirements
- Adjust migration strategy based on results

### Phase 3: Phased Production Migration (1-2 weeks)

#### 3.1 Current Content Migration (3-4 days)
```bash
# Phase 1: Critical business content
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --modified-after "2023-06-01" \
    --priority-pattern "Critical/*,Business/*,Current/*" \
    --batch-size 15 --rate-limit 2

# Phase 2: Department-specific content
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --include-pattern "Engineering/*,Sales/*,Support/*" \
    --modified-after "2023-01-01" \
    --batch-size 20
```

#### 3.2 Reference Content Migration (2-3 days)
```bash
# Phase 3: Reference and documentation
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --include-pattern "Reference/*,Documentation/*,Procedures/*" \
    --batch-size 25 --parallel-workers 2
```

#### 3.3 Archive Content Migration (2-3 days)
```bash
# Phase 4: Historical and archive content
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --include-pattern "Archive/*,Historical/*,Legacy/*" \
    --target-namespace "Archive" \
    --batch-size 10 --rate-limit 3
```

### Phase 4: Enterprise Validation (1-2 days)

#### 4.1 Automated Validation
```bash
# Comprehensive enterprise validation
python migration/validation_tool.py --wiki "EnterpriseWiki" \
    --enterprise-mode --all-namespaces \
    --link-validation --content-integrity \
    --performance-testing --output "enterprise_validation.pdf"
```

#### 4.2 User Acceptance Testing
```bash
# Generate UAT test cases
python migration/uat_generator.py --wiki "EnterpriseWiki" \
    --user-scenarios --test-data \
    --output "uat_test_cases.md"

# Monitor UAT results
python migration/uat_monitor.py --track-issues \
    --report-progress --output "uat_progress.md"
```

### Phase 5: Go-Live and Support (Ongoing)

#### 5.1 Go-Live Checklist
- ✅ All critical content migrated
- ✅ User training completed
- ✅ Support procedures established
- ✅ Monitoring systems active
- ✅ Rollback plan ready

#### 5.2 Post-Migration Monitoring
```bash
# Setup monitoring
python migration/monitoring_setup.py --wiki "EnterpriseWiki" \
    --alerts --dashboards --reporting

# Weekly health checks
python migration/health_checker.py --wiki "EnterpriseWiki" \
    --comprehensive --trending --output "weekly_report.md"
```

## 🛠️ Advanced Techniques

### Content Transformation Workflows

#### Custom Content Processors
```python
# migration/custom_processors.py
from migration.content_converter import ContentConverter

class CustomEnterpriseConverter(ContentConverter):
    def process_custom_templates(self, content):
        # Custom template conversion logic
        return content

    def handle_enterprise_links(self, content):
        # Enterprise-specific link processing
        return content
```

#### Bulk Content Operations
```bash
# Bulk find and replace
python migration/bulk_editor.py --wiki "EnterpriseWiki" \
    --find "old-server.company.com" \
    --replace "new-server.company.com" \
    --pattern "*.md"

# Bulk template updates
python migration/template_updater.py --wiki "EnterpriseWiki" \
    --old-template "OldInfo" \
    --new-template "NewInfo" \
    --namespace "Documentation"
```

### Integration Patterns

#### CI/CD Integration
```yaml
# .github/workflows/wiki-sync.yml
name: Wiki Synchronization
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  sync-wiki:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Sync recent changes
      run: |
        python migration/incremental_sync.py --wiki "EnterpriseWiki" \
          --modified-after "$(date -d '1 day ago' '+%Y-%m-%d')"
```

#### Webhook Integration
```python
# webhook_handler.py
from flask import Flask, request
from migration.incremental_migrator import IncrementalMigrator

app = Flask(__name__)

@app.route('/webhook/azure-devops', methods=['POST'])
def handle_wiki_update():
    data = request.json
    if data['resource']['area'] == 'wiki':
        migrator = IncrementalMigrator()
        migrator.sync_page(data['resource']['path'])
    return {'status': 'processed'}
```

## 📊 Performance Optimization

### Large-Scale Migration Optimization

#### Parallel Processing
```bash
# Split large migration into parallel jobs
python migration/job_splitter.py --wiki "EnterpriseWiki" \
    --workers 4 --output-dir "./migration_jobs"

# Run parallel jobs
for job in migration_jobs/*.json; do
    python migration/azure_devops_migrator.py --job-file "$job" &
done
wait
```

#### Resource Optimization
```bash
# Memory-optimized processing
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --memory-limit 2GB --streaming-mode \
    --cache-strategy minimal

# Storage-optimized processing
python migration/azure_devops_migrator.py --wiki "EnterpriseWiki" \
    --temp-storage "/fast-ssd/temp" \
    --compress-intermediates --cleanup-on-success
```

## 🔍 Monitoring and Observability

### Real-time Monitoring
```bash
# Real-time migration dashboard
python migration/dashboard.py --wiki "EnterpriseWiki" \
    --port 8080 --real-time-updates

# Access dashboard at http://localhost:8080
```

### Alerting
```bash
# Setup alerts for migration issues
python migration/alerting_setup.py --wiki "EnterpriseWiki" \
    --email "admin@company.com" \
    --slack-webhook "https://hooks.slack.com/..." \
    --thresholds error:5,warning:20
```

## 🎓 Training and Adoption

### User Training Materials
- **Quick Start Guide:** 15-minute overview for end users
- **Power User Guide:** Advanced features and customization
- **Admin Guide:** Configuration and maintenance procedures
- **Video Tutorials:** Screen recordings of common tasks

### Change Management
1. **Communication Plan:** Regular updates to stakeholders
2. **Training Schedule:** Phased rollout of training sessions
3. **Support Structure:** Help desk and expert support
4. **Feedback Collection:** Regular surveys and improvement cycles

## 📈 Success Measurement

### Key Performance Indicators (KPIs)
- **Migration Completeness:** % of content successfully migrated
- **User Adoption Rate:** % of users actively using new wiki
- **Content Quality Score:** Automated quality assessment
- **System Performance:** Page load times and availability
- **User Satisfaction:** Survey scores and feedback ratings

### Reporting
```bash
# Generate executive dashboard
python migration/executive_dashboard.py --wiki "EnterpriseWiki" \
    --kpis --trends --export-pdf "executive_report.pdf"

# Generate technical metrics
python migration/technical_report.py --wiki "EnterpriseWiki" \
    --performance --quality --issues --export-json "tech_metrics.json"
```

---

## 🆘 Need Help?

- **📖 Documentation:** [../docs/index.html](../docs/index.html)
- **🛠️ Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **🐛 Issues:** [GitHub Issues](https://github.com/development-toolbox/development-toolbox-mediawiki-tools/issues)
- **💬 Community:** [GitHub Discussions](https://github.com/development-toolbox/development-toolbox-mediawiki-tools/discussions)

Remember: Every enterprise migration is unique. Use these guides as a starting point and adapt them to your specific requirements and constraints.

Happy migrating! 🚀
