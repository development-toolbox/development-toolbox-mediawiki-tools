#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for MediaWiki migration tools tests.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

import pytest
import requests_mock
import responses


@pytest.fixture
def mock_env_vars():
    """Fixture providing mock environment variables for testing."""
    return {
        'AZURE_DEVOPS_ORGANIZATION': 'test-org',
        'AZURE_DEVOPS_PROJECT': 'test-project', 
        'AZURE_DEVOPS_PAT': 'test-pat-token-123',
        'AZURE_WIKI_NAME': 'TestWiki',
        'WIKI_URL': 'http://localhost:8080',
        'WIKI_USERNAME': 'testuser',
        'WIKI_PASSWORD': 'testpass123',
        'TEMPLATE_DIR': 'test-templates'
    }


@pytest.fixture
def mock_azure_api_response():
    """Fixture providing mock Azure DevOps API responses."""
    return {
        'wikis': {
            'value': [
                {
                    'id': 'wiki-123',
                    'name': 'TestWiki',
                    'type': 'codeWiki',
                    'url': 'https://dev.azure.com/test-org/test-project/_apis/wiki/wikis/wiki-123'
                }
            ]
        },
        'pages': {
            'value': [
                {
                    'id': 'page-1',
                    'path': '/Home',
                    'order': 0,
                    'gitItemPath': '/Home.md',
                    'subPages': []
                },
                {
                    'id': 'page-2', 
                    'path': '/Documentation/Setup',
                    'order': 1,
                    'gitItemPath': '/Documentation/Setup.md',
                    'subPages': []
                },
                {
                    'id': 'page-3',
                    'path': '/API/Reference',
                    'order': 2,
                    'gitItemPath': '/API/Reference.md',
                    'subPages': []
                }
            ]
        },
        'page_content': {
            'page-1': '# Welcome\n\nThis is the **home page** with some content.\n\n## Features\n- Feature 1\n- Feature 2',
            'page-2': '# Setup Documentation\n\n```bash\nnpm install\n```\n\n![Setup Diagram](images/setup.png)',
            'page-3': '# API Reference\n\n| Method | Endpoint | Description |\n|--------|----------|-------------|\n| GET | /api/users | Get users |'
        }
    }


