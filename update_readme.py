#!/usr/bin/env python3
"""Update README Script
This script fetches repository names and descriptions from the development-toolbox GitHub org page
and updates the README.md file with this information.
"""
import requests
from bs4 import BeautifulSoup
import re
import os

import base64
import time

def get_repo_readme_summary(repo_name, token=None):
    """
    Fetches the README of a repository and returns the first paragraph as a summary.
    """
    url = f"https://api.github.com/repos/development-toolbox/{repo_name}/readme"
    headers = {}
    if token:
        headers['Authorization'] = f"token {token}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return "No README found for this repository."
        response.raise_for_status()
        readme_data = response.json()

        readme_content = base64.b64decode(readme_data['content']).decode('utf-8')

        # Find the first meaningful paragraph
        paragraphs = readme_content.split('\n\n')
        summary = ""
        for p in paragraphs:
            # Clean and skip code blocks, badges, and simple lists
            p_clean = p.strip()
            if not p_clean or p_clean.startswith('#'):
                continue
            # Skip paragraphs that are code fences, badges, or list items
            if p_clean.startswith('```') or p_clean.startswith('![') or p_clean.startswith('- ') or p_clean.startswith('* '):
                continue
            # Use only sufficiently long paragraphs
            if len(p_clean.split()) <= 5:
                continue
            summary = p_clean.replace('\n', ' ')
            break

        return summary if summary else "Could not extract a summary from the README."

    except requests.RequestException as e:
        print(f"Error fetching README for {repo_name}: {e}")
        return "Could not fetch README."
    except (KeyError, TypeError):
        return "Invalid README data received."

def fetch_repos_from_api(token=None):
    """
    Fetches repository names and descriptions from the development-toolbox GitHub organization API.
    """
    url = "https://api.github.com/orgs/development-toolbox/repos?type=public"
    headers = {}
    if token:
        headers['Authorization'] = f"token {token}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        repos_data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except ValueError:
        print("Error parsing JSON response.")
        return None

    repos = []
    for repo in repos_data:
        repo_name = repo.get('name')
        if repo_name and repo_name != '.github':
            print(f"Analyzing repo: {repo_name}...")
            summary = get_repo_readme_summary(repo_name, token)
            repos.append({
                'name': repo_name,
                'description': summary
            })
            time.sleep(1) # Avoid hitting rate limits

    return repos


def update_readme(repos):
    """
    Updates the README.md file with the list of repositories.
    """
    if not repos:
        print("No repositories found. README will not be updated.")
        return

    readme_path = 'README.md'
    if not os.path.exists(readme_path):
        print(f"Error: {readme_path} not found.")
        return

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate YAML list for embedding
    yaml_lines = ["repos:"]
    for repo in repos:
        yaml_lines.append(f"  - name: {repo['name']}")
        # Escape double quotes
        desc = repo['description'].replace('"', '\\"')
        yaml_lines.append(f"    description: \"{desc}\"")
    repo_yaml = "\n".join(yaml_lines)

    # Use regex to replace content between placeholders
    pattern = re.compile(r"(<!-- REPO_LIST_START -->)(.*)(<!-- REPO_LIST_END -->)", re.DOTALL)

    # Replace between placeholders preserving markers
    # Replace placeholder with generated YAML block
    new_content = pattern.sub(f"\\1\n{repo_yaml}\n\\3", content)

    if new_content == content:
        print("No new repository information found. README.md is already up to date.")
        return

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("README.md has been successfully updated.")

if __name__ == "__main__":
    repositories = fetch_repos_from_api()
    if repositories:
        update_readme(repositories)

