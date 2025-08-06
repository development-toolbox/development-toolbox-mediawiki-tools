# Content Conversion Examples

This document shows how different types of content are converted from Azure DevOps Markdown to MediaWiki syntax.

## 📝 Headers

### Azure DevOps (Markdown)
```markdown
# Main Title
## Section Title
### Subsection Title
#### Sub-subsection Title
##### Small Header
```

### MediaWiki (Converted)
```mediawiki
= Main Title =
== Section Title ==
=== Subsection Title ===
==== Sub-subsection Title ====
===== Small Header =====
```

---

## 🎨 Text Formatting

### Azure DevOps (Markdown)
```markdown
**Bold text**
*Italic text*
***Bold and italic***
__Also bold__
_Also italic_
`Inline code`
```

### MediaWiki (Converted)
```mediawiki
'''Bold text'''
''Italic text''
'''''Bold and italic'''''
'''Also bold'''
''Also italic''
<code>Inline code</code>
```

---

## 🔗 Links

### Azure DevOps (Markdown)
```markdown
[Link text](https://example.com)
[Internal link](/Documentation/Setup)
[Email link](mailto:user@example.com)
```

### MediaWiki (Converted)
```mediawiki
[https://example.com Link text]
[/Documentation/Setup Internal link]
[mailto:user@example.com Email link]
```

---

## 📋 Lists

### Azure DevOps (Markdown)
```markdown
- Unordered item 1
- Unordered item 2
  - Nested item
  - Another nested item

1. Ordered item 1
2. Ordered item 2
   1. Nested ordered item
   2. Another nested ordered item
```

### MediaWiki (Converted)
```mediawiki
* Unordered item 1
* Unordered item 2
** Nested item
** Another nested item

# Ordered item 1
# Ordered item 2
## Nested ordered item
## Another nested ordered item
```

---

## 💻 Code Blocks

### Azure DevOps (Markdown)
```markdown
```python
def hello_world():
    print("Hello, World!")
    return True
```
```

### MediaWiki (Converted)
```mediawiki
<syntaxhighlight lang="python">
def hello_world():
    print("Hello, World!")
    return True
</syntaxhighlight>
```

---

## 📊 Tables

### Azure DevOps (Markdown)
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1 Data | More data | Even more |
| Row 2 Data | Additional | Final cell |
```

### MediaWiki (Converted)
```mediawiki
{| class="wikitable"
|-
! Column 1
! Column 2
! Column 3
|-
| Row 1 Data
| More data
| Even more
|-
| Row 2 Data
| Additional
| Final cell
|}
```

---

## 🖼️ Images (Manual Handling Required)

### Azure DevOps (Markdown)
```markdown
![Alt text](/.attachments/image.png)
![Logo](https://example.com/logo.png "Title text")
```

### MediaWiki (Manual Process)
```mediawiki
<!-- 1. Download image from Azure DevOps -->
<!-- 2. Upload to MediaWiki via Special:Upload -->
<!-- 3. Replace with MediaWiki image syntax -->

[[File:Image.png|alt=Alt text]]
[[File:Logo.png|thumb|Title text]]
```

**Note**: Images require manual download and upload - they cannot be automatically migrated.

---

## ⚠️ Complex Conversions

### Task Lists (Converted to Regular Lists)

#### Azure DevOps (Markdown)
```markdown
- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task
```

#### MediaWiki (Converted)
```mediawiki
* ✓ Completed task
* ☐ Incomplete task
* ✓ Another completed task
```

### Strikethrough (May Need Manual Review)

#### Azure DevOps (Markdown)
```markdown
~~This text is crossed out~~
Regular text continues here.
```

#### MediaWiki (May Not Display Correctly)
```mediawiki
<s>This text is crossed out</s>
Regular text continues here.
```

---

## 🔧 Advanced Features

### Blockquotes

#### Azure DevOps (Markdown)
```markdown
> This is a blockquote
> It can span multiple lines
> And includes attribution
```

#### MediaWiki (Converted)
```mediawiki
<blockquote>
This is a blockquote
It can span multiple lines
And includes attribution
</blockquote>
```

### Horizontal Rules

#### Azure DevOps (Markdown)
```markdown
---
```

#### MediaWiki (Converted)
```mediawiki
----
```

---

## 🚨 Items Requiring Manual Attention

### 1. HTML Tags
Some HTML in Azure DevOps may not convert properly:

#### Azure DevOps
```html
<div class="highlight">
  <p>Special formatting</p>
</div>
```

#### Action Required
- Review each HTML section manually
- Convert to MediaWiki templates if needed
- Test formatting in MediaWiki

### 2. Complex Tables
Tables with merged cells or special formatting:

#### Azure DevOps
```markdown
| Header 1 | Header 2 |
|----------|----------|
| Normal cell | `code cell` |
| **Bold cell** | [Link cell](url) |
```

#### Action Required
- Verify table appearance in MediaWiki
- Adjust cell formatting manually if needed
- Consider MediaWiki table extensions for complex layouts

### 3. Footnotes
Azure DevOps footnotes need manual conversion:

#### Azure DevOps
```markdown
This text has a footnote[^1].

[^1]: This is the footnote text.
```

#### Manual Conversion Required
```mediawiki
This text has a footnote<ref>This is the footnote text.</ref>.

== References ==
<references />
```

---

## 📋 Conversion Quality Checklist

After migration, verify these elements:

### ✅ Basic Formatting
- [ ] Headers display with correct hierarchy
- [ ] Bold and italic text appears correctly
- [ ] Lists maintain proper nesting
- [ ] Links work and point to correct destinations

### ✅ Code and Technical Content
- [ ] Code blocks have syntax highlighting
- [ ] Inline code appears with monospace font
- [ ] Technical symbols and characters display correctly

### ✅ Tables and Structure
- [ ] Tables display with proper borders and alignment
- [ ] Table headers are clearly distinguished
- [ ] Complex tables maintain readability

### ✅ Media and Links
- [ ] All images have been uploaded and display correctly
- [ ] Internal links work within the wiki
- [ ] External links open to correct destinations

### ⚠️ Manual Review Needed
- [ ] HTML sections converted appropriately
- [ ] Special formatting preserved
- [ ] Custom styles or classes handled
- [ ] Interactive elements (if any) function properly

---

## 💡 Tips for Better Conversion

### Before Migration
1. **Simplify complex HTML** in Azure DevOps where possible
2. **Standardize image references** to make replacement easier
3. **Document custom formatting** that might need special handling

### During Migration
1. **Test with sample pages** before full migration
2. **Migrate in batches** to catch issues early
3. **Keep track of manual changes** needed for consistency

### After Migration
1. **Create MediaWiki templates** for commonly used formatting
2. **Train users** on MediaWiki syntax differences
3. **Set up style guidelines** for future content creation

---

## 🔗 Additional Resources

- **MediaWiki Syntax Reference**: https://www.mediawiki.org/wiki/Help:Formatting
- **Azure DevOps Markdown Reference**: https://docs.microsoft.com/en-us/azure/devops/project/wiki/markdown-guidance
- **MediaWiki Table Help**: https://www.mediawiki.org/wiki/Help:Tables
- **Syntax Highlighting Extensions**: https://www.mediawiki.org/wiki/Extension:SyntaxHighlight

---

*This guide is part of the development-toolbox-mediawiki-tools project*
