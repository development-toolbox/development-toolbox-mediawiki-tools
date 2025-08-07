#!/usr/bin/env python3
"""
Content Preview Tool
Preview how your Azure DevOps wiki content will look in MediaWiki before migration

Author: Johan Sörell
Contact: https://github.com/J-SirL | https://se.linkedin.com/in/johansorell | automationblueprint.site
Date: 2025
Version: 1.0.0
"""

import os
import sys
import json
import base64
import re
import time
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv


class ContentConverter:
    """Converts content from Markdown (Azure DevOps) to MediaWiki syntax"""

    @staticmethod
    def markdown_to_mediawiki(markdown_content: str) -> str:
        """Convert Markdown to MediaWiki syntax with detailed tracking"""
        content = markdown_content

        # Headers
        content = re.sub(r'^# (.+)$', r'= \1 =', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'== \1 ==', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'=== \1 ===', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.+)$', r'==== \1 ====', content, flags=re.MULTILINE)
        content = re.sub(r'^##### (.+)$', r'===== \1 =====', content, flags=re.MULTILINE)

        # Bold and Italic
        content = re.sub(r'\*\*(.+?)\*\*', r"'''\1'''", content)
        content = re.sub(r'\*(.+?)\*', r"''\1''", content)
        content = re.sub(r'__(.+?)__', r"'''\1'''", content)
        content = re.sub(r'_(.+?)_', r"''\1''", content)

        # Links
        content = re.sub(r'\[(.+?)\]\((.+?)\)', r'[\2 \1]', content)

        # Code blocks
        content = re.sub(r'```(\w+)?\n(.*?)\n```', r'<syntaxhighlight lang="\1">\n\2\n</syntaxhighlight>', content, flags=re.DOTALL)
        content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)

        # Lists
        content = re.sub(r'^(\s*)- (.+)$', r'\1* \2', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)\d+\. (.+)$', r'\1# \2', content, flags=re.MULTILINE)

        # Tables (enhanced conversion)
        lines = content.split('\n')
        in_table = False
        converted_lines = []
        table_headers = []

        for line in lines:
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    converted_lines.append('{| class="wikitable"')
                    in_table = True
                    # First row is headers
                    cells = [cell.strip() for cell in line.strip().split('|')[1:-1]]
                    table_headers = cells
                    converted_lines.append('|-')
                    for cell in cells:
                        converted_lines.append(f'! {cell}')
                    continue

                # Check if this is the header separator line
                cells = [cell.strip() for cell in line.strip().split('|')[1:-1]]
                if all(re.match(r'^[-\\s:]*$', cell) for cell in cells):
                    # Header separator line, skip it
                    continue

                # Regular data row
                converted_lines.append('|-')
                for cell in cells:
                    converted_lines.append(f'| {cell}')
            else:
                if in_table:
                    converted_lines.append('|}')
                    in_table = False
                converted_lines.append(line)

        if in_table:
            converted_lines.append('|}')

        return '\\n'.join(converted_lines)

    @staticmethod
    def analyze_conversion_issues(original: str, converted: str) -> Dict[str, List[str]]:
        """Analyze potential issues in the conversion"""
        issues: Dict[str, List[str]] = {
            'warnings': [],
            'manual_review_needed': [],
            'info': []
        }

        # Check for images
        images = re.findall(r'!\\[.*?\\]\\(.*?\\)', original)
        if images:
            issues['manual_review_needed'].append(
                f"🖼️  Found {len(images)} images that need manual upload to MediaWiki"
            )
            for img in images[:3]:  # Show first 3
                issues['manual_review_needed'].append(f"   - {img}")

        # Check for HTML tags
        html_tags = re.findall(r'<[^>]+>', original)
        if html_tags:
            unique_tags = set(tag.split()[0].strip('<>') for tag in html_tags)
            issues['warnings'].append(
                f"⚠️  Found HTML tags that may not convert properly: {', '.join(unique_tags)}"
            )

        # Check for complex links
        internal_links = re.findall(r'\\[.*?\\]\\((?!http).*?\\)', original)
        if internal_links:
            issues['warnings'].append(
                f"🔗 Found {len(internal_links)} internal links - verify they work after migration"
            )

        # Check for task lists
        task_lists = re.findall(r'- \[[ x]\]', original)
        if task_lists:
            issues['info'].append(
                f"☑️  Found {len(task_lists)} task list items - converted to regular lists"
            )

        # Check for strikethrough
        strikethrough = re.findall(r'~~.*?~~', original)
        if strikethrough:
            issues['warnings'].append(
                f"❌ Found {len(strikethrough)} strikethrough items - may not display correctly"
            )

        # Check for footnotes
        footnotes = re.findall(r'\\[\\^.*?\\]', original)
        if footnotes:
            issues['manual_review_needed'].append(
                f"📝 Found {len(footnotes)} footnotes - need manual conversion"
            )

        return issues


