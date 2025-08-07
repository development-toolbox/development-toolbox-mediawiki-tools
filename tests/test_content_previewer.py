#!/usr/bin/env python3
"""
Tests for content_previewer.py - Content Preview Tool for Azure DevOps to MediaWiki Migration.
"""

import os
import sys
import json
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

import pytest
import requests

# Add the migration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'migration'))
from content_previewer import ContentConverter, ContentPreviewer, load_config, main


@pytest.mark.unit
class TestContentConverter:
    """Test ContentConverter functionality for detailed conversion analysis."""
    
    def test_markdown_to_mediawiki_basic_conversion(self):
        """Test basic markdown to MediaWiki conversion."""
        markdown = """# Main Title

This is a **bold** and *italic* text example.

## Sub Title

Here's a [link](https://example.com) and some `inline code`.
"""
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "= Main Title =" in result
        assert "== Sub Title ==" in result
        assert "'''bold'''" in result
        assert "''italic''" in result
        assert "[https://example.com link]" in result
        assert "<code>inline code</code>" in result
    
    def test_markdown_to_mediawiki_code_blocks(self):
        """Test code block conversion with language detection."""
        markdown = '''# Code Examples

```python
def hello_world():
    print("Hello, World!")
```

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}
```

```
# No language specified
echo "Hello"
```
'''
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert '<syntaxhighlight lang="python">' in result
        assert 'def hello_world():' in result
        assert '</syntaxhighlight>' in result
        assert '<syntaxhighlight lang="javascript">' in result
        assert 'function greet(name)' in result
        assert '<syntaxhighlight lang="">' in result  # No language
    
    def test_markdown_to_mediawiki_table_conversion(self):
        """Test advanced table conversion to MediaWiki format."""
        markdown = '''# Tables

| Name | Age | City |
|------|-----|------|
| John | 30  | NYC  |
| Jane | 25  | LA   |

Another paragraph.

| Simple | Table |
|--------|-------|
| A      | B     |
'''
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        # Check for MediaWiki table format
        assert '{| class="wikitable"' in result
        assert result.count('{| class="wikitable"') == 2  # Two tables
        assert result.count('|}') == 2  # Two table closings
        assert '! Name' in result
        assert '! Age' in result
        assert '! City' in result
        assert '| John' in result
        assert '| 30' in result
        assert '| NYC' in result
        assert '|-' in result  # Table row separators
    
    def test_markdown_to_mediawiki_nested_lists(self):
        """Test nested list conversion."""
        markdown = '''# Lists

- Top level item 1
- Top level item 2
  - Nested item 1
  - Nested item 2
    - Deep nested item
- Top level item 3

1. Numbered item 1
2. Numbered item 2
   1. Nested numbered
   2. Another nested
3. Numbered item 3
'''
        
        result = ContentConverter.markdown_to_mediawiki(markdown)
        
        assert "* Top level item 1" in result
        assert "* Top level item 2" in result
        assert "* Nested item 1" in result
        assert "* Deep nested item" in result
        assert "# Numbered item 1" in result
        assert "# Numbered item 2" in result
        assert "# Nested numbered" in result
    
    def test_analyze_conversion_issues_comprehensive(self):
        """Test comprehensive conversion issue analysis."""
        original_content = '''# Page with Issues

![Important Diagram](diagrams/flow.png)
![Another Image](images/setup.gif)

<div class="custom-class">
<p>Some HTML content</p>
<span>More HTML</span>
</div>

[Internal Link](./other-page.md)
[Another Internal](../docs/setup.md)
[External Link](https://example.com)

- [x] Completed task
- [ ] Incomplete task
- [x] Another completed

~~Strikethrough text~~
~~More strikethrough~~

Some text with footnotes[^1] and more[^2].

[^1]: First footnote
[^2]: Second footnote
'''
        
        converted_content = ContentConverter.markdown_to_mediawiki(original_content)
        issues = ContentConverter.analyze_conversion_issues(original_content, converted_content)
        
        # Check image detection
        assert len([item for item in issues['manual_review_needed'] if '2 images' in item]) == 1
        
        # Check HTML tag detection
        html_warnings = [item for item in issues['warnings'] if 'HTML tags' in item]
        assert len(html_warnings) == 1
        assert 'div, p, span' in html_warnings[0] or all(tag in html_warnings[0] for tag in ['div', 'p', 'span'])
        
        # Check internal links
        internal_link_warnings = [item for item in issues['warnings'] if 'internal links' in item]
        assert len(internal_link_warnings) == 1
        assert '2 internal links' in internal_link_warnings[0]
        
        # Check task lists
        task_list_info = [item for item in issues['info'] if 'task list' in item]
        assert len(task_list_info) == 1
        assert '3 task list items' in task_list_info[0]
        
        # Check strikethrough
        strikethrough_warnings = [item for item in issues['warnings'] if 'strikethrough' in item]
        assert len(strikethrough_warnings) == 1
        assert '2 strikethrough items' in strikethrough_warnings[0]
        
        # Check footnotes
        footnote_manual = [item for item in issues['manual_review_needed'] if 'footnotes' in item]
        assert len(footnote_manual) == 1
        assert '4 footnotes' in footnote_manual[0]  # 2 references + 2 definitions
    
    def test_analyze_conversion_issues_empty_content(self):
        """Test conversion issue analysis with empty content."""
        issues = ContentConverter.analyze_conversion_issues("", "")
        
        assert issues['warnings'] == []
        assert issues['manual_review_needed'] == []
        assert issues['info'] == []
    
    def test_analyze_conversion_issues_clean_content(self):
        """Test conversion issue analysis with clean, simple content."""
        clean_content = """# Simple Page

This is a simple page with **bold** and *italic* text.

## Section

- Simple list item
- Another item

[External link](https://example.com)
"""
        
        converted = ContentConverter.markdown_to_mediawiki(clean_content)
        issues = ContentConverter.analyze_conversion_issues(clean_content, converted)
        
        # Should have minimal or no issues
        assert len(issues['warnings']) <= 1  # May have external link
        assert len(issues['manual_review_needed']) == 0
        assert len(issues['info']) == 0


