# Tools Configuration

API keys and tool configurations for AgentARC content marketing.

## Telegram (Primary Interface)

Telegram is the primary control interface for the GCP-deployed agent.

### Setup Steps

1. **Create bot with @BotFather:**
   ```
   /newbot
   Name: AgentARC Content Bot
   Username: agentarc_content_bot
   ```
   Save the token.

2. **Get your Telegram user ID:**
   - Message @userinfobot on Telegram
   - Copy your numeric ID

3. **Configure:**
   ```yaml
   telegram:
     token: "${TELEGRAM_BOT_TOKEN}"
     dmPolicy: pairing  # Requires approval for new users
     allowedUsers:
       - "YOUR_TELEGRAM_ID"  # Add your ID here
     notifications:
       contentPublished: true
       approvalNeeded: true
       competitorAlert: true
       errors: true
   ```

**Required env vars:**
- `TELEGRAM_BOT_TOKEN`

### Quick Commands via Telegram
- `/q <topic>` - Quick research
- `/idea` - Generate content idea
- `/draft <type> <topic>` - Start draft
- `/status` - Pipeline status
- `/approve` / `/reject` - Content approval
- Send voice note - Auto-transcribe and process

---

## Web Research

```yaml
web_search:
  provider: brave  # Options: brave, perplexity, gemini
  # BRAVE_API_KEY required in environment

web_fetch:
  fallback: firecrawl
  # FIRECRAWL_API_KEY for JS-heavy sites
```

## Content Publishing

### WordPress (AgentARC Blog)
```yaml
wordpress:
  site_url: "https://blog.agentarc.dev"  # Update with actual URL
  default_status: draft
  default_category: "Blog"
  default_author: 1
```

**Required env vars:**
- `WP_SITE_URL`
- `WP_USERNAME`
- `WP_APPLICATION_PASSWORD`

### Newsletter
```yaml
newsletter:
  provider: convertkit  # Options: convertkit, beehiiv, substack
```

**Required env vars:**
- `CONVERTKIT_API_KEY` (or provider-specific key)

## Social Media

### Genviral (Multi-Platform)
```yaml
genviral:
  enabled: true
  platforms:
    - twitter
    - linkedin
    - instagram
    - tiktok
    - youtube
    - threads
```

**Required env vars:**
- `GENVIRAL_API_KEY`

### Direct Platform Keys (Fallback)
If not using Genviral:
- `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`
- `LINKEDIN_ACCESS_TOKEN`
- `META_ACCESS_TOKEN` (Instagram)
- `YOUTUBE_API_KEY`

## SEO Tools

```yaml
seo:
  keyword_research: semrush  # Options: semrush, ahrefs
  serp_tracking: serpapi
```

**Required env vars:**
- `SEMRUSH_API_KEY`
- `SERPAPI_KEY`

## AI & Content Processing

```yaml
ai:
  # For LLM-based content analysis
  model: openai  # or anthropic

transcription:
  provider: deepgram
```

**Required env vars:**
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `DEEPGRAM_API_KEY`

## AI Detection

```yaml
ai_detection:
  checker: originality  # For checking AI patterns
```

**Required env vars:**
- `ORIGINALITY_API_KEY`

## Analytics

```yaml
analytics:
  google:
    property_id: "GA_PROPERTY_ID"
```

**Required env vars:**
- `GA_PROPERTY_ID`
- `GA_CREDENTIALS_JSON`

---

## Environment Variables Checklist

```bash
# === REQUIRED ===

# Telegram (Primary Interface)
TELEGRAM_BOT_TOKEN=

# Web Research
BRAVE_API_KEY=

# LLM (at least one)
OPENAI_API_KEY=
# or
ANTHROPIC_API_KEY=

# === RECOMMENDED ===

# Social Publishing
GENVIRAL_API_KEY=

# WordPress
WP_SITE_URL=
WP_USERNAME=
WP_APPLICATION_PASSWORD=

# Voice Transcription
DEEPGRAM_API_KEY=

# === OPTIONAL ===

# SEO
SEMRUSH_API_KEY=
SERPAPI_KEY=

# AI Detection
ORIGINALITY_API_KEY=

# Newsletter
CONVERTKIT_API_KEY=

# Advanced Web Scraping
FIRECRAWL_API_KEY=

# Analytics
GA_PROPERTY_ID=
GA_CREDENTIALS_JSON=
```

## MCP Servers (Optional)

For additional integrations via Model Context Protocol:

```json
{
  "mcp": {
    "servers": {
      "notion": {
        "command": "npx",
        "args": ["@notionhq/mcp-server"],
        "env": {
          "NOTION_API_KEY": "..."
        }
      },
      "github": {
        "command": "npx",
        "args": ["@anthropic/mcp-github"],
        "env": {
          "GITHUB_TOKEN": "..."
        }
      }
    }
  }
}
```
