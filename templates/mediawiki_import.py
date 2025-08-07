#!/usr/bin/env python3
"""
MediaWiki Template Import Script
This script imports all your existing templates into MediaWiki
"""

import os
import sys
import json
import glob
import time
from pathlib import Path
from typing import Tuple, Optional

import requests
from dotenv import load_dotenv


class MediaWikiImporter:
    def __init__(self, wiki_url: str, username: str, password: str):
        self.wiki_url = wiki_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.api_url = f"{self.wiki_url}/api.php"

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
                    print(f"❌ API request timed out after {max_retries} attempts")
                    raise Exception("Request timeout - check network connectivity")
                print(f"⏳ Request timed out, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    print(f"❌ API connection failed: {e}")
                    print("💡 Check MediaWiki URL and network connectivity")
                    raise Exception(f"Connection failed: {e}")
                print(f"⚠️  Connection error, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    print("❌ Authentication failed - check username/password")
                    raise Exception("Authentication failed")
                elif e.response.status_code >= 500:
                    if attempt == max_retries - 1:
                        print(f"❌ Server error: {e.response.status_code}")
                        raise Exception(f"Server error: {e.response.status_code}")
                    print(f"⚠️  Server error, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)
                else:
                    print(f"❌ API request failed: {e}")
                    raise Exception(f"HTTP error: {e.response.status_code}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print("💡 MediaWiki might be returning HTML error page")
                raise Exception("Invalid JSON response")
                
        return {}

    def get_login_token(self) -> str:
        """Get login token from MediaWiki"""
        print("🔑 Getting login token...")

        response = self._make_request(
            action="query",
            meta="tokens",
            type="login",
            format="json"
        )

        token = response.get("query", {}).get("tokens", {}).get("logintoken")
        if not token:
            print("❌ Failed to get login token. Check your MediaWiki URL.")
            sys.exit(1)

        print("✅ Login token obtained")
        return token

    def login(self, login_token: str) -> bool:
        """Login to MediaWiki"""
        print(f"🔐 Logging in as {self.username}...")

        response = self._make_request(
            action="login",
            lgname=self.username,
            lgpassword=self.password,
            lgtoken=login_token,
            format="json"
        )

        login_result = response.get("login", {}).get("result")

        if login_result != "Success":
            print(f"❌ Login failed. Check your username and password.")
            print(f"Login result: {login_result}")
            return False

        print("✅ Successfully logged in")
        return True

    def get_edit_token(self) -> str:
        """Get edit token for making changes"""
        print("📝 Getting edit token...")

        response = self._make_request(
            action="query",
            meta="tokens",
            format="json"
        )

        token = response.get("query", {}).get("tokens", {}).get("csrftoken")
        if not token:
            print("❌ Failed to get edit token.")
            sys.exit(1)

        print("✅ Edit token obtained")
        return token

    def import_template(self, template_name: str, content: str, edit_token: str) -> bool:
        """Import a single template"""
        print(f"📄 Importing Template:{template_name}...")

        response = self._make_request(
            action="edit",
            title=f"Template:{template_name}",
            text=content,
            token=edit_token,
            format="json"
        )

        # Check for success
        edit_result = response.get("edit", {}).get("result")
        error_code = response.get("error", {}).get("code")

        if edit_result == "Success":
            print(f"  ✅ Template:{template_name} imported successfully")
            return True
        else:
            error_msg = error_code or response.get("error", {}).get("info") or "unknown error"
            print(f"  ❌ Failed to import Template:{template_name}")
            print(f"     Error: {error_msg}")
            return False

    def import_templates_from_directory(self, template_dir: str) -> Tuple[int, int]:
        """Import all templates from a directory"""
        print("📦 Importing templates...")

        template_path = Path(template_dir)
        if not template_path.exists():
            print(f"❌ Template directory not found: {template_dir}")
            sys.exit(1)

        # Find template files
        template_files = list(template_path.glob("*.mediawiki")) + list(template_path.glob("*.wiki"))

        if not template_files:
            print(f"❌ No template files found in {template_dir}")
            print("   Template files should have .mediawiki or .wiki extension")
            return 0, 0

        print(f"📄 Found {len(template_files)} template files")

        # Get tokens
        login_token = self.get_login_token()
        if not self.login(login_token):
            sys.exit(1)

        edit_token = self.get_edit_token()

        success_count = 0
        failed_count = 0

        for template_file in template_files:
            try:
                # Extract template name from filename
                template_name = template_file.stem
                if template_name.startswith("Template_"):
                    template_name = template_name[9:]  # Remove "Template_" prefix

                # Read template content
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Import template
                if self.import_template(template_name, content, edit_token):
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"❌ Error processing {template_file.name}: {e}")
                failed_count += 1

        return success_count, failed_count


def load_config() -> Tuple[str, str, str, str]:
    """Load configuration from .env file"""
    load_dotenv()

    wiki_url = os.getenv('WIKI_URL')
    username = os.getenv('WIKI_USERNAME')
    password = os.getenv('WIKI_PASSWORD')
    template_dir = os.getenv('TEMPLATE_DIR', 'internal-wiki/templates')

    # Validate required fields
    if not wiki_url or not username or not password:
        print("❌ Missing required environment variables.")
        print("Please copy .env.template to .env and configure:")
        print("  - WIKI_URL")
        print("  - WIKI_USERNAME")
        print("  - WIKI_PASSWORD")
        sys.exit(1)

    # Type checker now knows these are not None due to the check above
    return wiki_url, username, password, template_dir


def main():
    """Main function"""
    print("🎨 MediaWiki Template Import Tool")
    print("=" * 40)

    try:
        # Load configuration
        wiki_url, username, password, template_dir = load_config()

        # Initialize importer
        importer = MediaWikiImporter(wiki_url, username, password)

        # Import templates
        success_count, failed_count = importer.import_templates_from_directory(template_dir)

        # Summary
        print("\n" + "=" * 40)
        print("🎉 Import complete!")
        print(f"   ✅ Successfully imported: {success_count} templates")
        if failed_count > 0:
            print(f"   ❌ Failed to import: {failed_count} templates")

        print(f"\n🔗 Visit your MediaWiki at: {wiki_url}")
        print("✨ Your templates are now available!")

    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