@pytest.mark.unit
class TestContentPreviewer:
    """Test ContentPreviewer class functionality."""
    
    def test_init_success(self):
        """Test successful ContentPreviewer initialization."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        assert previewer.organization == "test-org"
        assert previewer.project == "test-project"
        assert previewer.pat == "test-pat"
        assert previewer.base_url == "https://dev.azure.com/test-org/test-project/_apis"
        assert "Basic" in previewer.session.headers['Authorization']
        assert "MediaWiki-Content-Previewer" in previewer.session.headers['User-Agent']
        assert previewer.converter is not None
    
    def test_make_api_request_success(self, mock_azure_api_response):
        """Test successful API request."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_azure_api_response['wikis']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = previewer._make_api_request('GET', 'https://example.com/api')
            
        assert result == mock_azure_api_response['wikis']
    
    def test_make_api_request_retry_logic(self, capsys):
        """Test API request retry logic."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timed out"),
                requests.exceptions.ConnectionError("Connection failed"),
                MagicMock(json=lambda: {"success": True}, raise_for_status=lambda: None)
            ]
            
            result = previewer._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2
        
        captured = capsys.readouterr()
        assert "Request timed out, retrying" in captured.out
        assert "Connection error, retrying" in captured.out
    
    def test_get_wikis_success(self, mock_azure_api_response):
        """Test successful wiki retrieval."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, '_make_api_request') as mock_request:
            mock_request.return_value = mock_azure_api_response['wikis']
            
            wikis = previewer.get_wikis()
            
        assert len(wikis) == 1
        assert wikis[0]['name'] == 'TestWiki'
    
    def test_get_wiki_pages_success(self, mock_azure_api_response):
        """Test successful wiki pages retrieval."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, '_make_api_request') as mock_request:
            mock_request.return_value = mock_azure_api_response['pages']
            
            pages = previewer.get_wiki_pages("wiki-123")
            
        assert len(pages) == 3
        assert pages[0]['path'] == '/Home'
    
    def test_get_page_content_success(self, mock_azure_api_response):
        """Test successful page content retrieval."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {'content': mock_azure_api_response['page_content']['page-1']}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            content = previewer.get_page_content("wiki-123", "page-1")
            
        assert "Welcome" in content
        assert "home page" in content


