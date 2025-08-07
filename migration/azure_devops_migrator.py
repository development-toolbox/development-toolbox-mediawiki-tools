#!/usr/bin/env python3
"""
Azure DevOps to MediaWiki Migration Script
This script migrates wiki pages from Azure DevOps to MediaWiki

Author: Johan Sörell
Contact: https://github.com/J-SirL | https://se.linkedin.com/in/johansorell | automationblueprint.site
Date: 2025
Version: 1.0.0
"""

import os
import sys
import json
import re
import base64
import time
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from dotenv import load_dotenv


class AzureDevOpsWikiClient:
    """Client for Azure DevOps Wiki REST API"""

    def _make_api_request(self, method: str, url: str, max_retries: int = 3, 
                         backoff_factor: float = 1.0) -> Dict:
        """
        Make API request with retry logic and proper error handling.
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
                    raise
                wait_time = backoff_factor * (2 ** attempt)
                print(f"⏳ Request timed out, retrying in {wait_time}s...")
                time.sleep(wait_time)
                
            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    raise
                wait_time = backoff_factor * (2 ** attempt)
                print(f"⚠️  Connection error, retrying in {wait_time}s...")
                time.sleep(wait_time)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    print(f"⏳ Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                else:
                    raise
                    
        return {}
        
    def __init__(self, organization: str, project: str, personal_access_token: str):
        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        self.session = requests.Session()

        # Set up authentication
        auth_string = f":{personal_access_token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'User-Agent': 'MediaWiki-Migration-Tool/1.0'
        })

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
        try:
            response = self._make_api_request('GET', url)
            return response.get('content', '')
        except requests.RequestException as e:
            print(f"⚠️  Failed to retrieve content for page {page_id}: {e}")
            return ''  # Return empty content rather than crashing


class MediaWikiClient:
    """Client for MediaWiki API"""

    def __init__(self, wiki_url: str, username: str, password: str):
        self.wiki_url = wiki_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.api_url = f"{self.wiki_url}/api.php"
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
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    print(f"❌ MediaWiki connection failed: {e}")
                    print("💡 Check MediaWiki URL and network connectivity")
                    raise
                print(f"⚠️  Connection error, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    print("❌ MediaWiki authentication failed - check username/password")
                    raise
                elif e.response.status_code == 403:
                    print("❌ MediaWiki access denied - check user permissions")
                    raise
                elif e.response.status_code >= 500:
                    if attempt == max_retries - 1:
                        print(f"❌ MediaWiki server error: {e.response.status_code}")
                        raise
                    print(f"⚠️  Server error, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)  # Longer wait for server errors
                else:
                    print(f"❌ MediaWiki API request failed: {e}")
                    raise
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response from MediaWiki: {e}")
                print("💡 MediaWiki might be returning HTML error page")
                raise
                
        return {}

    def login(self):
        """Login to MediaWiki with comprehensive error handling"""
        if self._logged_in:
            return

        print(f"🔐 Logging into MediaWiki as {self.username}...")

        try:
            # Get login token
            response = self._make_request(
                "GET",
                action="query",
                meta="tokens",
                type="login",
                format="json"
            )

            login_token = response.get("query", {}).get("tokens", {}).get("logintoken")
            if not login_token:
                raise Exception("Failed to get login token from MediaWiki - check MediaWiki configuration")

            # Login
            response = self._make_request(
                "POST",
                action="login",
                lgname=self.username,
                lgpassword=self.password,
                lgtoken=login_token,
                format="json"
            )

            login_result = response.get("login", {}).get("result")
            if login_result == "Success":
                self._logged_in = True
                print("✅ Successfully logged into MediaWiki")
            elif login_result == "Failed":
                error_msg = response.get("login", {}).get("reason", "Unknown login failure")
                raise Exception(f"MediaWiki login failed: {error_msg}")
            elif login_result == "NeedToken":
                raise Exception("Login token issue - this shouldn't happen in normal flow")
            else:
                raise Exception(f"Unexpected MediaWiki login result: {login_result}")
                
        except Exception as e:
            print(f"❌ MediaWiki login failed: {e}")
            print("💡 Common solutions:")
            print("   - Verify username and password are correct")
            print("   - Check if user has appropriate permissions")
            print("   - Ensure MediaWiki API is accessible")
            raise

    def create_page(self, title: str, content: str, summary: str = "Migrated from Azure DevOps") -> bool:
        """Create or update a page in MediaWiki"""
        self.login()

        # Get edit token
        response = self._make_request(
            action="query",
            meta="tokens",
            format="json"
        )

        edit_token = response.get("query", {}).get("tokens", {}).get("csrftoken")
        if not edit_token:
            raise Exception("Failed to get edit token from MediaWiki")

        # Create/edit page
        response = self._make_request(
            action="edit",
            title=title,
            text=content,
            token=edit_token,
            summary=summary,
            format="json"
        )

        edit_result = response.get("edit", {}).get("result")
        if edit_result == "Success":
            return True
        else:
            error_msg = response.get("error", {}).get("info", "Unknown error")
            print(f"❌ Failed to create page '{title}': {error_msg}")
            return False


class ContentConverter:
    """Converts content from Markdown (Azure DevOps) to MediaWiki syntax"""

    @staticmethod
    def markdown_to_mediawiki(markdown_content: str) -> str:
        """Convert Markdown to MediaWiki syntax"""
        content = markdown_content

        # Headers
        content = re.sub(r'^# (.+)$', r'= \1 =', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'== \1 ==', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'=== \1 ===', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.+)$', r'==== \1 ====', content, flags=re.MULTILINE)
        content = re.sub(r'^##### (.+)$', r'===== \1 =====', content, flags=re.MULTILINE)

        # Bold and italic
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

        return content

    @staticmethod
    def sanitize_page_title(title: str) -> str:
        """Sanitize page title for MediaWiki"""
        # Remove .md extension
        title = re.sub(r'\.md$', '', title)

        # Replace underscores and hyphens with spaces
        title = title.replace('_', ' ').replace('-', ' ')

        # Capitalize first letter of each word
        title = ' '.join(word.title() for word in title.split())

        return title


class ProgressTracker:
    """Track migration progress with resume capability"""
    
    def __init__(self, checkpoint_file: str = '.migration_checkpoint'):
        self.checkpoint_file = checkpoint_file
        self.progress = self.load_checkpoint() or {
            'processed_pages': set(),
            'failed_pages': {},
            'skipped_pages': {},
            'start_time': time.time()
        }
    
    def load_checkpoint(self) -> Optional[Dict]:
        """Load progress from checkpoint file"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'rb') as f:
                    data = pickle.load(f)
                print(f"📊 Resuming migration from checkpoint ({len(data['processed_pages'])} pages completed)")
                return data
        except Exception as e:
            print(f"⚠️  Could not load checkpoint: {e}")
        return None
    
    def save_checkpoint(self):
        """Save current progress to checkpoint file"""
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(self.progress, f)
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
    
    def mark_processed(self, page_id: str):
        """Mark a page as successfully processed"""
        self.progress['processed_pages'].add(page_id)
        if len(self.progress['processed_pages']) % 10 == 0:
            self.save_checkpoint()
    
    def mark_failed(self, page_id: str, error: str):
        """Mark a page as failed with error details"""
        self.progress['failed_pages'][page_id] = {
            'error': error,
            'timestamp': time.time()
        }
        self.save_checkpoint()
    
    def mark_skipped(self, page_id: str, reason: str):
        """Mark a page as skipped"""
        self.progress['skipped_pages'][page_id] = reason
    
    def should_skip(self, page_id: str) -> bool:
        """Check if a page was already processed"""
        return page_id in self.progress['processed_pages']
    
    def cleanup(self):
        """Remove checkpoint file after successful completion"""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                print("✅ Migration completed successfully, checkpoint removed")
        except Exception:
            pass  # Ignore cleanup errors


