# GitHub Pages Setup

This directory contains the GitHub Pages documentation site for the MediaWiki Migration Tools.

## 🌐 Live Site

The documentation is automatically deployed to GitHub Pages at:
**https://development-toolbox.github.io/development-toolbox-mediawiki-tools**

## 📁 Site Structure

```
docs/
├── index.html                          # Main documentation page
├── content-conversion-examples.md      # Conversion syntax reference
├── content_examples.md                 # Real-world migration examples
├── complete-migration-guide.md         # Step-by-step guide
└── README.md                          # This file

_config.yml                             # GitHub Pages configuration
```

## 🚀 Setting Up GitHub Pages

1. **Enable GitHub Pages** in your repository settings:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main`
   - Folder: `/ (root)`

2. **The site will be available at:**
   ```
   https://[username].github.io/[repository-name]
   ```

3. **Custom Domain (Optional):**
   - Add a `CNAME` file to the root directory
   - Configure DNS settings for your domain

## 📝 Content Updates

The site automatically rebuilds when you:
- Push changes to the `main` branch
- Update any files in the `docs/` directory
- Modify `_config.yml`

## 🛠️ Local Development

To test the site locally:

```bash
# Install Jekyll (if not already installed)
gem install bundler jekyll

# Serve the site locally
jekyll serve --source . --destination _site

# Or with live reload
jekyll serve --source . --destination _site --livereload
```

Access the local site at: `http://localhost:4000`

## 📋 Features

The documentation site includes:

- **📊 Tool Overview** - Complete description of all migration tools
- **🚀 Getting Started** - 6-phase migration process
- **📝 Examples** - Before/after conversion examples
- **🛠️ Troubleshooting** - Common issues and solutions
- **📱 Responsive Design** - Mobile-friendly interface
- **🔍 Syntax Highlighting** - Code examples with proper highlighting
- **🧭 Navigation** - Smooth scrolling and active section tracking

## 🎨 Customization

To customize the appearance:

1. **Colors**: Edit CSS variables in `docs/index.html` under `:root`
2. **Content**: Update sections directly in the HTML
3. **Navigation**: Modify the nav structure in the HTML
4. **Styling**: Add custom CSS in the `<style>` section

## 🔧 Configuration

Key settings in `_config.yml`:

- **title**: Site title shown in browser tabs
- **description**: Site description for SEO
- **url**: Your GitHub Pages URL
- **baseurl**: Repository name (for GitHub Pages)

## 📞 Support

If you encounter issues with GitHub Pages:

1. Check the **Actions** tab for build errors
2. Review the **Pages** settings in repository settings
3. Ensure all file paths are correct
4. Verify markdown syntax in documentation files

## 🚀 Deployment

The site deploys automatically via GitHub Actions when:
- Changes are pushed to the `main` branch
- Files in `docs/` are modified
- `_config.yml` is updated

Deployment typically takes 1-5 minutes to complete.