class ContentPreviewer:
    """Previews content conversion for Azure DevOps wiki pages"""

    def __init__(self, organization: str, project: str, personal_access_token: str):
        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        self.session = requests.Session()
        self.converter = ContentConverter()

        # Set up authentication
        auth_string = f":{personal_access_token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'User-Agent': 'MediaWiki-Content-Previewer/1.0'
        })

    def _make_api_request(self, method: str, url: str, max_retries: int = 3) -> Dict:
        """Make API request with retry logic and proper error handling"""
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=30)
                else:
                    response = self.session.post(url, timeout=30)
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise
                print(f"⏳ Request timed out, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    raise
                print(f"⚠️  Connection error, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    print(f"⏳ Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                else:
                    raise
                    
        return {}
        
    def get_wikis(self) -> List[Dict]:
        """Get all wikis in the project"""
        url = f"{self.base_url}/wiki/wikis?api-version=7.0"
        try:
            response = self._make_api_request('GET', url)
            return response.get('value', [])
        except requests.RequestException as e:
            print(f"❌ Failed to retrieve wikis: {e}")
            raise

    def get_wiki_pages(self, wiki_id: str) -> List[Dict]:
        """Get all pages in a wiki"""
        url = f"{self.base_url}/wiki/wikis/{wiki_id}/pages?api-version=7.0&recursionLevel=full"
        try:
            response = self._make_api_request('GET', url)
            return response.get('value', [])
        except requests.RequestException as e:
            print(f"❌ Failed to retrieve pages for wiki {wiki_id}: {e}")
            raise

    def get_page_content(self, wiki_id: str, page_id: str) -> str:
        """Get the content of a specific page"""
        url = f"{self.base_url}/wiki/wikis/{wiki_id}/pages/{page_id}?api-version=7.0&includeContent=true"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('content', '')

    def preview_page(self, wiki_id: str, page_path: str) -> Dict:
        """Preview a specific page conversion"""
        # Find the page
        pages = self.get_wiki_pages(wiki_id)
        target_page = None

        for page in pages:
            if page['path'].lower() == page_path.lower():
                target_page = page
                break

        if not target_page:
            raise ValueError(f"Page not found: {page_path}")

        # Get content
        original_content = self.get_page_content(wiki_id, target_page['id'])

        if not original_content.strip():
            return {
                'page_info': target_page,
                'original_content': '',
                'converted_content': '',
                'conversion_issues': {'warnings': [], 'manual_review_needed': [], 'info': ['Page is empty']},
                'preview_available': False
            }

        # Convert content
        converted_content = self.converter.markdown_to_mediawiki(original_content)

        # Analyze issues
        conversion_issues = self.converter.analyze_conversion_issues(original_content, converted_content)

        return {
            'page_info': target_page,
            'original_content': original_content,
            'converted_content': converted_content,
            'conversion_issues': conversion_issues,
            'preview_available': True
        }

    def preview_sample_pages(self, wiki_id: str, sample_size: int = 5) -> List[Dict]:
        """Preview a sample of pages for quick assessment"""
        pages = self.get_wiki_pages(wiki_id)

        if not pages:
            return []

        # Select diverse sample (first page, largest, some random ones)
        sample_pages = []

        # Always include first page
        if pages:
            sample_pages.append(pages[0])

        # Get pages with content and select diverse sample
        pages_with_content = []
        for page in pages[1:]:  # Skip first since we already added it
            try:
                content = self.get_page_content(wiki_id, page['id'])
                if content.strip():
                    pages_with_content.append((page, len(content)))
            except:
                continue

        # Sort by content length and take some from different sizes
        pages_with_content.sort(key=lambda x: x[1], reverse=True)

        # Add largest page
        if pages_with_content:
            sample_pages.append(pages_with_content[0][0])

        # Add medium and smaller pages
        if len(pages_with_content) > 2:
            mid_idx = len(pages_with_content) // 2
            sample_pages.append(pages_with_content[mid_idx][0])

        # Add more pages up to sample_size
        remaining = sample_size - len(sample_pages)
        step = max(1, len(pages_with_content) // remaining) if remaining > 0 else 1

        for i in range(0, min(len(pages_with_content), remaining * step), step):
            if len(sample_pages) >= sample_size:
                break
            page_candidate = pages_with_content[i][0]
            if page_candidate not in [p for p in sample_pages]:
                sample_pages.append(page_candidate)

        # Preview each sample page
        previews = []
        for page in sample_pages[:sample_size]:
            try:
                preview = self.preview_page(wiki_id, page['path'])
                previews.append(preview)
                print(f"  📄 Previewed: {page['path']}")
            except Exception as e:
                print(f"  ⚠️  Error previewing {page['path']}: {e}")

        return previews

    def generate_preview_report(self, previews: List[Dict], wiki_name: str) -> str:
        """Generate a preview report"""
        if not previews:
            return "No previews available."

        report = f"""# Content Preview Report - {wiki_name}

This report shows how your Azure DevOps wiki content will look after conversion to MediaWiki.

## 📊 Sample Analysis

Previewed {len(previews)} pages to assess conversion quality.

"""

        for i, preview in enumerate(previews, 1):
            page_info = preview['page_info']
            issues = preview['conversion_issues']

            report += f"""## {i}. {page_info['path']}

**Original content length**: {len(preview['original_content'])} characters
**Converted content length**: {len(preview['converted_content'])} characters

"""

            # Show issues
            if issues['manual_review_needed']:
                report += "### 🚨 Manual Review Required:\n"
                for issue in issues['manual_review_needed']:
                    report += f"- {issue}\n"
                report += "\n"

            if issues['warnings']:
                report += "### ⚠️ Warnings:\n"
                for warning in issues['warnings']:
                    report += f"- {warning}\n"
                report += "\n"

            if issues['info']:
                report += "### ℹ️ Info:\n"
                for info in issues['info']:
                    report += f"- {info}\n"
                report += "\n"

            # Show side-by-side comparison (first 500 chars)
            report += "### 📋 Content Comparison\n\n"
            report += "**Original (Markdown):**\n```markdown\n"
            report += preview['original_content'][:500]
            if len(preview['original_content']) > 500:
                report += "\n... (truncated)"
            report += "\n```\n\n"

            report += "**Converted (MediaWiki):**\n```mediawiki\n"
            report += preview['converted_content'][:500]
            if len(preview['converted_content']) > 500:
                report += "\n... (truncated)"
            report += "\n```\n\n"

            report += "---\n\n"

        # Summary section
        total_issues = sum(
            len(p['conversion_issues']['manual_review_needed']) +
            len(p['conversion_issues']['warnings'])
            for p in previews
        )

        report += f"""## 📋 Summary

Based on the {len(previews)} sample pages:

- **Total conversion issues found**: {total_issues}
- **Pages needing manual review**: {sum(1 for p in previews if p['conversion_issues']['manual_review_needed'])}
- **Pages with warnings**: {sum(1 for p in previews if p['conversion_issues']['warnings'])}

### 🎯 Recommendations

1. **Review all pages with manual review requirements** before migration
2. **Test the conversion** with a small batch first
3. **Prepare to handle images manually** - they need to be uploaded separately
4. **Check internal links** after migration to ensure they still work
5. **Review table formatting** in MediaWiki after conversion

### ✅ Next Steps

1. If the preview looks good, proceed with the full migration using `azure_devops_migrator.py`
2. If issues are found, consider pre-processing problematic content in Azure DevOps
3. Plan extra time for manual review of flagged pages

---
*Preview report generated by Content Preview Tool*
"""

        return report


def load_config() -> Tuple[str, str, str, Optional[str]]:
    """Load configuration from .env file"""
    load_dotenv()

    azure_org = os.getenv("AZURE_DEVOPS_ORGANIZATION")
    azure_project = os.getenv("AZURE_DEVOPS_PROJECT")
    azure_pat = os.getenv("AZURE_DEVOPS_PAT")
    wiki_name = os.getenv("AZURE_WIKI_NAME")

    if not azure_org or not azure_project or not azure_pat:
        print("❌ Missing required environment variables:")
        print("Please set: AZURE_DEVOPS_ORGANIZATION, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_PAT")
        sys.exit(1)

    # Type checker now knows these are not None due to the check above
    return azure_org, azure_project, azure_pat, wiki_name


def main():
    """Main function"""
    print("👀 Azure DevOps Wiki Content Preview Tool")
    print("=" * 45)

    # Check required packages
    try:
        import requests
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Required package not installed: {e}")
        print("Please install: pip install requests python-dotenv")
        sys.exit(1)

    # Load configuration
    azure_org, azure_project, azure_pat, wiki_name = load_config()

    try:
        # Initialize previewer
        previewer = ContentPreviewer(azure_org, azure_project, azure_pat)

        print(f"🔗 Connecting to Azure DevOps: {azure_org}/{azure_project}")

        # Get wikis
        wikis = previewer.get_wikis()
        if not wikis:
            print("❌ No wikis found")
            return

        # Select wiki
        target_wiki = None
        if wiki_name:
            target_wiki = next((w for w in wikis if w['name'].lower() == wiki_name.lower()), None)
            if not target_wiki:
                print(f"❌ Wiki '{wiki_name}' not found")
                return
        else:
            target_wiki = wikis[0]

        print(f"📚 Previewing wiki: {target_wiki['name']}")

        # Ask user for preview type
        print("\nChoose preview option:")
        print("1. Preview specific page")
        print("2. Preview sample pages (recommended)")

        choice = input("Enter choice (1 or 2): ").strip()

        if choice == "1":
            page_path = input("Enter page path (e.g., /Documentation/Setup): ").strip()
            try:
                preview = previewer.preview_page(target_wiki['id'], page_path)
                previews = [preview]
                print(f"✅ Previewed page: {page_path}")
            except ValueError as e:
                print(f"❌ {e}")
                return
        else:
            print("🔍 Analyzing sample pages...")
            sample_size = 5
            try:
                sample_input = input(f"Number of sample pages (default {sample_size}): ").strip()
                if sample_input:
                    sample_size = int(sample_input)
            except ValueError:
                pass

            previews = previewer.preview_sample_pages(target_wiki['id'], sample_size)

        if previews:
            # Generate report
            report = previewer.generate_preview_report(previews, target_wiki['name'])

            # Save report
            report_file = "content_preview_report.md"
            with open(report_file, "w", encoding='utf-8') as f:
                f.write(report)

            print(f"\n✅ Preview complete!")
            print(f"📄 Report saved to: {report_file}")
            print(f"👀 Previewed {len(previews)} pages")

            # Show quick summary
            total_issues = sum(
                len(p['conversion_issues']['manual_review_needed']) +
                len(p['conversion_issues']['warnings'])
                for p in previews
            )

            if total_issues == 0:
                print("🎉 No major issues found - migration should be smooth!")
            else:
                print(f"⚠️  Found {total_issues} potential issues - review the report")

            print(f"\n🔗 Open {report_file} to see the detailed preview!")

    except Exception as e:
        print(f"❌ Preview failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