class WikiMigrator:
    """Main migration class"""

    def __init__(self, azure_client: AzureDevOpsWikiClient, mediawiki_client: MediaWikiClient):
        self.azure_client = azure_client
        self.mediawiki_client = mediawiki_client
        self.converter = ContentConverter()

    def migrate_wiki(self, wiki_name: Optional[str] = None) -> Tuple[int, int]:
        """Migrate a wiki from Azure DevOps to MediaWiki"""
        print("🔍 Getting available wikis...")
        wikis = self.azure_client.get_wikis()

        if not wikis:
            print("❌ No wikis found in the Azure DevOps project")
            return 0, 0

        # Select wiki
        if wiki_name:
            wiki = next((w for w in wikis if w['name'] == wiki_name), None)
            if not wiki:
                print(f"❌ Wiki '{wiki_name}' not found")
                available_wikis = [w['name'] for w in wikis]
                print(f"Available wikis: {', '.join(available_wikis)}")
                return 0, 0
        else:
            wiki = wikis[0]  # Use first wiki
            print(f"📖 Using wiki: {wiki['name']}")

        print(f"📄 Getting pages from wiki: {wiki['name']}")
        pages = self.azure_client.get_wiki_pages(wiki['id'])

        if not pages:
            print("❌ No pages found in the wiki")
            return 0, 0

        print(f"📝 Found {len(pages)} pages to migrate")

        success_count = 0
        failed_count = 0

        # Initialize progress tracking
        progress_tracker = ProgressTracker('.migration_progress.pkl')
        
        for i, page in enumerate(pages, 1):
            # Check if page was already processed
            if progress_tracker.should_skip(page['id']):
                print(f"ℹ️  Skipping already processed page: {page['path']}")
                success_count += 1
                continue
                
            try:
                print(f"🔄 Migrating ({i}/{len(pages)}): {page['path']}")

                # Get page content with error handling
                try:
                    content = self.azure_client.get_page_content(wiki['id'], page['id'])
                    if not content or not content.strip():
                        print(f"  ℹ️  Skipping empty page: {page['path']}")
                        progress_tracker.mark_skipped(page['id'], "Empty content")
                        continue
                except Exception as e:
                    error_msg = f"Failed to retrieve content: {e}"
                    print(f"  ❌ {error_msg}")
                    progress_tracker.mark_failed(page['id'], error_msg)
                    failed_count += 1
                    continue

                # Convert content with error handling
                try:
                    mediawiki_content = self.converter.markdown_to_mediawiki(content)
                except Exception as e:
                    error_msg = f"Content conversion failed: {e}"
                    print(f"  ⚠️  {error_msg}")
                    progress_tracker.mark_failed(page['id'], error_msg)
                    failed_count += 1
                    continue

                # Sanitize title
                try:
                    title = self.converter.sanitize_page_title(page['path'].lstrip('/'))
                    if not title or not title.strip():
                        title = f"Page_{page['id']}"
                        print(f"  ⚠️  Using fallback title: {title}")
                except Exception as e:
                    title = f"Page_{page['id']}"
                    print(f"  ⚠️  Title sanitization failed, using: {title}")

                # Create page in MediaWiki with retries
                try:
                    if self.mediawiki_client.create_page(title, mediawiki_content):
                        print(f"  ✅ Successfully migrated: {title}")
                        progress_tracker.mark_processed(page['id'])
                        success_count += 1
                    else:
                        error_msg = "Page creation failed"
                        print(f"  ❌ {error_msg}: {title}")
                        progress_tracker.mark_failed(page['id'], error_msg)
                        failed_count += 1
                        
                except Exception as e:
                    error_msg = f"Page creation error: {e}"
                    print(f"  ❌ {error_msg}")
                    progress_tracker.mark_failed(page['id'], error_msg)
                    failed_count += 1

            except KeyboardInterrupt:
                print("\n⚠️  Migration interrupted by user")
                print(f"📊 Progress saved. Resume later by running the same command.")
                progress_tracker.save_checkpoint()
                raise
                
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                print(f"  ❌ {error_msg}")
                progress_tracker.mark_failed(page['id'], error_msg)
                failed_count += 1
                
        # Clean up progress tracking on successful completion
        if failed_count == 0:
            progress_tracker.cleanup()

        return success_count, failed_count


