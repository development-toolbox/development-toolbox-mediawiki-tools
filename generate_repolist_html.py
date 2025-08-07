#!/usr/bin/env python3
"""
Generate a static HTML repository catalogue page by fetching from the GitHub API.
"""
import os
import json
from urllib.request import Request, urlopen

# Paths
output_dir = os.path.join('docs', 'site')
output_html = os.path.join(output_dir, 'repolist.html')
output_css = os.path.join(output_dir, 'styles.css')

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Fetch repository list from GitHub API directly using urllib
api_url = 'https://api.github.com/orgs/development-toolbox/repos?type=public&per_page=100'
req = Request(api_url, headers={'User-Agent': 'urllib'})
with urlopen(req) as response:
    # Load and override repository data
    raw_repos = json.load(response)
    # Manual overrides for technical descriptions
    overrides = {
        ".github": "Org-level configuration: workflows, issue templates, and Action setups.",
        "development-toolbox-compose-file-generator": "Generate docker-compose or podman-compose files from running containers.",
        "demo-container-deploy": "Deploy demo containers via scripted pipelines.",
        "rich-examples": "Collection of Python scripts demonstrating Rich library features.",
        "openstack-clouds-yaml-to-terraform-workspace-vars": "Convert OpenStack clouds.yaml auth details into Terraform workspace vars.",
        "development-toolbox-git-hooks-installer": "Install and manage Git hooks for automated commit docs.",
        "development-toolbox-demo-repo-branch-search": "Search code across branches in demo repositories.",
        "development-toolbox-smarttree": "CLI for visualizing directory trees with emoji, export, and filtering.",
        "development-toolbox-github-tutorials-agent": "Agent for automating GitHub tutorial generation.",
        "development-toolbox-mediawiki-tools": "Toolkit for MediaWiki migration, maintenance, sync, and automation.",
    }
    repos = []
    for repo in raw_repos:
        name = repo.get('name')
        # Apply override or fallback
        repo['description'] = overrides.get(name, repo.get('description') or 'No technical description available.')
        repos.append(repo)

# Write CSS
css_content = '''
body {
    font-family: sans-serif;
    padding: 2rem;
    background-color: #fafafa;
}
.repo-grid {
    display: grid;
    grid-gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}
.repo-card {
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: #fff;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.repo-card h2 {
    margin-top: 0;
    font-size: 1.25rem;
}
.repo-card p {
    margin-bottom: 0;
}
'''
with open(output_css, 'w', encoding='utf-8') as f:
    f.write(css_content)

# Write HTML
html_header = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Development Toolbox Repository Catalogue</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<h1>Development Toolbox Repository Catalogue</h1>
<div class="repo-grid">
'''
html_footer = '''
</div>
</body>
</html>
'''

# Build technical-focused cards with clone instructions
cards = []
for repo in repos:
    name = repo.get('name')
    desc = repo.get('description')
    cards.append(f"""
<div class="repo-card">
  <h2><a href="https://github.com/development-toolbox/{name}">{name}</a></h2>
  <p>{desc}</p>
  <pre><code>git clone https://github.com/development-toolbox/{name}.git</code></pre>
</div>
""")

with open(output_html, 'w', encoding='utf-8') as f:
    f.write(html_header + '\n'.join(cards) + html_footer)

print(f"Generated HTML catalogue: {output_html}")