@pytest.mark.unit
class TestPagePreviewing:
    """Test individual page previewing functionality."""
    
    def test_preview_page_success(self, mock_azure_api_response, sample_markdown_content):
        """Test successful page preview."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages, \
             patch.object(previewer, 'get_page_content') as mock_get_content:
            
            mock_get_pages.return_value = mock_azure_api_response['pages']['value']
            mock_get_content.return_value = sample_markdown_content
            
            preview = previewer.preview_page("wiki-123", "/Home")
            
        assert preview['preview_available'] is True
        assert preview['page_info']['path'] == '/Home'
        assert len(preview['original_content']) > 0
        assert len(preview['converted_content']) > 0
        assert 'conversion_issues' in preview
        
        # Verify conversion happened
        assert "= Main Title =" in preview['converted_content']
        assert "'''bold'''" in preview['converted_content']
    
    def test_preview_page_not_found(self, mock_azure_api_response):
        """Test preview when page is not found."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages:
            mock_get_pages.return_value = mock_azure_api_response['pages']['value']
            
            with pytest.raises(ValueError, match="Page not found: /NonExistent"):
                previewer.preview_page("wiki-123", "/NonExistent")
    
    def test_preview_page_empty_content(self, mock_azure_api_response):
        """Test preview with empty page content."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages, \
             patch.object(previewer, 'get_page_content') as mock_get_content:
            
            mock_get_pages.return_value = mock_azure_api_response['pages']['value']
            mock_get_content.return_value = ""  # Empty content
            
            preview = previewer.preview_page("wiki-123", "/Home")
            
        assert preview['preview_available'] is False
        assert preview['original_content'] == ''
        assert preview['converted_content'] == ''
        assert 'Page is empty' in preview['conversion_issues']['info']
    
    def test_preview_page_case_insensitive(self, mock_azure_api_response, sample_markdown_content):
        """Test preview with case-insensitive page matching."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages, \
             patch.object(previewer, 'get_page_content') as mock_get_content:
            
            mock_get_pages.return_value = mock_azure_api_response['pages']['value']
            mock_get_content.return_value = sample_markdown_content
            
            # Test different case
            preview = previewer.preview_page("wiki-123", "/home")  # lowercase
            
        assert preview['preview_available'] is True
        assert preview['page_info']['path'] == '/Home'  # Should match original case


