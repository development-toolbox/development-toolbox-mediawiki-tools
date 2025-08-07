# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MediaWiki development toolkit focused on migration, maintenance, and management of MediaWiki instances. The primary use case is migrating content from Azure DevOps Wiki to MediaWiki, with additional tools for synchronization, monitoring, and template management.

## Common Development Tasks

### Initial Setup
```bash
# Run the interactive setup script
python getting_started.py

# Install core dependencies
pip install -r requirements.txt

# Install migration-specific dependencies
pip install -r migration/requirements.txt
```

### Running Migration Tools
```bash
# Analyze content before migration
python migration/migration_planner.py --wiki "WikiName"

# Preview content transformation
python migration/content_previewer.py --page "PageName"

# Run the actual migration
python migration/azure_devops_migrator.py --wiki "WikiName" --dry-run

# Validate migrated content
python migration/validation_tool.py
```

### Local Development Environment
```bash
# Start local MediaWiki instance
cd examples
docker-compose up -d

# Access at http://localhost:8080
```

### Testing Tools
```bash
# Test mode for getting started script
python getting_started.py --test-mode

# Dry-run mode for migration tools (recommended for testing)
python migration/migration_planner.py --wiki "TestWiki" --dry-run
python migration/azure_devops_migrator.py --wiki "TestWiki" --dry-run --batch-size 1
```

## Code Architecture

### Core Components

1. **getting_started.py**: Interactive setup script that detects the environment and creates `.toolkit_env` configuration. Provides menu-driven interface for tool selection.

2. **migration/**: Core migration toolkit
   - `migration_planner.py`: Analyzes Azure DevOps wiki content, calculates complexity scores, estimates migration time
   - `azure_devops_migrator.py`: Performs actual content migration with API integration
   - `content_previewer.py`: Shows how content will be transformed during migration
   - `validation_tool.py`: Validates migrated content for issues

3. **Environment Configuration**: Uses `.toolkit_env` file to store toolkit-specific settings without affecting system environment

### Key Design Patterns

- **Session-based API clients**: All migration tools use `requests.Session` for efficient API calls
- **Dry-run support**: Migration tools support `--dry-run` flag for safe testing
- **Comprehensive error handling**: Tools provide detailed error messages and recovery suggestions
- **Cross-platform compatibility**: Supports Windows (Git Bash recommended), macOS, and Linux

### Dependencies

- Core: `requests`, `python-dotenv`
- Optional: `beautifulsoup4` (HTML parsing), `schedule` (monitoring), `click` (CLI)

## Important Conventions

- All Python scripts are executable with shebang `#!/usr/bin/env python3`
- Environment variables prefixed with `TOOLKIT_` to avoid conflicts
- Tools read Azure DevOps credentials from environment variables or `.env` file
- Migration tools use comprehensive docstrings with type hints
- Error messages include actionable recovery steps
- never use wording like production-ready, Production-ready or anything like that!. that's just bad wording.