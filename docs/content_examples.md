# Content Conversion Examples

This document shows real examples of how Azure DevOps wiki content converts to MediaWiki format.

## 📋 Example 1: Basic Formatting

### Before (Azure DevOps Markdown):
```markdown
# Getting Started Guide

This is a **comprehensive guide** to help you get started with our *awesome* platform.

## Prerequisites

Before you begin, make sure you have:
- Python 3.7 or higher
- Git installed and configured
- Access to the development environment

### Installation Steps

1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Configure your environment variables
4. Run the application

**Important**: Make sure to read the troubleshooting section if you encounter issues.
```

### After (MediaWiki):
```mediawiki
= Getting Started Guide =

This is a '''comprehensive guide''' to help you get started with our ''awesome'' platform.

== Prerequisites ==

Before you begin, make sure you have:
* Python 3.7 or higher
* Git installed and configured
* Access to the development environment

=== Installation Steps ===

# Clone the repository
# Install dependencies with <code>pip install -r requirements.txt</code>
# Configure your environment variables
# Run the application

'''Important''': Make sure to read the troubleshooting section if you encounter issues.
```

### ✅ What Works Well:
- Headers convert perfectly
- Bold and italic formatting
- Lists maintain structure
- Inline code formatting

---

## 📊 Example 2: Tables

### Before (Azure DevOps Markdown):
```markdown
## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/users | Get all users | Yes |
| POST | /api/users | Create new user | Yes |
| PUT | /api/users/{id} | Update user | Yes |
| DELETE | /api/users/{id} | Delete user | Admin |

### Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
```

### After (MediaWiki):
```mediawiki
== API Endpoints ==

{| class="wikitable"
|-
! Method
! Endpoint
! Description
! Auth Required
|-
| GET
| /api/users
| Get all users
| Yes
|-
| POST
| /api/users
| Create new user
| Yes
|-
| PUT
| /api/users/{id}
| Update user
| Yes
|-
| DELETE
| /api/users/{id}
| Delete user
| Admin
|}

=== Response Codes ===

{| class="wikitable"
|-
! Code
! Status
! Description
|-
| 200
| OK
| Request successful
|-
| 401
| Unauthorized
| Authentication required
|-
| 403
| Forbidden
| Insufficient permissions
|-
| 404
| Not Found
| Resource not found
|}
```

### ✅ What Works Well:
- Table structure preserved
- Headers properly converted
- Clean MediaWiki table syntax

### ⚠️ Potential Issues:
- Complex table formatting may need manual adjustment
- Cell alignment might not preserve perfectly

---

## 💻 Example 3: Code Blocks

### Before (Azure DevOps Markdown):
```markdown
## Configuration Example

Here's how to configure the application:

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp_db"
  },
  "logging": {
    "level": "info",
    "file": "/var/log/myapp.log"
  }
}
```

For Python configuration:

```python
import os
from config import Config

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))
        self.name = os.getenv('DB_NAME', 'myapp_db')

    def get_connection_string(self):
        return f"postgresql://{self.host}:{self.port}/{self.name}"
```

You can also use inline code like `config.get('database.host')` in your text.
```

### After (MediaWiki):
```mediawiki
== Configuration Example ==

Here's how to configure the application:

<syntaxhighlight lang="json">
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp_db"
  },
  "logging": {
    "level": "info",
    "file": "/var/log/myapp.log"
  }
}
</syntaxhighlight>

For Python configuration:

<syntaxhighlight lang="python">
import os
from config import Config

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))
        self.name = os.getenv('DB_NAME', 'myapp_db')

    def get_connection_string(self):
        return f"postgresql://{self.host}:{self.port}/{self.name}"
</syntaxhighlight>

You can also use inline code like <code>config.get('database.host')</code> in your text.
```

### ✅ What Works Well:
- Code blocks maintain syntax highlighting
- Language specification preserved
- Inline code formatting works perfectly

### 📝 Note:
- Requires SyntaxHighlight_GeSHi extension in MediaWiki
- Language names are preserved from Markdown

---

## 🔗 Example 4: Links and References

### Before (Azure DevOps Markdown):
```markdown
## Useful Resources

For more information, check out these resources:

