---
name: wordpress_publisher
description: Publish blog posts to WordPress with SEO optimization and scheduling
emoji: "📝"
requires:
  env:
    - WP_SITE_URL
    - WP_APPLICATION_PASSWORD
    - WP_USERNAME
user-invocable: true
---

# WordPress Publisher

Publish AgentARC content to WordPress blog with full SEO and formatting support.

## Setup

1. Create Application Password in WordPress:
   - Go to Users → Your Profile → Application Passwords
   - Create new password for "AgentARC Publisher"
   - Save to WP_APPLICATION_PASSWORD env var

2. Configure in TOOLS.md:
```yaml
wordpress:
  site_url: "https://blog.agentarc.dev"
  default_status: draft
  default_category: "Blog"
  default_author: 1
```

## Commands

### `/wp publish <content>`
Publish content to WordPress.

**Process:**
1. Parse content for title, body, excerpt
2. Run fact-checker skill
3. Run seo-optimizer skill
4. Format for WordPress (Gutenberg blocks)
5. Upload any images
6. Set categories and tags
7. Create post (draft by default)
8. Return preview URL for approval

**Content Format:**
```markdown
---
title: "Your Post Title"
excerpt: "Brief description for SEO"
category: "Tutorials"
tags: ["security", "python", "ai-agents"]
featured_image: "/path/to/image.png"
status: draft
---

# Post content here...
```

### `/wp draft <content>`
Create as draft (default behavior).

### `/wp schedule <content> <datetime>`
Schedule post for future publication.

**Format:** "YYYY-MM-DD HH:MM" or relative ("next Monday 9am")

### `/wp update <post-id> <content>`
Update existing post.

### `/wp list [status]`
List posts by status (draft, published, scheduled).

### `/wp categories`
List available categories.

### `/wp tags`
List/manage tags.

## Gutenberg Block Formatting

Automatically converts markdown to Gutenberg blocks:

| Markdown | Gutenberg Block |
|----------|-----------------|
| `# Heading` | Heading block |
| Paragraph | Paragraph block |
| `- List` | List block |
| ``` code ``` | Code block (with syntax highlighting) |
| `> Quote` | Quote block |
| `![Image](url)` | Image block |
| `---` | Separator block |

## SEO Integration

Before publishing, automatically:
1. Set SEO title (via Yoast/RankMath if installed)
2. Set meta description from excerpt
3. Set focus keyword
4. Check readability score
5. Add schema markup for articles

## Content Checklist

Before `/wp publish`:
- [ ] Title is compelling and keyword-optimized
- [ ] Excerpt is 150-160 characters
- [ ] Featured image is set
- [ ] Categories and tags are appropriate
- [ ] Internal links to other AgentARC content
- [ ] External links to authoritative sources
- [ ] CTA is clear (try AgentARC, star repo, etc.)
- [ ] Code examples are syntax-highlighted
- [ ] Fact-checked via fact-checker skill

## Post Templates

### Tutorial Post
```markdown
---
title: "How to [Action] with AgentARC"
category: "Tutorials"
tags: ["tutorial", "python", "getting-started"]
---

# How to [Action] with AgentARC

Brief intro (2-3 sentences).

## Prerequisites

- Python 3.10+
- AgentARC installed
- [Other requirements]

## Step 1: [First Step]

Explanation...

```python
# Code example
```

## Step 2: [Second Step]

...

## Conclusion

Summary and next steps.

**Ready to try it?** [pip install agentarc](link)
```

### Announcement Post
```markdown
---
title: "Announcing [Feature/Version]"
category: "Product Updates"
tags: ["announcement", "release"]
---

# Announcing [Feature/Version]

We're excited to announce...

## What's New

- Feature 1
- Feature 2

## Why This Matters

...

## Get Started

...
```

## Logging

All published posts logged to memory/content-performance.md:
```markdown
## 2026-03-05: [Post Title]
- URL: https://blog.agentarc.dev/post-slug
- Status: published
- Category: Tutorials
- Views: [tracked over time]
- Engagement: [comments, shares]
```