def load_config():
    """Load configuration from .env file"""
    load_dotenv()

    # Azure DevOps configuration
    organization = os.getenv('AZURE_DEVOPS_ORGANIZATION')
    project = os.getenv('AZURE_DEVOPS_PROJECT')
    pat = os.getenv('AZURE_DEVOPS_PAT')
    wiki_name = os.getenv('AZURE_WIKI_NAME')

    # MediaWiki configuration
    wiki_url = os.getenv('WIKI_URL')
    username = os.getenv('WIKI_USERNAME')
    password = os.getenv('WIKI_PASSWORD')

    # Validate required fields
    required_fields = {
        'AZURE_DEVOPS_ORGANIZATION': organization,
        'AZURE_DEVOPS_PROJECT': project,
        'AZURE_DEVOPS_PAT': pat,
        'WIKI_URL': wiki_url,
        'WIKI_USERNAME': username,
        'WIKI_PASSWORD': password
    }

    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        print(f"❌ Missing required environment variables: {', '.join(missing_fields)}")
        print("Please copy .env.template to .env and configure all required values.")
        print("\n💡 Required environment variables:")
        for field in missing_fields:
            print(f"   - {field}")
        sys.exit(1)
    
    # At this point we know all required fields are not None or empty
    # Cast to str to satisfy type checker since we've validated they exist
    organization_str = str(organization)
    project_str = str(project)
    pat_str = str(pat)
    wiki_url_str = str(wiki_url)
    username_str = str(username)
    password_str = str(password)
    
    # Basic validation of values
    try:
        if not organization_str.replace('-', '').replace('_', '').replace('.', '').isalnum():
            print("⚠️  Azure DevOps organization name contains unusual characters")
        if not project_str.strip():
            print("❌ Azure DevOps project name cannot be empty")
            sys.exit(1)
        if len(pat_str) < 20:
            print("⚠️  Personal Access Token seems too short")
        if not wiki_url_str.startswith(('http://', 'https://')):
            print("❌ MediaWiki URL must start with http:// or https://")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️  Configuration validation warning: {e}")

    return organization_str, project_str, pat_str, wiki_url_str, username_str, password_str, wiki_name


def main():
    """Main function"""
    print("🚀 Azure DevOps to MediaWiki Migration Tool")
    print("=" * 50)

    try:
        # Load configuration
        organization, project, pat, wiki_url, username, password, wiki_name = load_config()

        # Initialize clients
        print("🔧 Initializing clients...")
        azure_client = AzureDevOpsWikiClient(organization, project, pat)
        mediawiki_client = MediaWikiClient(wiki_url, username, password)

        # Initialize migrator
        migrator = WikiMigrator(azure_client, mediawiki_client)

        # Run migration
        success_count, failed_count = migrator.migrate_wiki(wiki_name)

        # Summary
        print("\\n" + "=" * 50)
        print("🎉 Migration complete!")
        print(f"   ✅ Successfully migrated: {success_count} pages")
        if failed_count > 0:
            print(f"   ❌ Failed to migrate: {failed_count} pages")

        print(f"\\n🔗 Visit your MediaWiki at: {wiki_url}")
        print("✨ Your Azure DevOps wiki has been migrated!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