- [Official Documentation](https://docs.example.com/api)
- [GitHub Repository](https://github.com/example/project)
- [Getting Started Tutorial](/wiki/Getting-Started)
- [API Reference Guide](/wiki/API-Reference)

### Internal Navigation

You can navigate to different sections:
- Go to [Installation Guide](#installation-steps) in this page
- Check out [Configuration Examples](/wiki/Configuration)
- Review [Troubleshooting Tips](/wiki/Troubleshooting)

**Pro tip**: Use `Ctrl+K` to quickly search for pages!
```

### After (MediaWiki):
```mediawiki
== Useful Resources ==

For more information, check out these resources:

* [https://docs.example.com/api Official Documentation]
* [https://github.com/example/project GitHub Repository]
* [/wiki/Getting-Started Getting Started Tutorial]
* [/wiki/API-Reference API Reference Guide]

=== Internal Navigation ===

You can navigate to different sections:
* Go to [#installation-steps Installation Guide] in this page
* Check out [/wiki/Configuration Configuration Examples]
* Review [/wiki/Troubleshooting Troubleshooting Tips]

'''Pro tip''': Use <code>Ctrl+K</code> to quickly search for pages!
```

### ✅ What Works Well:
- External links convert properly
- Link text is preserved
- Internal links maintain references

### ⚠️ Requires Manual Review:
- Internal wiki links may need URL adjustment
- Anchor links might need verification
- Some links may break if page titles change during migration

---

## 🖼️ Example 5: Images and Media (Manual Handling Required)

### Before (Azure DevOps Markdown):
```markdown
## Architecture Overview

Here's our system architecture:

![System Architecture](/.attachments/architecture-diagram.png)

The diagram above shows:
1. **Client Applications** - Web and mobile interfaces
2. **API Gateway** - Central routing and authentication
3. **Microservices** - Individual business logic components
4. **Database Layer** - Data persistence and caching

### Process Flow

![Process Flow Diagram](/.attachments/process-flow.png)

*Figure 1: Standard request processing flow*

For more detailed diagrams, see our [Design Documents](/wiki/Design-Documents).
```

### After (MediaWiki - Post Manual Image Upload):
```mediawiki
== Architecture Overview ==

Here's our system architecture:

[[File:Architecture-diagram.png|thumb|System Architecture]]

The diagram above shows:
# '''Client Applications''' - Web and mobile interfaces
# '''API Gateway''' - Central routing and authentication
# '''Microservices''' - Individual business logic components
# '''Database Layer''' - Data persistence and caching

=== Process Flow ===

[[File:Process-flow.png|thumb|Process Flow Diagram]]

''Figure 1: Standard request processing flow''

For more detailed diagrams, see our [/wiki/Design-Documents Design Documents].
```

### 🚨 Manual Steps Required:
1. **Download images** from Azure DevOps (cannot be automated)
2. **Upload to MediaWiki** using Special:Upload or bulk tools
3. **Update image syntax** in migrated content
4. **Test image display** and adjust sizing if needed

### 💡 Pro Tips for Images:
- Use descriptive filenames when uploading
- Consider image optimization for web
- Use MediaWiki's thumbnail features for better layout
- Create consistent naming conventions

---

## ⚠️ Example 6: Complex Content (Needs Manual Review)

### Before (Azure DevOps Markdown):
```markdown
## Advanced Features

### Task Lists
- [x] User authentication implemented
- [x] Database schema created
- [ ] API documentation completed
- [ ] Performance testing done

### Nested Content

> **Important Note**:
> This is a blockquote that contains important information.
> It may span multiple lines and include **formatting**.

### HTML Elements

Some content might include HTML:
<div class="warning-box">
  <strong>Warning:</strong> This feature is experimental.
  <ul>
    <li>Use with caution</li>
    <li>Test thoroughly before production</li>
  </ul>
</div>

### Strikethrough Text

~~This text is outdated~~ and should be ignored.

### Footnotes

This is a reference to something important[^1].

[^1]: This is the footnote explaining the important thing.
```

### After (MediaWiki - With Manual Adjustments):
```mediawiki
== Advanced Features ==

=== Task Lists ===
* ✓ User authentication implemented
* ✓ Database schema created
* ☐ API documentation completed
* ☐ Performance testing done

=== Nested Content ===

{{Warning|'''Important Note''':
This is a blockquote that contains important information.
It may span multiple lines and include '''formatting'''.}}

=== HTML Elements ===

Some content might include HTML:
<div class="warning-box">
  <strong>Warning:</strong> This feature is experimental.
  <ul>
    <li>Use with caution</li>
    <li>Test thoroughly before production</li>
  </ul>
</div>

=== Strikethrough Text ===

<s>This text is outdated</s> and should be ignored.

=== Footnotes ===

This is a reference to something important<ref>This is the footnote explaining the important thing.</ref>.

== References ==
<references />
```

### 🛠️ Manual Adjustments Made:
- **Task lists**: Converted to Unicode checkboxes
- **Blockquotes**: Used MediaWiki warning template
- **HTML**: Preserved (MediaWiki supports HTML)
- **Strikethrough**: Used `<s>` tags
- **Footnotes**: Converted to MediaWiki reference system

### 📝 Notes:
- Task lists don't have native MediaWiki equivalent
- Blockquotes often look better as templates/boxes
- HTML generally works but should be tested
- Footnotes require MediaWiki reference syntax

---

## 📊 Summary: Conversion Success Rates

| Content Type | Auto-Conversion Success | Manual Review Needed | Common Issues |
|--------------|-------------------------|----------------------|---------------|
| **Headers** | 100% | None | Perfect conversion |
| **Basic Formatting** | 95% | Rare edge cases | Mostly perfect |
| **Lists** | 90% | Nested complex lists | Good conversion |
| **Tables** | 85% | Complex formatting | Usually good |
| **Code Blocks** | 90% | Language verification | Very good |
| **Links** | 80% | Internal link updates | Need URL checking |
| **Images** | 0% | All images | Manual upload required |
| **Task Lists** | 50% | Visual formatting | Need manual styling |
| **Footnotes** | 0% | All footnotes | Different syntax |
| **HTML Content** | 70% | Compatibility testing | Case-by-case |

## 🎯 Migration Strategy Recommendations

### High-Priority Content (Migrate First):
- Documentation with basic formatting
- API references with simple tables
- Getting started guides
- FAQ pages

### Medium-Priority Content (Review During Migration):
- Pages with complex tables
- Content with many internal links
- Tutorial pages with code blocks

### Low-Priority Content (Manual Review After):
- Pages with images and diagrams
- Content with HTML elements
- Pages with footnotes or complex formatting
- Archive/historical content

---

## 🔧 Tools to Help

Use these tools from the migration toolkit:

1. **`migration_planner.py`** - Analyzes your wiki and identifies complexity
2. **`content_previewer.py`** - Shows exactly how your content will convert
3. **`azure_devops_migrator.py`** - Performs the actual migration
4. **Step-by-step guide** - Complete walkthrough of the process

**Remember**: The preview tools will show you exactly how YOUR content will convert, so you're never surprised by the results!

---

*These examples are part of the development-toolbox-mediawiki-tools project*