@pytest.mark.unit
class TestSamplePagePreviewing:
    """Test sample pages previewing functionality."""
    
    def test_preview_sample_pages_success(self, mock_azure_api_response, complex_wiki_structure, capsys):
        """Test successful sample pages preview."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages, \
             patch.object(previewer, 'get_page_content') as mock_get_content:
            
            # Setup pages data
            pages_data = [
                {'id': page['id'], 'path': page['path']} 
                for page in complex_wiki_structure['pages']
            ]
            mock_get_pages.return_value = pages_data
            
            # Setup content responses
            def content_side_effect(wiki_id, page_id):
                for page in complex_wiki_structure['pages']:
                    if page['id'] == page_id:
                        return page['content']
                return ''
            
            mock_get_content.side_effect = content_side_effect
            
            previews = previewer.preview_sample_pages("wiki-123", sample_size=3)
            
        assert len(previews) <= 3  # Should not exceed sample size
        assert all(preview['preview_available'] for preview in previews)
        
        captured = capsys.readouterr()
        assert "Previewed:" in captured.out
    
    def test_preview_sample_pages_empty_wiki(self):
        """Test sample pages preview with empty wiki."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages:
            mock_get_pages.return_value = []
            
            previews = previewer.preview_sample_pages("wiki-123", sample_size=5)
            
        assert previews == []
    
    def test_preview_sample_pages_with_errors(self, mock_azure_api_response, capsys):
        """Test sample pages preview with some pages failing."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages, \
             patch.object(previewer, 'get_page_content') as mock_get_content:
            
            mock_get_pages.return_value = [
                {'id': 'page1', 'path': '/Page1'},
                {'id': 'page2', 'path': '/Page2'},
                {'id': 'page3', 'path': '/Page3'}
            ]
            
            def content_side_effect(wiki_id, page_id):
                if page_id == 'page2':
                    raise Exception("Content fetch failed")
                return "# Sample Content\n\nSample text."
            
            mock_get_content.side_effect = content_side_effect
            
            previews = previewer.preview_sample_pages("wiki-123", sample_size=3)
            
        # Should have some previews despite errors
        assert len(previews) >= 1
        
        captured = capsys.readouterr()
        assert "Error previewing" in captured.out
    
    def test_preview_sample_pages_content_length_selection(self, mock_azure_api_response):
        """Test that sample pages selection considers content length diversity."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        # Create pages with different content lengths
        pages_data = [
            {'id': 'short', 'path': '/Short'},
            {'id': 'medium', 'path': '/Medium'},
            {'id': 'long', 'path': '/Long'},
            {'id': 'verylong', 'path': '/VeryLong'},
            {'id': 'empty', 'path': '/Empty'}
        ]
        
        content_responses = {
            'short': "# Short\nBrief content.",
            'medium': "# Medium\n" + "Content line.\n" * 50,
            'long': "# Long\n" + "Longer content line.\n" * 100,
            'verylong': "# Very Long\n" + "Very long content line.\n" * 200,
            'empty': ""
        }
        
        with patch.object(previewer, 'get_wiki_pages') as mock_get_pages, \
             patch.object(previewer, 'get_page_content') as mock_get_content:
            
            mock_get_pages.return_value = pages_data
            
            def content_side_effect(wiki_id, page_id):
                return content_responses.get(page_id, '')
            
            mock_get_content.side_effect = content_side_effect
            
            previews = previewer.preview_sample_pages("wiki-123", sample_size=3)
            
        # Should select diverse content lengths, prioritizing pages with content
        assert len(previews) == 3
        preview_paths = [p['page_info']['path'] for p in previews]
        
        # Should include the first page and longest page
        assert '/Short' in preview_paths  # First page always included
        assert '/VeryLong' in preview_paths  # Longest page should be included
        
        # Should not include empty page
        assert '/Empty' not in preview_paths


