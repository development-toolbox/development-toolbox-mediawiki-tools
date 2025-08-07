#!/usr/bin/env python3
"""
Pre-Migration Analysis Tool for Azure DevOps to MediaWiki Migration

This module provides comprehensive analysis capabilities for Azure DevOps wiki content
to help plan and estimate the effort required for migration to MediaWiki.

Features:
- Content complexity analysis and scoring
- Migration time estimation
- Identification of high-risk content requiring manual attention
- Detailed reporting with actionable recommendations

Author: Development Toolbox Team
Date: August 2025
Version: 1.0.0
"""

import os
import sys
import json
import base64
import time
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Union, Any, Optional
import re
from datetime import datetime

import requests
from dotenv import load_dotenv


class MigrationPlanner:
    """
    Analyzes Azure DevOps wiki content for migration planning to MediaWiki.

    This class provides comprehensive analysis of wiki content including:
    - Content complexity scoring
    - Migration time estimation
    - Identification of potential issues
    - Generation of detailed reports with recommendations

    Attributes:
        organization (str): Azure DevOps organization name
        project (str): Azure DevOps project name
        pat (str): Personal Access Token for authentication
        base_url (str): Base URL for Azure DevOps API calls
        session (requests.Session): HTTP session with authentication headers

    Example:
        >>> planner = MigrationPlanner("myorg", "myproject", "pat_token")
        >>> analysis = planner.analyze_wiki("MyWiki")
        >>> report = planner.generate_report(analysis)
    """

    def _make_api_request(self, method: str, url: str, max_retries: int = 3,
                         backoff_factor: float = 1.0) -> Dict[str, Any]:
        """
        Make API request with retry logic and proper error handling.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.)
            url (str): Full URL for the API request
            max_retries (int): Maximum number of retry attempts
            backoff_factor (float): Exponential backoff multiplier

        Returns:
            Dict[str, Any]: Parsed JSON response

        Raises:
            requests.RequestException: If all retry attempts fail
        """
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=30)
                elif method.upper() == 'POST':
                    response = self.session.post(url, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    print(f"❌ Request timed out after {max_retries} attempts: {url}")
                    raise
                wait_time = backoff_factor * (2 ** attempt)
                print(f"⏳ Request timed out, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    print(f"❌ Connection failed after {max_retries} attempts: {e}")
                    raise
                wait_time = backoff_factor * (2 ** attempt)
                print(f"⚠️  Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    print(f"⏳ Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                elif e.response.status_code == 401:
                    print("❌ Authentication failed - check your Personal Access Token")
                    raise
                elif e.response.status_code == 403:
                    print("❌ Access denied - check your PAT permissions (need Wiki read access)")
                    raise
                elif e.response.status_code == 404:
                    print(f"❌ Resource not found: {url}")
                    raise
                else:
                    if attempt == max_retries - 1:
                        print(f"❌ HTTP {e.response.status_code} error after {max_retries} attempts")
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    print(f"⚠️  HTTP {e.response.status_code}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response from Azure DevOps API: {e}")
                print(f"💡 This may indicate an authentication or API endpoint issue")
                raise

        return {}  # Should not reach here

    def __init__(self, organization: str, project: str, personal_access_token: str):
        """
        Initialize the Migration Planner with Azure DevOps credentials.

        Args:
            organization (str): Azure DevOps organization name
            project (str): Azure DevOps project name
            personal_access_token (str): Personal Access Token for API authentication

        Raises:
            ValueError: If any required parameter is empty or None
        """
        if not all([organization, project, personal_access_token]):
            raise ValueError("Organization, project, and personal access token are required")

        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        self.session = requests.Session()

        # Set up authentication headers for Azure DevOps API
        # Uses Basic authentication with empty username and PAT as password
        auth_string = f":{personal_access_token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'User-Agent': 'MediaWiki-Migration-Tool/1.0'
        })

        # Set reasonable timeouts (handled per request, not on session)

    def get_wikis(self) -> List[Dict[str, Any]]:
        """
        Retrieve all wikis available in the Azure DevOps project.

        Returns:
            List[Dict[str, Any]]: List of wiki objects containing id, name, and other metadata

        Raises:
            requests.HTTPError: If the API request fails

        Example:
            >>> wikis = planner.get_wikis()
            >>> for wiki in wikis:
            ...     print(f"Wiki: {wiki['name']} (ID: {wiki['id']})")
        """
        url = f"{self.base_url}/wiki/wikis?api-version=7.0"
        try:
            response = self._make_api_request('GET', url)
            return response.get('value', [])
        except requests.RequestException as e:
            print(f"❌ Failed to retrieve wikis: {e}")
            raise

    def get_wiki_pages(self, wiki_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all pages from a specific wiki, including nested pages.

        Args:
            wiki_id (str): The unique identifier of the wiki

        Returns:
            List[Dict[str, Any]]: List of page objects with metadata (id, path, etc.)

        Raises:
            requests.HTTPError: If the API request fails or wiki doesn't exist

        Note:
            Uses recursionLevel=full to get all nested pages in the wiki hierarchy.
        """
        url = f"{self.base_url}/wiki/wikis/{wiki_id}/pages?api-version=7.0&recursionLevel=full"
        try:
            response = self._make_api_request('GET', url)
            return response.get('value', [])
        except requests.RequestException as e:
            print(f"❌ Failed to retrieve pages for wiki {wiki_id}: {e}")
            raise

    def get_page_content(self, wiki_id: str, page_id: str) -> str:
        """
        Retrieve the markdown content of a specific wiki page.

        Args:
            wiki_id (str): The unique identifier of the wiki
            page_id (str): The unique identifier of the page

        Returns:
            str: The markdown content of the page, empty string if no content

        Raises:
            requests.HTTPError: If the API request fails or page doesn't exist

        Note:
            Uses includeContent=true to get the actual page content in the response.
        """
        url = f"{self.base_url}/wiki/wikis/{wiki_id}/pages/{page_id}?api-version=7.0&includeContent=true"
        try:
            response = self._make_api_request('GET', url)
            return response.get('content', '')
        except requests.RequestException as e:
            print(f"⚠️  Failed to retrieve content for page {page_id}: {e}")
            return ''  # Return empty content rather than crashing

    def analyze_content_complexity(self, content: str) -> Dict[str, Union[int, str]]:
        """
        Analyze markdown content to determine migration complexity and effort required.

        This method examines various aspects of the content to identify elements that
        may require special attention during migration to MediaWiki.

        Args:
            content (str): The markdown content to analyze

        Returns:
            Dict[str, Union[int, str]]: Analysis results containing:
                - Basic metrics (word_count, char_count, line_count)
                - Content elements (headers, links, images, tables, etc.)
                - complexity_score (int): Weighted score based on difficult elements
                - complexity_level (str): 'Low', 'Medium', or 'High' classification

        Note:
            Complexity scoring weights:
            - Tables: 3 points each (complex conversion)
            - Code blocks: 2 points each (syntax highlighting concerns)
            - Images: 2 points each (manual upload required)
            - HTML tags: 2 points each (may need conversion)
            - Links: 1 point each (need verification)
        """
        # Initialize analysis dictionary with basic content metrics
        analysis: Dict[str, Union[int, str]] = {
            'word_count': len(content.split()),
            'char_count': len(content),
            'line_count': len(content.split('\n')),

            # Structural elements that affect migration complexity
            'headers': len(re.findall(r'^#+\s', content, re.MULTILINE)),
            'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
            'images': len(re.findall(r'!\[.*?\]\(.*?\)', content)),
            'code_blocks': len(re.findall(r'```.*?```', content, re.DOTALL)),
            'inline_code': len(re.findall(r'`[^`]+`', content)),
            'tables': len(re.findall(r'\|.*?\|', content)),
            'lists': len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE)),
            'numbered_lists': len(re.findall(r'^\s*\d+\.\s', content, re.MULTILINE)),
            'bold_text': len(re.findall(r'\*\*.*?\*\*', content)),
            'italic_text': len(re.findall(r'\*.*?\*', content)),
            'html_tags': len(re.findall(r'<[^>]+>', content)),
        }

        # Calculate weighted complexity score based on elements that require special handling
        complexity_score = (
            int(analysis['tables']) * 3 +      # Tables are complex to convert properly
            int(analysis['code_blocks']) * 2 + # Code blocks need syntax highlighting setup
            int(analysis['images']) * 2 +      # Images require manual download/upload
            int(analysis['html_tags']) * 2 +   # HTML might need manual conversion
            int(analysis['links']) * 1         # Links need verification after migration
        )

        analysis['complexity_score'] = complexity_score

        # Classify complexity level based on score thresholds
        if complexity_score < 10:
            analysis['complexity_level'] = 'Low'      # Simple pages, mostly auto-convertible
        elif complexity_score < 25:
            analysis['complexity_level'] = 'Medium'   # Some manual review needed
        else:
            analysis['complexity_level'] = 'High'     # Significant manual work required

        return analysis

    def analyze_wiki(self, wiki_name: Union[str, None] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a wiki for migration planning.

        This method analyzes all pages in a wiki to provide detailed metrics,
        complexity assessment, and migration recommendations.

        Args:
            wiki_name (str, optional): Name of the specific wiki to analyze.
                                     If None, analyzes the first available wiki.

        Returns:
            Dict[str, Any]: Comprehensive analysis results containing:
                - wiki_info: Basic wiki metadata
                - Statistics: Page counts, content metrics, complexity distribution
                - page_details: Individual page analysis results
                - largest_pages: Top 10 pages by word count
                - most_complex_pages: Top 10 pages by complexity score
                - potential_issues: List of identified migration challenges

        Raises:
            ValueError: If specified wiki_name is not found
            requests.HTTPError: If API requests fail

        Example:
            >>> analysis = planner.analyze_wiki("ProjectDocs")
            >>> print(f"Found {analysis['total_pages']} pages")
            >>> print(f"High complexity: {analysis['complexity_distribution']['High']}")
        """
        print("🔍 Starting wiki analysis...")

        # Retrieve all available wikis from the project
        wikis = self.get_wikis()
        if not wikis:
            print("❌ No wikis found")
            return {}

        # Select target wiki based on name or use first available
        target_wiki = None
        if wiki_name:
            target_wiki = next((w for w in wikis if w['name'].lower() == wiki_name.lower()), None)
            if not target_wiki:
                print(f"❌ Wiki '{wiki_name}' not found")
                available_wikis = [w['name'] for w in wikis]
                print(f"Available wikis: {', '.join(available_wikis)}")
                return {}
        else:
            target_wiki = wikis[0]

        print(f"📚 Analyzing wiki: {target_wiki['name']}")
        wiki_id = target_wiki['id']

        # Get all pages in the wiki (including nested pages)
        pages = self.get_wiki_pages(wiki_id)
        if not pages:
            print("❌ No pages found in wiki")
            return {}

        print(f"📄 Found {len(pages)} pages to analyze")

        # Initialize comprehensive analysis structure
        analysis: Dict[str, Any] = {
            'wiki_info': target_wiki,
            'total_pages': len(pages),
            'pages_analyzed': 0,
            'pages_with_content': 0,
            'total_complexity_score': 0,
            'complexity_distribution': {'Low': 0, 'Medium': 0, 'High': 0},
            'content_stats': {
                'total_words': 0,
                'total_chars': 0,
                'total_lines': 0,
                'total_headers': 0,
                'total_links': 0,
                'total_images': 0,
                'total_code_blocks': 0,
                'total_tables': 0,
            },
            'page_details': [],
            'potential_issues': [],
            'largest_pages': [],
            'most_complex_pages': [],
        }

        # Analyze each page individually
        for i, page in enumerate(pages, 1):
            # Show progress for large wikis
            if i % 10 == 0:
                print(f"  📊 Analyzing page {i}/{len(pages)}...")

            try:
                # Get page content and skip empty pages
                try:
                    content = self.get_page_content(wiki_id, page['id'])
                    if not content or not content.strip():
                        print(f"  ℹ️  Skipping empty page: {page['path']}")
                        continue

                except Exception as e:
                    print(f"  ⚠️  Error getting content for {page['path']}: {e}")
                    continue

                # Perform detailed content analysis
                page_analysis = self.analyze_content_complexity(content)
                page_analysis['path'] = page['path']
                page_analysis['id'] = page['id']

                # Update overall statistics
                analysis['pages_analyzed'] += 1
                analysis['pages_with_content'] += 1
                analysis['total_complexity_score'] += int(page_analysis['complexity_score'])
                analysis['complexity_distribution'][str(page_analysis['complexity_level'])] += 1

                # Aggregate content statistics across all pages
                for key in analysis['content_stats']:
                    stat_key = key.replace('total_', '')
                    analysis['content_stats'][key] += int(page_analysis.get(stat_key, 0))

                analysis['page_details'].append(page_analysis)

                # Track largest pages (potential performance concerns)
                if int(page_analysis['word_count']) > 500:
                    analysis['largest_pages'].append({
                        'path': page['path'],
                        'word_count': int(page_analysis['word_count']),
                        'complexity_level': str(page_analysis['complexity_level'])
                    })

                # Track most complex pages (require special attention)
                if int(page_analysis['complexity_score']) > 15:
                    page_issues = []

                    # Identify specific issues that need manual handling
                    if int(page_analysis['images']) > 0:
                        page_issues.append(f"{page_analysis['images']} images (need manual handling)")
                    if int(page_analysis['tables']) > 3:
                        page_issues.append(f"{page_analysis['tables']} tables (complex conversion)")
                    if int(page_analysis['html_tags']) > 0:
                        page_issues.append(f"{page_analysis['html_tags']} HTML tags (may need conversion)")
                    if int(page_analysis['code_blocks']) > 5:
                        page_issues.append(f"{page_analysis['code_blocks']} code blocks (check syntax highlighting)")

                    analysis['most_complex_pages'].append({
                        'path': page['path'],
                        'complexity_score': int(page_analysis['complexity_score']),
                        'complexity_level': str(page_analysis['complexity_level']),
                        'issues': page_issues
                    })

            except Exception as e:
                print(f"  ⚠️ Error analyzing page {page['path']}: {e}")
                continue

        # Sort and limit results for reporting
        analysis['largest_pages'].sort(key=lambda x: x['word_count'], reverse=True)
        analysis['most_complex_pages'].sort(key=lambda x: x['complexity_score'], reverse=True)

        # Keep only top 10 for cleaner reports
        analysis['largest_pages'] = analysis['largest_pages'][:10]
        analysis['most_complex_pages'] = analysis['most_complex_pages'][:10]

        return analysis

    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a comprehensive, formatted migration analysis report.

        Creates a detailed markdown report with migration recommendations,
        complexity assessment, time estimates, and actionable checklists.

        Args:
            analysis (Dict[str, Any]): Analysis results from analyze_wiki()

        Returns:
            str: Formatted markdown report ready for saving or display

        Raises:
            ValueError: If analysis data is empty or invalid

        Note:
            The report includes:
            - Executive summary with key metrics
            - Complexity breakdown and recommendations
            - Pre/during/post migration checklists
            - Time estimation based on content complexity
            - Specific pages requiring attention
        """
        if not analysis:
            return "No analysis data available. Please run wiki analysis first."

        # Calculate key metrics for the summary
        pages_with_content = analysis.get('pages_with_content', 0)
        if pages_with_content == 0:
            return "No pages with content found in the analysis."

        avg_complexity = analysis['total_complexity_score'] / pages_with_content
        time_estimate = self._calculate_time_estimate(analysis)

        # Generate comprehensive markdown report
        report = f"""# Azure DevOps Wiki Migration Analysis Report

## 📊 Executive Summary
- **Wiki Name**: {analysis['wiki_info']['name']}
- **Total Pages**: {analysis['total_pages']:,}
- **Pages with Content**: {pages_with_content:,}
- **Empty Pages**: {analysis['total_pages'] - pages_with_content:,}
- **Average Complexity Score**: {avg_complexity:.1f}
- **Estimated Migration Time**: {time_estimate}

## 📈 Content Statistics
- **Total Words**: {analysis['content_stats']['total_words']:,}
- **Total Characters**: {analysis['content_stats']['total_chars']:,}
- **Total Lines**: {analysis['content_stats']['total_lines']:,}
- **Headers**: {analysis['content_stats']['total_headers']:,}
- **Links**: {analysis['content_stats']['total_links']:,}
- **Images**: {analysis['content_stats']['total_images']:,} ⚠️ *Need manual handling*
- **Code Blocks**: {analysis['content_stats']['total_code_blocks']:,}
- **Tables**: {analysis['content_stats']['total_tables']:,}

## 🎯 Migration Complexity Assessment

### Complexity Distribution
- **Low Complexity**: {analysis['complexity_distribution']['Low']:,} pages (easy migration)
- **Medium Complexity**: {analysis['complexity_distribution']['Medium']:,} pages (moderate attention needed)
- **High Complexity**: {analysis['complexity_distribution']['High']:,} pages (requires careful review)

### Risk Assessment
"""

        # Add complexity-based recommendations
        high_complexity_pages = analysis['complexity_distribution']['High']
        if high_complexity_pages == 0:
            report += "✅ **Low Risk Migration** - No high-complexity pages detected\n\n"
        elif high_complexity_pages < 5:
            report += "⚠️ **Medium Risk Migration** - Few complex pages, manageable effort\n\n"
        else:
            report += "🚨 **High Risk Migration** - Many complex pages require significant planning\n\n"

        report += """## 📋 Migration Recommendations

### ✅ Low Risk Items (Auto-convertible)
- Headers and text formatting
- Basic lists and bullet points
- Simple links and bold/italic text
- Inline code snippets

### ⚠️ Medium Risk Items (Review Needed)
- Tables with complex formatting
- Multiple code blocks per page
- Pages with many internal links

### 🚨 High Risk Items (Manual Attention Required)
- **Images and attachments** ({:,} total)
- Pages with HTML tags
- Very large pages (>1000 words)
- Complex table structures

## 🔍 Pages Requiring Special Attention

### 📚 Largest Pages (Top 10)
""".format(analysis['content_stats']['total_images'])

        # Add largest pages section
        if analysis['largest_pages']:
            for i, page in enumerate(analysis['largest_pages'], 1):
                report += f"{i}. **{page['path']}** - {page['word_count']:,} words ({page['complexity_level']} complexity)\n"
        else:
            report += "No particularly large pages found.\n"

        report += "\n### 🔧 Most Complex Pages (Top 10)\n"

        # Add most complex pages section
        if analysis['most_complex_pages']:
            for i, page in enumerate(analysis['most_complex_pages'], 1):
                report += f"{i}. **{page['path']}** - Score: {page['complexity_score']} ({page['complexity_level']})\n"
                if page['issues']:
                    for issue in page['issues']:
                        report += f"   - {issue}\n"
        else:
            report += "No particularly complex pages found.\n"

        # Add detailed checklists and recommendations
        report += f"""

## 📋 Pre-Migration Checklist

### Before Starting Migration
- [ ] **Backup current MediaWiki** (if existing)
- [ ] **Download all images/attachments** from Azure DevOps manually
- [ ] **Review the {analysis['complexity_distribution']['High']} high-complexity pages** listed above
- [ ] **Set up test MediaWiki instance** for validation
- [ ] **Configure MediaWiki extensions** needed for code syntax highlighting

### During Migration
- [ ] **Start with low-complexity pages** to test the process
- [ ] **Migrate high-complexity pages manually** or with extra review
- [ ] **Handle images separately** - upload to MediaWiki and update links
- [ ] **Test internal links** after migration
- [ ] **Verify table formatting** in MediaWiki

### After Migration
- [ ] **Review all {analysis['content_stats']['total_links']:,} links** for correctness
- [ ] **Test search functionality** in MediaWiki
- [ ] **Set up user permissions** and access controls
- [ ] **Train users** on MediaWiki differences
- [ ] **Create redirect pages** if needed for bookmarked URLs

## 🎯 Estimated Migration Time

Based on the analysis:
- **Low complexity pages** ({analysis['complexity_distribution']['Low']:,}): ~2-5 minutes each
- **Medium complexity pages** ({analysis['complexity_distribution']['Medium']:,}): ~10-15 minutes each
- **High complexity pages** ({analysis['complexity_distribution']['High']:,}): ~30-60 minutes each
- **Image handling**: {analysis['content_stats']['total_images']:,} images × 5-10 minutes each

**Total Estimated Time**: {time_estimate}

## 🚀 Next Steps

1. **Review this report** with your team
2. **Plan the migration schedule** based on page complexity
3. **Set up test environment** using the provided Docker Compose
4. **Configure the migration script** with your credentials
5. **Start with a small batch** of low-complexity pages for testing

---
*Report generated by MediaWiki Migration Analysis Tool on {self._get_current_date()}*
"""

        return report

    def _calculate_time_estimate(self, analysis: Dict[str, Any]) -> str:
        """
        Calculate estimated time required for the complete migration process.

        Uses complexity-based time estimates to provide realistic project planning.

        Args:
            analysis (Dict[str, Any]): Analysis results containing complexity distribution

        Returns:
            str: Human-readable time estimate (e.g., "2.5 hours", "3.2 work days")

        Note:
            Time estimates per page type:
            - Low complexity: 3 minutes average
            - Medium complexity: 12 minutes average
            - High complexity: 45 minutes average
            - Images: 7 minutes each for download/upload
        """
        # Calculate time based on page complexity (in minutes)
        low_time = analysis['complexity_distribution']['Low'] * 3      # 3 min avg per low complexity
        medium_time = analysis['complexity_distribution']['Medium'] * 12  # 12 min avg per medium complexity
        high_time = analysis['complexity_distribution']['High'] * 45     # 45 min avg per high complexity
        image_time = analysis['content_stats']['total_images'] * 7       # 7 min avg per image

        total_minutes = low_time + medium_time + high_time + image_time

        # Convert to human-readable format
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        elif total_minutes < 480:  # Less than 8 hours
            hours = total_minutes / 60
            return f"{hours:.1f} hours"
        else:  # 8+ hours, convert to work days
            days = total_minutes / 480  # 8-hour work days
            return f"{days:.1f} work days"

    def _get_current_date(self) -> str:
        """
        Get current date in a readable format for report timestamps.

        Returns:
            str: Current date in format "Month Day, Year"
        """
        return datetime.now().strftime("%B %d, %Y")


def load_config() -> Tuple[str, str, str, Optional[str]]:
    """
    Load and validate Azure DevOps configuration from environment variables.

    Reads configuration from .env file or environment variables for secure
    credential management. All credentials should be kept out of source code.

    Returns:
        Tuple[str, str, str, Optional[str]]: Organization, project, PAT token, and optional wiki name

    Raises:
        SystemExit: If required environment variables are missing

    Environment Variables Required:
        - AZURE_DEVOPS_ORGANIZATION: Azure DevOps organization name
        - AZURE_DEVOPS_PROJECT: Project name within the organization
        - AZURE_DEVOPS_PAT: Personal Access Token with wiki read permissions
        - AZURE_WIKI_NAME: (Optional) Specific wiki name to analyze

    Example:
        Create a .env file with:
        AZURE_DEVOPS_ORGANIZATION=myorg
        AZURE_DEVOPS_PROJECT=myproject
        AZURE_DEVOPS_PAT=your_personal_access_token
        AZURE_WIKI_NAME=ProjectDocs
    """
    load_dotenv()

    # Load required configuration
    azure_org = os.getenv("AZURE_DEVOPS_ORGANIZATION")
    azure_project = os.getenv("AZURE_DEVOPS_PROJECT")
    azure_pat = os.getenv("AZURE_DEVOPS_PAT")
    wiki_name = os.getenv("AZURE_WIKI_NAME")  # Optional

    # Validate required variables are present and not empty
    if not azure_org or not azure_project or not azure_pat:
        print("❌ Missing required environment variables:")
        print("Please set: AZURE_DEVOPS_ORGANIZATION, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_PAT")
        print("\nCreate a .env file or set environment variables with your Azure DevOps credentials.")
        sys.exit(1)

    # Type checker now knows these are not None due to the check above
    return azure_org, azure_project, azure_pat, wiki_name


def main() -> None:
    """
    Main entry point for the migration analysis tool.

    Orchestrates the complete analysis workflow:
    1. Validates required dependencies
    2. Loads configuration from environment
    3. Connects to Azure DevOps and analyzes wiki
    4. Generates comprehensive report
    5. Saves results and provides user feedback

    Raises:
        SystemExit: If dependencies missing, configuration invalid, or analysis fails

    Example Usage:
        python migration_planner.py

    Output:
        Creates migration_analysis_report.md with detailed analysis and recommendations
    """
    print("🔍 Azure DevOps Wiki Migration Analysis Tool")
    print("=" * 55)

    # Verify required Python packages are installed
    try:
        import requests
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Required package not installed: {e}")
        print("Please install dependencies: pip install requests python-dotenv")
        sys.exit(1)

    # Load and validate configuration
    try:
        azure_org, azure_project, azure_pat, wiki_name = load_config()
    except SystemExit:
        raise  # Re-raise configuration errors
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    try:
        # Initialize the migration planner with Azure DevOps credentials
        print(f"🔗 Connecting to Azure DevOps: {azure_org}/{azure_project}")
        planner = MigrationPlanner(azure_org, azure_project, azure_pat)

        # Perform comprehensive wiki analysis
        print("📊 Starting analysis...")
        analysis = planner.analyze_wiki(wiki_name if wiki_name else None)

        if analysis:
            # Generate and save detailed report
            print("📝 Generating report...")
            report = planner.generate_report(analysis)

            # Save report to file
            report_file = "migration_analysis_report.md"
            try:
                # Ensure we can write to the current directory
                if not os.access('.', os.W_OK):
                    print("❌ No write permission to current directory")
                    print(f"💡 Please run from a directory with write permissions")
                    sys.exit(1)

                with open(report_file, "w", encoding='utf-8') as f:
                    f.write(report)
                    f.flush()  # Ensure data is written

            except PermissionError:
                print(f"❌ Permission denied: Cannot write report to {report_file}")
                print("💡 Try running from a directory with write permissions")
                sys.exit(1)
            except OSError as e:
                if e.errno == 28:  # No space left on device
                    print("❌ Insufficient disk space to save report")
                else:
                    print(f"❌ System error saving report: {e}")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Unexpected error saving report: {e}")
                sys.exit(1)

            # Provide summary feedback to user
            print(f"\n✅ Analysis complete!")
            print(f"📄 Report saved to: {report_file}")
            print(f"📊 Analyzed {analysis['pages_with_content']:,} pages")
            print(f"⚠️  Found {analysis['complexity_distribution']['High']:,} high-complexity pages")
            print(f"📸 Found {analysis['content_stats']['total_images']:,} images requiring manual handling")

            # Show next steps
            if analysis['complexity_distribution']['High'] > 0:
                print(f"\n🎯 Recommendation: Review high-complexity pages before starting migration")
            if analysis['content_stats']['total_images'] > 0:
                print(f"🖼️  Recommendation: Plan time for manual image migration")

            print(f"\n🔗 Open {report_file} to see the full analysis and recommendations!")

        else:
            print("❌ No analysis results generated. Check wiki access and try again.")
            sys.exit(1)

    except requests.RequestException as e:
        print(f"❌ Azure DevOps API error: {e}")
        print("Check your credentials and network connection.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("Please check the error details and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
