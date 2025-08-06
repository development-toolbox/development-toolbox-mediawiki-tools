#!/usr/bin/env python3
"""
Azure DevOps to MediaWiki Migration Script
This script migrates wiki pages from Azure DevOps to MediaWiki
"""

import os
import sys
import json
import re
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from dotenv import load_dotenv


class AzureDevOpsWikiClient:
    """Client for Azure DevOps Wiki REST API"""

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
            'Content-Type': 'application/json'
        })

    def get_wikis(self) -> List[Dict]:
        """Get all wikis in the project"""
        url = f"{self.base_url}/wiki/wikis?api-version=7.0"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('value', [])

    def get_wiki_pages(self, wiki_id: str) -> List[Dict]:
        """Get all pages in a wiki"""
        url = f"{self.base_url}/wiki/wikis/{wiki_id}/pages?api-version=7.0&recursionLevel=full"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('value', [])

    def get_page_content(self, wiki_id: str, page_id: str) -> str:
        """Get the content of a specific page"""
        url = f"{self.base_url}/wiki/wikis/{wiki_id}/pages/{page_id}?api-version=7.0&includeContent=true"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('content', '')


class MediaWikiClient:
    """Client for MediaWiki API"""

    def __init__(self, wiki_url: str, username: str, password: str):
        self.wiki_url = wiki_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.api_url = f"{self.wiki_url}/api.php"
        self._logged_in = False

    def _make_request(self, method: str = "POST", **params) -> dict:
        """Make a request to the MediaWiki API"""
        try:
            if method.upper() == "GET":
                response = self.session.get(self.api_url, params=params)
            else:
                response = self.session.post(self.api_url, data=params)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ MediaWiki API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response from MediaWiki: {e}")
            raise

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
        content = re.sub(r'^# (.+)$', r'= \\1 =', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'== \\1 ==', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'=== \\1 ===', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.+)$', r'==== \\1 ====', content, flags=re.MULTILINE)
        content = re.sub(r'^##### (.+)$', r'===== \\1 =====', content, flags=re.MULTILINE)

        # Bold and italic
        content = re.sub(r'\\*\\*(.+?)\\*\\*', r"'''\\1'''", content)
        content = re.sub(r'\\*(.+?)\\*', r"''\\1''", content)
        content = re.sub(r'__(.+?)__', r"'''\\1'''", content)
        content = re.sub(r'_(.+?)_', r"''\\1''", content)

        # Links
        content = re.sub(r'\\[(.+?)\\]\\((.+?)\\)', r'[\\2 \\1]', content)

        # Code blocks
        content = re.sub(r'```(\\w+)?\\n(.*?)\\n```', r'<syntaxhighlight lang="\\1">\\n\\2\\n</syntaxhighlight>', content, flags=re.DOTALL)
        content = re.sub(r'`(.+?)`', r'<code>\\1</code>', content)

        # Lists
        content = re.sub(r'^(\\s*)- (.+)$', r'\\1* \\2', content, flags=re.MULTILINE)
        content = re.sub(r'^(\\s*)\\d+\\. (.+)$', r'\\1# \\2', content, flags=re.MULTILINE)

        return content

    @staticmethod
    def sanitize_page_title(title: str) -> str:
        """Sanitize page title for MediaWiki"""
        # Remove .md extension
        title = re.sub(r'\\.md$', '', title)

        # Replace underscores and hyphens with spaces
        title = title.replace('_', ' ').replace('-', ' ')

        # Capitalize first letter of each word
        title = ' '.join(word.capitalize() for word in title.split())

        return title


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

        for page in pages:
            try:
                print(f"🔄 Migrating: {page['path']}")

                # Get page content
                content = self.azure_client.get_page_content(wiki['id'], page['id'])

                # Convert content
                mediawiki_content = self.converter.markdown_to_mediawiki(content)

                # Sanitize title
                title = self.converter.sanitize_page_title(page['path'].lstrip('/'))

                # Create page in MediaWiki
                if self.mediawiki_client.create_page(title, mediawiki_content):
                    print(f"  ✅ Successfully migrated: {title}")
                    success_count += 1
                else:
                    print(f"  ❌ Failed to migrate: {title}")
                    failed_count += 1

            except Exception as e:
                print(f"  ❌ Error migrating {page['path']}: {e}")
                failed_count += 1

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
        sys.exit(1)

    return organization, project, pat, wiki_url, username, password, wiki_name


def main():
    """Main function"""
    print("🚀 Azure DevOps to MediaWiki Migration Tool")
    print("=" * 50)

    try:
        # Load configuration
        organization, project, pat, wiki_url, username, password, wiki_name = load_config()

        # Initialize clients
        print("🔧 Initializing clients...")
        azure_client = AzureDevOpsWikiClient(organization, project, pat)  # type: ignore
        mediawiki_client = MediaWikiClient(wiki_url, username, password)  # type: ignore

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