@pytest.mark.unit
class TestReportGeneration:
    """Test preview report generation functionality."""
    
    def test_generate_preview_report_success(self):
        """Test successful preview report generation."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        # Mock preview data with various complexity levels
        mock_previews = [
            {
                'page_info': {'path': '/Simple'},
                'original_content': "# Simple\n\nBasic content.",
                'converted_content': "= Simple =\n\nBasic content.",
                'conversion_issues': {
                    'warnings': [],
                    'manual_review_needed': [],
                    'info': ['Simple conversion']
                }
            },
            {
                'page_info': {'path': '/Complex'},
                'original_content': "# Complex\n\n![Image](img.png)\n\n<div>HTML</div>",
                'converted_content': "= Complex =\n\n![Image](img.png)\n\n<div>HTML</div>",
                'conversion_issues': {
                    'warnings': ['1 HTML tags may not convert properly: div'],
                    'manual_review_needed': ['🖼️  Found 1 images that need manual upload to MediaWiki'],
                    'info': []
                }
            }
        ]
        
        report = previewer.generate_preview_report(mock_previews, "TestWiki")
        
        assert "# Content Preview Report - TestWiki" in report
        assert "Previewed 2 pages to assess conversion quality" in report
        assert "## 1. /Simple" in report
        assert "## 2. /Complex" in report
        assert "### 🚨 Manual Review Required:" in report
        assert "### ⚠️ Warnings:" in report
        assert "### ℹ️ Info:" in report
        assert "**Total conversion issues found**: 3" in report
        assert "**Pages needing manual review**: 1" in report
        assert "**Pages with warnings**: 1" in report
        
        # Check recommendations
        assert "🎯 Recommendations" in report
        assert "Review all pages with manual review requirements" in report
        assert "Prepare to handle images manually" in report
        
        # Check next steps
        assert "✅ Next Steps" in report
        assert "azure_devops_migrator.py" in report
    
    def test_generate_preview_report_empty_previews(self):
        """Test report generation with no previews."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        report = previewer.generate_preview_report([], "EmptyWiki")
        
        assert "No previews available" in report
    
    def test_generate_preview_report_no_issues(self):
        """Test report generation when no issues are found."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        clean_previews = [
            {
                'page_info': {'path': '/CleanPage'},
                'original_content': "# Clean\n\nSimple content.",
                'converted_content': "= Clean =\n\nSimple content.",
                'conversion_issues': {
                    'warnings': [],
                    'manual_review_needed': [],
                    'info': []
                }
            }
        ]
        
        report = previewer.generate_preview_report(clean_previews, "CleanWiki")
        
        assert "**Total conversion issues found**: 0" in report
        assert "**Pages needing manual review**: 0" in report
        assert "**Pages with warnings**: 0" in report
    
    def test_generate_preview_report_content_truncation(self):
        """Test that long content is properly truncated in report."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        long_content = "# Long Content\n\n" + "This is a very long line of content. " * 50
        
        long_preview = [
            {
                'page_info': {'path': '/LongPage'},
                'original_content': long_content,
                'converted_content': long_content.replace('# Long Content', '= Long Content ='),
                'conversion_issues': {
                    'warnings': [],
                    'manual_review_needed': [],
                    'info': []
                }
            }
        ]
        
        report = previewer.generate_preview_report(long_preview, "TestWiki")
        
        # Check that content is truncated
        assert "... (truncated)" in report
        
        # Ensure truncated sections are not too long
        original_section_start = report.find("**Original (Markdown):**")
        original_section_end = report.find("**Converted (MediaWiki):**")
        original_section = report[original_section_start:original_section_end]
        
        # Should not exceed reasonable length (considering markdown wrapper)
        assert len(original_section) < 700  # 500 chars content + markup


