#!/usr/bin/env python3
"""
Check Repositories Script

This script fetches and lists public and private repositories from the
'development-toolbox' GitHub organization.

To access private repositories, this script will automatically try to use credentials
from the GitHub CLI ('gh') if you are logged in. As a fallback, it will use
a GitHub Personal Access Token (PAT) with 'repo' scope if provided via the
GITHUB_TOKEN environment variable.
"""
import os
import requests
import subprocess

def fetch_repos(repo_type, token=None):
    """
    Fetches repositories of a specific type (public or private) from the GitHub API.
    """
    url = f"https://api.github.com/orgs/development-toolbox/repos?type={repo_type}"
    headers = {}
    if token:
        headers['Authorization'] = f"token {token}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        repos_data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching {repo_type} repositories: {e}")
        return None
    except ValueError:
        print("Error parsing JSON response.")
        return None

    if not isinstance(repos_data, list):
        print(f"Unexpected API response format for {repo_type} repos: {repos_data.get('message', 'No message')}")
        return []

    repos = [
        {
            'name': repo.get('name'),
            'description': repo.get('description') or "No description available."
        }
        for repo in repos_data if repo.get('name')
    ]
    return repos

def print_repos(title, repos):
    """Prints a formatted list of repositories."""
    print("-" * 40)
    print(title)
    print("-" * 40)
    if not repos:
        print("No repositories found.")
    else:
        for repo in repos:
            print(f"- {repo['name']}: {repo['description']}")
    print("\n")

def get_gh_auth_token():
    """
    Retrieves the GitHub authentication token from the 'gh' CLI tool.
    """
    try:
        # Check if gh is installed and the user is logged in
        result = subprocess.run(
            ['gh', 'auth', 'token'],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        # gh CLI not installed, not logged in, or other error
        print(f"Could not get auth token from 'gh' CLI: {e}")
        return None

if __name__ == "__main__":
    # Prioritize gh CLI token, fall back to environment variable
    github_token = get_gh_auth_token() or os.getenv('GITHUB_TOKEN')

    # Fetch and print public repositories
    public_repos = fetch_repos('public')
    if public_repos is not None:
        print_repos("✅ Public Repositories", public_repos)

    # Fetch and print private repositories if a token is provided
    if github_token:
        private_repos = fetch_repos('private', token=github_token)
        if private_repos is not None:
            print_repos("🔒 Private Repositories (Visible with Token)", private_repos)
    else:
        print("-" * 40)
        print("ℹ️  Private Repositories")
        print("-" * 40)
        print("Set the GITHUB_TOKEN environment variable to view private repositories.")
        print("See script comments for details on creating a token.")
