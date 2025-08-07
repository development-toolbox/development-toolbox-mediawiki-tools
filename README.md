# Development Toolbox - MediaWiki Tools

This repository contains a collection of Python scripts designed to assist with the management, migration, and maintenance of MediaWiki instances. It is the designated toolset for handling MediaWiki-related tasks within the `development-toolbox` ecosystem.

The primary entry point is the `getting_started.py` script, which configures the local environment to ensure all tools and their dependencies operate correctly and consistently.

## About the `development-toolbox` Organization

The `development-toolbox` is a GitHub organization focused on centralizing essential development scripts and tools. The goal is to provide a structured, well-documented, and automated suite of utilities to solve common development and infrastructure challenges.

This repository is one component of that larger ecosystem.

<!-- REPO_LIST_START -->
For an interactive, browsable catalogue of all public repositories, you can view:
- **Live (GitHub Pages):** [Repo Catalogue](https://development-toolbox.github.io/development-toolbox-mediawiki-tools/repolist.html)
- **Local preview:** [Repo Catalogue](docs/site/repolist.html)

To re regenerate Repo Catalogue locally  run:
```bash
python generate_repolist_html.py
```
<!-- REPO_LIST_END -->

## Current Features

*   **Interactive Setup Script (`getting_started.py`):** An interactive script that guides you through the initial setup. It detects your operating system, sets up necessary configurations, and helps you install required dependencies, ensuring a smooth start.
*   **Documentation Website:** A comprehensive documentation site is available and deployed via GitHub Pages. It includes guides, examples, and technical references.

## Planned Features

The following toolsets are planned for future development:

*   **Migration Tools:** A robust suite for migrating content from various sources (e.g., Azure DevOps Wiki) to MediaWiki.
*   **Synchronization Tools:** Scripts for keeping MediaWiki content synchronized with external repositories or sources.
*   **Maintenance Scripts:** Utilities for database optimization, link checking, and other routine maintenance tasks.
*   **Template Management:** Tools for bulk importing, exporting, and validating MediaWiki templates.
*   **Monitoring & Deployment:** Scripts for health checks, performance monitoring, and automated deployment/updates.

## Getting Started

1.  Clone the repository:
    ```bash
    git clone https://github.com/development-toolbox/development-toolbox-mediawiki-tools.git
    cd development-toolbox-mediawiki-tools
    ```

2.  Run the setup script:
    ```bash
    python getting_started.py
    ```
    This will guide you through the necessary configuration steps.

## Contributing

Contributions are highly welcome and encouraged. This project is intended to be a collaborative effort. If you have a script, a bug fix, or an improvement, please feel free to contribute.

Please refer to the `CONTRIBUTING.md` file and the documentation site for guidelines on how to get started with development, testing, and submitting pull requests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