@pytest.fixture 
def mock_mediawiki_api_response():
    """Fixture providing mock MediaWiki API responses."""
    return {
        'login_token': {
            'query': {
                'tokens': {
                    'logintoken': 'test-login-token-456'
                }
            }
        },
        'login_success': {
            'login': {
                'result': 'Success',
                'lguserid': 1,
                'lgusername': 'testuser'
            }
        },
        'edit_token': {
            'query': {
                'tokens': {
                    'csrftoken': 'test-edit-token-789'
                }
            }
        },
        'edit_success': {
            'edit': {
                'result': 'Success',
                'pageid': 100,
                'title': 'Test Page',
                'contentmodel': 'wikitext',
                'oldrevid': 1,
                'newrevid': 2
            }
        },
        'all_pages': {
            'query': {
                'allpages': [
                    {'pageid': 1, 'ns': 0, 'title': 'Home'},
                    {'pageid': 2, 'ns': 0, 'title': 'Documentation Setup'}, 
                    {'pageid': 3, 'ns': 0, 'title': 'API Reference'}
                ]
            }
        },
        'page_content': {
            'query': {
                'pages': {
                    '1': {
                        'pageid': 1,
                        'title': 'Home',
                        'revisions': [{
                            '*': '= Welcome =\n\nThis is the \'\'\'home page\'\'\' with some content.\n\n== Features ==\n* Feature 1\n* Feature 2'
                        }]
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_markdown_content():
    """Fixture providing sample markdown content for testing conversion."""
    return """# Main Title

This is a **bold** and *italic* text example.

## Sub Title

Here's a [link](https://example.com) and some `inline code`.

### Code Block

```python
def hello_world():
    print("Hello, World!")
```

### List Examples

- Item 1
- Item 2
  - Nested item
- Item 3

1. Numbered item 1
2. Numbered item 2

### Table Example

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

### Image Example

![Alt text](images/example.png)

### HTML Example

<div class="custom-div">
<p>Some HTML content</p>
</div>
"""


@pytest.fixture
def sample_mediawiki_content():
    """Fixture providing sample MediaWiki content for validation testing."""
    return """= Main Title =

This is a '''bold''' and ''italic'' text example.

== Sub Title ==

Here's a [https://example.com link] and some <code>inline code</code>.

=== Code Block ===

<syntaxhighlight lang="python">
def hello_world():
    print("Hello, World!")
</syntaxhighlight>

=== List Examples ===

* Item 1
* Item 2
** Nested item
* Item 3

# Numbered item 1
# Numbered item 2

=== Table Example ===

{| class="wikitable"
|-
! Column 1
! Column 2  
! Column 3
|-
| Data 1
| Data 2
| Data 3
|-
| Data 4
| Data 5
| Data 6
|}

=== Image Example ===

[[File:example.png|thumb|Alt text]]
"""


@pytest.fixture
def temp_directory():
    """Fixture providing a temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_env_file(temp_directory):
    """Fixture creating a temporary .env file for testing."""
    env_file = temp_directory / '.env'
    env_content = """# Test Environment Variables
AZURE_DEVOPS_ORGANIZATION=test-org
AZURE_DEVOPS_PROJECT=test-project
AZURE_DEVOPS_PAT=test-pat-token-123
AZURE_WIKI_NAME=TestWiki
WIKI_URL=http://localhost:8080
WIKI_USERNAME=testuser
WIKI_PASSWORD=testpass123
TEMPLATE_DIR=test-templates
"""
    env_file.write_text(env_content)
    return env_file


@pytest.fixture
def temp_template_files(temp_directory):
    """Fixture creating temporary template files for testing."""
    template_dir = temp_directory / 'templates'
    template_dir.mkdir()
    
    # Create sample template files
    (template_dir / 'InfoBox.mediawiki').write_text("""<div class="infobox">
<h3>{{{{title}}}}</h3>
<p>{{{{content}}}}</p>
</div>""")
    
    (template_dir / 'CodeBlock.wiki').write_text("""<syntaxhighlight lang="{{{{1|text}}}}">
{{{{2|No code provided}}}}
</syntaxhighlight>""")
    
    return template_dir


@pytest.fixture
def mock_requests_session():
    """Fixture providing a mocked requests session."""
    session = MagicMock()
    session.get = MagicMock()
    session.post = MagicMock()
    session.headers = {}
    return session


@pytest.fixture 
def azure_client_mock_setup():
    """Fixture setting up Azure DevOps client mocks."""
    with patch('requests.Session') as mock_session:
        mock_instance = mock_session.return_value
        mock_instance.headers = {}
        yield mock_instance


@pytest.fixture
def mediawiki_client_mock_setup():
    """Fixture setting up MediaWiki client mocks."""
    with patch('requests.Session') as mock_session:
        mock_instance = mock_session.return_value
        mock_instance.headers = {}
        yield mock_instance


@pytest.fixture
def mock_file_operations():
    """Fixture for mocking file operations."""
    with patch('builtins.open') as mock_open, \
         patch('os.path.exists') as mock_exists, \
         patch('pathlib.Path.exists') as mock_path_exists, \
         patch('pathlib.Path.mkdir') as mock_mkdir:
        
        mock_exists.return_value = True
        mock_path_exists.return_value = True
        
        yield {
            'open': mock_open,
            'exists': mock_exists,
            'path_exists': mock_path_exists,
            'mkdir': mock_mkdir
        }


@pytest.fixture
def complex_wiki_structure():
    """Fixture providing a complex wiki structure for comprehensive testing."""
    return {
        'pages': [
            {
                'id': 'root-1',
                'path': '/Home',
                'complexity': 'low',
                'word_count': 150,
                'content': '# Home\nWelcome to our wiki.\n\n## Getting Started\n- Read the documentation\n- Try the examples'
            },
            {
                'id': 'doc-1', 
                'path': '/Documentation/Installation',
                'complexity': 'medium',
                'word_count': 500,
                'content': '# Installation\n\n## Prerequisites\n\n```bash\nnpm install\n```\n\n![Install](setup.png)'
            },
            {
                'id': 'api-1',
                'path': '/API/Advanced',
                'complexity': 'high', 
                'word_count': 1200,
                'content': '''# Advanced API
                
## Complex Table
| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| GET | /api/v1/users | Bearer | 1000/hr | Get users |
| POST | /api/v1/users | Bearer | 100/hr | Create user |

## Code Examples

```javascript
const api = new ApiClient({
  baseURL: 'https://api.example.com',
  timeout: 5000
});
```

<div class="warning">
<p>This is important information</p>
</div>

![Architecture](images/arch.png)
![Flow](images/flow.png)
'''
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Auto-fixture that resets environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_print_output(capsys):
    """Fixture to capture print output for testing CLI tools."""
    def _capture():
        captured = capsys.readouterr()
        return captured.out, captured.err
    return _capture


# Custom markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "network: Tests requiring network access")
    config.addinivalue_line("markers", "cli: Command line interface tests")
    config.addinivalue_line("markers", "api: API interaction tests")