#!/usr/bin/env python3
"""
Post-Migration Validation Tool
Validates that your Azure DevOps wiki migration to MediaWiki was successful

Author: Johan Sörell
Contact: https://github.com/J-SirL | https://se.linkedin.com/in/johansorell | automationblueprint.site
Date: 2025
Version: 1.0.0
"""

import os
import sys
import json
import re
import time
import pickle
from typing import Dict, List, Tuple, Set, Optional, Union
from urllib.parse import urljoin, urlparse

import requests
from dotenv import load_dotenv


class MigrationValidator:
    """Validates migration results between Azure DevOps and MediaWiki"""

    def __init__(self, mediawiki_url: str, username: str, password: str):
        self.mediawiki_url = mediawiki_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.api_url = f"{self.mediawiki_url}/api.php"
        self._logged_in = False

    def _make_request(self, method: str = "POST", max_retries: int = 3, **params) -> dict:
        """Make a request to the MediaWiki API with retry logic"""
        for attempt in range(max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(self.api_url, params=params, timeout=30)
                else:
                    response = self.session.post(self.api_url, data=params, timeout=30)

                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    print(f"❌ MediaWiki API request timed out after {max_retries} attempts")
                    raise
                print(f"⏳ Request timed out, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    print(f"❌ MediaWiki connection failed: {e}")
                    raise
                print(f"⚠️  Connection error, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code >= 500:
                    if attempt == max_retries - 1:
                        print(f"❌ MediaWiki server error: {e.response.status_code}")
                        raise
                    print(f"⚠️  Server error, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)
                else:
                    print(f"❌ MediaWiki API request failed: {e}")
                    raise
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response from MediaWiki: {e}")
                print("💡 MediaWiki might be returning HTML error page")
                raise
                
        return {}

    def login(self):
        """Login to MediaWiki"""
        if self._logged_in:
            return

        print(f"🔐 Logging into MediaWiki as {self.username}...")

        # Get login token
        response = self._make_request(
            action="query",
            meta="tokens",
            type="login",
            format="json"
        )

        login_token = response.get("query", {}).get("tokens", {}).get("logintoken")
        if not login_token:
            raise Exception("Failed to get login token from MediaWiki")

        # Login
        response = self._make_request(
            action="login",
            lgname=self.username,
            lgpassword=self.password,
            lgtoken=login_token,
            format="json"
        )

        login_result = response.get("login", {}).get("result")
        if login_result != "Success":
            raise Exception(f"MediaWiki login failed: {login_result}")

        self._logged_in = True
        print("✅ Successfully logged into MediaWiki")

    def get_all_pages(self) -> List[Dict]:
        """Get all pages from MediaWiki"""
        self.login()
        all_pages = []
        apcontinue = None

        while True:
            params = {
                'action': 'query',
                'list': 'allpages',
                'aplimit': 500,
                'format': 'json'
            }

            if apcontinue:
                params['apcontinue'] = apcontinue

            response = self._make_request(**params)
            pages = response.get('query', {}).get('allpages', [])
            all_pages.extend(pages)

            apcontinue = response.get('continue', {}).get('apcontinue')
            if not apcontinue:
                break

        return all_pages

    def get_page_content(self, title: str) -> str:
        """Get content of a specific page"""
        self.login()

        response = self._make_request(
            action='query',
            titles=title,
            prop='revisions',
            rvprop='content',
            format='json'
        )

        pages = response.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if 'revisions' in page_data:
                return page_data['revisions'][0]['*']

        return ""

    def check_page_accessibility(self, title: str) -> Dict:
        """Check if a page is accessible and loads properly"""
        try:
            # Try API access
            content = self.get_page_content(title)
            api_accessible = len(content) > 0

            # Try web access
            page_url = f"{self.mediawiki_url}/wiki/{title.replace(' ', '_')}"
            web_response = requests.get(page_url, timeout=10)
            web_accessible = web_response.status_code == 200

            return {
                'api_accessible': api_accessible,
                'web_accessible': web_accessible,
                'content_length': len(content),
                'status_code': web_response.status_code if not web_accessible else 200
            }
        except Exception as e:
            return {
                'api_accessible': False,
                'web_accessible': False,
                'content_length': 0,
                'error': str(e),
                'status_code': 0
            }

    def analyze_content_quality(self, title: str, content: str) -> Dict[str, Union[str, int, List[str]]]:
        """Analyze the quality of migrated content"""
        analysis: Dict[str, Union[str, int, List[str]]] = {
            'title': title,
            'length': len(content),
            'word_count': len(content.split()),
            'issues': [],
            'warnings': [],
            'quality_score': 100
        }

        # Check for common migration issues
        if '[[File:' not in content and '![' in content:
            analysis['issues'].append("Contains markdown image syntax - images may not display")
            analysis['quality_score'] -= 20

        # Check for unconverted markdown
        markdown_patterns = [
            (r'\*\*.*?\*\*', "Bold markdown not converted"),
            (r'\*.*?\*', "Italic markdown not converted"),
            (r'```.*?```', "Code block markdown not converted"),
            (r'\[.*?\]\(.*?\)', "Link markdown not converted"),
            (r'^#+\s', "Header markdown not converted")
        ]

        for pattern, issue in markdown_patterns:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                analysis['issues'].append(issue)
                analysis['quality_score'] -= 15

        # Check for broken internal links
        internal_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        if internal_links:
            analysis['internal_links'] = len(internal_links)

        # Check for HTML that might not render properly
        html_tags = re.findall(r'<([a-zA-Z]+)[^>]*>', content)
        if html_tags:
            analysis['html_tags'] = len(html_tags)
            analysis['warnings'].append(f"Contains {len(html_tags)} HTML tags - verify they render correctly")

        # Check for empty or very short content
        if len(content.strip()) < 50:
            analysis['warnings'].append("Very short content - may be incomplete migration")
            analysis['quality_score'] -= 10

        # Assign quality level
        if analysis['quality_score'] >= 90:
            analysis['quality_level'] = 'Excellent'
        elif analysis['quality_score'] >= 75:
            analysis['quality_level'] = 'Good'
        elif analysis['quality_score'] >= 60:
            analysis['quality_level'] = 'Fair'
        else:
            analysis['quality_level'] = 'Poor'

        return analysis

    def validate_internal_links(self, pages: List[Dict], sample_size: int = 50) -> Dict:
        """Validate internal links within migrated content"""
        print(f"🔗 Validating internal links (sampling {min(sample_size, len(pages))} pages)...")

        # Get page titles for reference
        page_titles = {page['title'] for page in pages}

        link_validation = {
            'total_links_checked': 0,
            'valid_links': 0,
            'broken_links': 0,
            'broken_link_details': [],
            'pages_with_broken_links': []
        }

        # Sample pages to check
        sample_pages = pages[:sample_size] if len(pages) > sample_size else pages

        for page in sample_pages:
            try:
                content = self.get_page_content(page['title'])
                internal_links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)

                page_broken_links = []

                for link in internal_links:
                    link_validation['total_links_checked'] += 1

                    # Check if the linked page exists
                    if link in page_titles:
                        link_validation['valid_links'] += 1
                    else:
                        link_validation['broken_links'] += 1
                        page_broken_links.append(link)

                if page_broken_links:
                    link_validation['pages_with_broken_links'].append({
                        'page': page['title'],
                        'broken_links': page_broken_links
                    })

                    link_validation['broken_link_details'].extend([
                        f"{page['title']} -> {link}" for link in page_broken_links
                    ])

            except Exception as e:
                print(f"  ⚠️  Error checking links in {page['title']}: {e}")
                continue

        return link_validation

    def run_comprehensive_validation(self, expected_pages: Optional[List[str]] = None) -> Dict:
        """Run comprehensive migration validation"""
        print("🔍 Starting comprehensive migration validation...")

        validation_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'mediawiki_url': self.mediawiki_url,
            'pages_found': 0,
            'pages_accessible': 0,
            'pages_with_issues': 0,
            'total_issues': 0,
            'total_warnings': 0,
            'quality_distribution': {'Excellent': 0, 'Good': 0, 'Fair': 0, 'Poor': 0},
            'page_details': [],
            'summary': {},
            'recommendations': []
        }

        # Get all pages
        print("📄 Fetching all pages from MediaWiki...")
        pages = self.get_all_pages()
        validation_results['pages_found'] = len(pages)

        print(f"📊 Found {len(pages)} pages to validate")

        if expected_pages:
            missing_pages = set(expected_pages) - {p['title'] for p in pages}
            if missing_pages:
                validation_results['missing_pages'] = list(missing_pages)
                print(f"⚠️  {len(missing_pages)} expected pages not found")

        # Validate each page
        for i, page in enumerate(pages[:100]):  # Limit to 100 pages for performance
            if i % 10 == 0:
                print(f"  📋 Validating page {i+1}/{min(len(pages), 100)}...")

            title = page['title']

            # Check accessibility
            access_check = self.check_page_accessibility(title)

            if access_check['api_accessible']:
                validation_results['pages_accessible'] += 1

                # Get content and analyze quality
                content = self.get_page_content(title)
                quality_analysis = self.analyze_content_quality(title, content)

                validation_results['page_details'].append({
                    'title': title,
                    'accessible': True,
                    'quality': quality_analysis,
                    'content_length': len(content)
                })

                # Update counters
                if quality_analysis['issues']:
                    validation_results['pages_with_issues'] += 1
                    validation_results['total_issues'] += len(quality_analysis['issues'])

                validation_results['total_warnings'] += len(quality_analysis['warnings'])
                validation_results['quality_distribution'][quality_analysis['quality_level']] += 1

            else:
                validation_results['page_details'].append({
                    'title': title,
                    'accessible': False,
                    'error': access_check.get('error', 'Unknown error')
                })

        # Validate internal links
        link_validation = self.validate_internal_links(pages[:50])  # Sample 50 pages
        validation_results['link_validation'] = link_validation

        # Generate summary and recommendations
        validation_results['summary'] = self._generate_summary(validation_results)
        validation_results['recommendations'] = self._generate_recommendations(validation_results)

        return validation_results

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate validation summary"""
        total_pages = results['pages_found']
        accessible_pages = results['pages_accessible']
        issues_pages = results['pages_with_issues']

        success_rate = (accessible_pages / total_pages * 100) if total_pages > 0 else 0
        quality_rate = ((accessible_pages - issues_pages) / accessible_pages * 100) if accessible_pages > 0 else 0

        return {
            'total_pages': total_pages,
            'accessibility_success_rate': round(success_rate, 1),
            'quality_success_rate': round(quality_rate, 1),
            'pages_with_issues': issues_pages,
            'total_issues_found': results['total_issues'],
            'link_validation': {
                'broken_links': results.get('link_validation', {}).get('broken_links', 0),
                'total_links_checked': results.get('link_validation', {}).get('total_links_checked', 0)
            }
        }

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Accessibility recommendations
        inaccessible_pages = results['pages_found'] - results['pages_accessible']
        if inaccessible_pages > 0:
            recommendations.append(
                f"🔧 Fix {inaccessible_pages} inaccessible pages - check page titles and permissions"
            )

        # Quality recommendations
        if results['pages_with_issues'] > 0:
            recommendations.append(
                f"📝 Review {results['pages_with_issues']} pages with content issues"
            )

        # Specific issue recommendations
        poor_quality_pages = results['quality_distribution'].get('Poor', 0)
        if poor_quality_pages > 0:
            recommendations.append(
                f"⚠️  Manually review {poor_quality_pages} pages with poor quality scores"
            )

        # Link recommendations
        link_validation = results.get('link_validation', {})
        broken_links = link_validation.get('broken_links', 0)
        if broken_links > 0:
            recommendations.append(
                f"🔗 Fix {broken_links} broken internal links"
            )

        # Missing pages
        if 'missing_pages' in results:
            recommendations.append(
                f"📄 Investigate {len(results['missing_pages'])} missing expected pages"
            )

        # General recommendations
        if not recommendations:
            recommendations.append("🎉 Migration validation looks excellent! No major issues found.")
        else:
            recommendations.append("📋 After fixes, run validation again to verify improvements")

        return recommendations

    def generate_validation_report(self, results: Dict) -> str:
        """Generate a comprehensive validation report"""
        report = f"""# MediaWiki Migration Validation Report

**Generated**: {results['timestamp']}
**MediaWiki URL**: {results['mediawiki_url']}

## 📊 Overall Results

### Migration Success Metrics
- **Pages Found**: {results['pages_found']}
- **Pages Accessible**: {results['pages_accessible']} ({results['summary']['accessibility_success_rate']}%)
- **Pages with Issues**: {results['pages_with_issues']}
- **Quality Success Rate**: {results['summary']['quality_success_rate']}%

### Content Quality Distribution
"""

        for quality, count in results['quality_distribution'].items():
            percentage = (count / results['pages_accessible'] * 100) if results['pages_accessible'] > 0 else 0
            report += f"- **{quality}**: {count} pages ({percentage:.1f}%)\n"

        # Link validation results
        link_val = results.get('link_validation', {})
        if link_val.get('total_links_checked', 0) > 0:
            report += f"\n### 🔗 Link Validation\n"
            report += f"- **Total Internal Links Checked**: {link_val['total_links_checked']}\n"
            report += f"- **Valid Links**: {link_val['valid_links']}\n"
            report += f"- **Broken Links**: {link_val['broken_links']}\n"

            if link_val['broken_links'] > 0:
                link_success_rate = (link_val['valid_links'] / link_val['total_links_checked'] * 100)
                report += f"- **Link Success Rate**: {link_success_rate:.1f}%\n"

        # Missing pages
        if 'missing_pages' in results:
            report += f"\n### 📄 Missing Pages\n"
            report += f"Expected but not found: {len(results['missing_pages'])} pages\n\n"
            for page in results['missing_pages'][:10]:  # Show first 10
                report += f"- {page}\n"
            if len(results['missing_pages']) > 10:
                report += f"... and {len(results['missing_pages']) - 10} more\n"

        # Issues breakdown
        report += f"\n## 🚨 Issues Found\n\n"

        issues_by_type: Dict[str, int] = {}
        for page_detail in results['page_details']:
            if 'quality' in page_detail and page_detail['quality']['issues']:
                for issue in page_detail['quality']['issues']:
                    issues_by_type[issue] = issues_by_type.get(issue, 0) + 1

        if issues_by_type:
            for issue, count in sorted(issues_by_type.items(), key=lambda x: x[1], reverse=True):
                report += f"- **{issue}**: {count} pages\n"
        else:
            report += "🎉 No content issues found!\n"

        # Broken links details
        if link_val.get('broken_links', 0) > 0:
            report += f"\n### 🔗 Broken Links Details\n\n"
            for page_info in link_val.get('pages_with_broken_links', [])[:10]:
                report += f"**{page_info['page']}**:\n"
                for link in page_info['broken_links'][:5]:  # Show first 5 broken links
                    report += f"  - {link}\n"
                report += "\n"

        # Recommendations
        report += f"\n## 🎯 Recommendations\n\n"
        for recommendation in results['recommendations']:
            report += f"- {recommendation}\n"

        # Next steps
        report += f"""
## 🚀 Next Steps

### Immediate Actions
1. **Fix broken internal links** - Update page references
2. **Review pages with poor quality scores** - Manual content verification
3. **Test key user workflows** - Ensure critical pages work correctly
4. **Update bookmarks and documentation** - Point to new MediaWiki URLs

### Ongoing Maintenance
1. **Set up regular backups** - Protect migrated content
2. **Monitor user feedback** - Address usability issues
3. **Plan MediaWiki updates** - Keep system secure and updated
4. **Train users** - Help team adapt to new wiki system

### Validation Commands
To re-run this validation after fixes:
```bash
python post_migration_validator.py
```

---
*Validation report generated by MediaWiki Migration Tools*
"""

        return report


def load_config() -> Tuple[str, str, str]:
    """Load configuration from .env file"""
    load_dotenv()

    wiki_url = os.getenv("WIKI_URL")
    wiki_username = os.getenv("WIKI_USERNAME")
    wiki_password = os.getenv("WIKI_PASSWORD")

    if not wiki_url or not wiki_username or not wiki_password:
        print("❌ Missing required environment variables!")
        print("Please set: WIKI_URL, WIKI_USERNAME, WIKI_PASSWORD")
        sys.exit(1)

    # Type checker now knows these are not None due to the check above
    return wiki_url, wiki_username, wiki_password


def main():
    """Main function"""
    print("✅ Post-Migration Validation Tool")
    print("=" * 40)

    # Check required packages
    try:
        import requests
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Required package not installed: {e}")
        print("Please install: pip install requests python-dotenv")
        sys.exit(1)

    # Load configuration
    wiki_url, wiki_username, wiki_password = load_config()

    try:
        # Initialize validator
        validator = MigrationValidator(wiki_url, wiki_username, wiki_password)

        print(f"🔗 Connecting to MediaWiki: {wiki_url}")

        # Run validation
        validation_results = validator.run_comprehensive_validation()

        # Generate report
        report = validator.generate_validation_report(validation_results)

        # Save report
        report_file = "migration_validation_report.md"
        with open(report_file, "w", encoding='utf-8') as f:
            f.write(report)

        # Show summary
        summary = validation_results['summary']
        print(f"\n🎉 Validation complete!")
        print(f"📄 Report saved to: {report_file}")
        print(f"📊 Found {summary['total_pages']} pages")
        print(f"✅ {summary['accessibility_success_rate']}% accessibility success rate")
        print(f"⭐ {summary['quality_success_rate']}% quality success rate")

        if summary['total_issues_found'] > 0:
            print(f"⚠️  Found {summary['total_issues_found']} issues to review")

        broken_links = summary.get('link_validation', {}).get('broken_links', 0)
        if broken_links > 0:
            print(f"🔗 Found {broken_links} broken internal links")

        print(f"\n📖 Open {report_file} for detailed analysis and recommendations!")

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()