# Template Management Tools

Tools for managing MediaWiki templates including import, export, and validation.

## 🎨 Available Template Tools

### Template Importer
Bulk import MediaWiki templates from local files.

**Files:**
- `mediawiki_import.py` - Template import script
- `.env.template` - Configuration template

### Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.template` to `.env` and configure
3. Run import: `python mediawiki_import.py`

### Template Format
Templates should be saved as `.mediawiki` files with the naming convention:
`Template_TemplateName.mediawiki`