@pytest.mark.unit
class TestConfigurationLoading:
    """Test configuration loading for content previewer."""
    
    def test_load_config_success(self, mock_env_vars):
        """Test successful configuration loading."""
        with patch.dict(os.environ, mock_env_vars):
            azure_org, azure_project, azure_pat, wiki_name = load_config()
            
        assert azure_org == "test-org"
        assert azure_project == "test-project"
        assert azure_pat == "test-pat-token-123"
        assert wiki_name == "TestWiki"
    
    def test_load_config_missing_required(self, capsys):
        """Test configuration loading with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                load_config()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
        assert "AZURE_DEVOPS_ORGANIZATION" in captured.out
        assert "AZURE_DEVOPS_PROJECT" in captured.out
        assert "AZURE_DEVOPS_PAT" in captured.out


@pytest.mark.integration
class TestMainFunction:
    """Test main function integration."""
    
    def test_main_success_flow_sample_pages(self, mock_env_vars, mock_azure_api_response, temp_directory, monkeypatch):
        """Test successful main function execution with sample pages."""
        monkeypatch.chdir(temp_directory)
        
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class, \
             patch('builtins.input', side_effect=['2', '3']), \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            
            # Mock sample preview results
            mock_previews = [
                {
                    'page_info': {'path': '/Home'},
                    'original_content': "# Home\nContent here.",
                    'converted_content': "= Home =\nContent here.",
                    'conversion_issues': {'warnings': [], 'manual_review_needed': [], 'info': []}
                }
            ]
            mock_previewer.preview_sample_pages.return_value = mock_previews
            mock_previewer.generate_preview_report.return_value = "Test Preview Report"
            
            main()
            
        # Verify previewer was created and methods called
        mock_previewer_class.assert_called_once_with("test-org", "test-project", "test-pat-token-123")
        mock_previewer.preview_sample_pages.assert_called_once_with(mock_azure_api_response['wikis']['value'][0]['id'], 3)
        mock_previewer.generate_preview_report.assert_called_once()
        
        # Verify file was written
        mock_file.assert_called_once_with("content_preview_report.md", "w", encoding='utf-8')
    
    def test_main_success_flow_specific_page(self, mock_env_vars, mock_azure_api_response, temp_directory, monkeypatch, capsys):
        """Test successful main function execution with specific page."""
        monkeypatch.chdir(temp_directory)
        
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class, \
             patch('builtins.input', side_effect=['1', '/Home']), \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            
            # Mock specific page preview
            mock_preview = {
                'page_info': {'path': '/Home'},
                'original_content': "# Home\nContent here.",
                'converted_content': "= Home =\nContent here.",
                'conversion_issues': {'warnings': [], 'manual_review_needed': [], 'info': []}
            }
            mock_previewer.preview_page.return_value = mock_preview
            mock_previewer.generate_preview_report.return_value = "Test Preview Report"
            
            main()
            
        mock_previewer.preview_page.assert_called_once_with(mock_azure_api_response['wikis']['value'][0]['id'], '/Home')
        
        captured = capsys.readouterr()
        assert "Previewed page: /Home" in captured.out
    
    def test_main_page_not_found_error(self, mock_env_vars, mock_azure_api_response, capsys):
        """Test main function when specific page is not found."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class, \
             patch('builtins.input', side_effect=['1', '/NonExistent']):
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            mock_previewer.preview_page.side_effect = ValueError("Page not found: /NonExistent")
            
            main()
            
        captured = capsys.readouterr()
        assert "Page not found: /NonExistent" in captured.out
    
    def test_main_no_wikis_found(self, mock_env_vars, capsys):
        """Test main function when no wikis are found."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class:
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = []
            
            main()
            
        captured = capsys.readouterr()
        assert "No wikis found" in captured.out
    
    def test_main_wiki_not_found(self, mock_env_vars, mock_azure_api_response, capsys):
        """Test main function when specified wiki is not found."""
        env_with_specific_wiki = mock_env_vars.copy()
        env_with_specific_wiki['AZURE_WIKI_NAME'] = 'NonExistentWiki'
        
        with patch.dict(os.environ, env_with_specific_wiki), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class:
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            
            main()
            
        captured = capsys.readouterr()
        assert "Wiki 'NonExistentWiki' not found" in captured.out
    
    def test_main_missing_dependencies(self, capsys):
        """Test main function with missing dependencies."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'requests'")):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Required package not installed" in captured.out
    
    def test_main_configuration_error(self, capsys):
        """Test main function with configuration error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Missing required environment variables" in captured.out
    
    def test_main_general_error(self, mock_env_vars, capsys):
        """Test main function with general error."""
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer', side_effect=Exception("General error")):
            
            with pytest.raises(SystemExit):
                main()
                
        captured = capsys.readouterr()
        assert "Preview failed" in captured.out
    
    def test_main_no_issues_summary(self, mock_env_vars, mock_azure_api_response, temp_directory, monkeypatch, capsys):
        """Test main function summary when no issues are found."""
        monkeypatch.chdir(temp_directory)
        
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class, \
             patch('builtins.input', side_effect=['2', '1']), \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            
            # Mock clean preview with no issues
            mock_previews = [
                {
                    'page_info': {'path': '/Clean'},
                    'original_content': "# Clean\nContent here.",
                    'converted_content': "= Clean =\nContent here.",
                    'conversion_issues': {'warnings': [], 'manual_review_needed': [], 'info': []}
                }
            ]
            mock_previewer.preview_sample_pages.return_value = mock_previews
            mock_previewer.generate_preview_report.return_value = "Clean Report"
            
            main()
            
        captured = capsys.readouterr()
        assert "No major issues found - migration should be smooth!" in captured.out
    
    def test_main_with_issues_summary(self, mock_env_vars, mock_azure_api_response, temp_directory, monkeypatch, capsys):
        """Test main function summary when issues are found."""
        monkeypatch.chdir(temp_directory)
        
        with patch.dict(os.environ, mock_env_vars), \
             patch('content_previewer.ContentPreviewer') as mock_previewer_class, \
             patch('builtins.input', side_effect=['2', '1']), \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_previewer = mock_previewer_class.return_value
            mock_previewer.get_wikis.return_value = mock_azure_api_response['wikis']['value']
            
            # Mock preview with issues
            mock_previews = [
                {
                    'page_info': {'path': '/Issues'},
                    'original_content': "# Issues\n![Image](img.png)",
                    'converted_content': "= Issues =\n![Image](img.png)",
                    'conversion_issues': {
                        'warnings': ['HTML issue'],
                        'manual_review_needed': ['Image issue'],
                        'info': []
                    }
                }
            ]
            mock_previewer.preview_sample_pages.return_value = mock_previews
            mock_previewer.generate_preview_report.return_value = "Issues Report"
            
            main()
            
        captured = capsys.readouterr()
        assert "Found 2 potential issues - review the report" in captured.out


@pytest.mark.api
class TestApiIntegrationScenarios:
    """Test API integration scenarios and edge cases."""
    
    def test_rate_limiting_handling(self, capsys):
        """Test handling of API rate limiting."""
        previewer = ContentPreviewer("test-org", "test-project", "test-pat")
        
        with patch.object(previewer.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Mock rate limit response
            rate_limited_response = MagicMock()
            rate_limited_response.status_code = 429
            rate_limited_response.headers = {'Retry-After': '30'}
            rate_limited_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=rate_limited_response)
            
            success_response = MagicMock()
            success_response.json.return_value = {"success": True}
            success_response.raise_for_status.return_value = None
            
            mock_get.side_effect = [rate_limited_response, success_response]
            
            result = previewer._make_api_request('GET', 'https://example.com/api')
            
        assert result == {"success": True}
        mock_sleep.assert_called_once_with(30)
        
        captured = capsys.readouterr()
        assert "Rate limited, waiting 30s" in captured.out
    
    def test_complex_content_conversion_edge_cases(self):
        """Test content conversion with complex edge cases."""
        converter = ContentConverter()
        
        edge_case_content = '''# Complex Edge Cases

## Table with pipes in content
| Column | Data with | in it |
|--------|-----------|--------|
| Test   | Value|2  | More|  |

## Mixed formatting
This has **bold with `code` inside** and *italic with [link](url) inside*.

## Escaped characters
Code with \\`backticks\\` and \\*asterisks\\* and \\[brackets\\].

## Empty sections

## Multiple blank lines



## Unicode content
Unicode: 🚀 ✨ 📊 → ← ↑ ↓

## Complex code block
```python
def complex_function():
    """
    Docstring with **markdown** in it.
    """
    # Comment with `backticks`
    return f"String with {variable} and **bold**"
```
'''
        
        result = converter.markdown_to_mediawiki(edge_case_content)
        
        # Should not crash and should handle edge cases reasonably
        assert "= Complex Edge Cases =" in result
        assert "== Table with pipes in content ==" in result
        assert "{| class=\"wikitable\"" in result
        assert "'''bold with <code>code</code> inside'''" in result
        assert '<syntaxhighlight lang="python">' in result
        assert "Unicode: 🚀 ✨ 📊" in result  # Unicode should be preserved


if __name__ == '__main__':
    pytest.main([__file__])