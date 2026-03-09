---
name: export_to_telegram
description: Export social media posts as document files to Telegram (no Genviral needed)
emoji: "📄"
requires:
  env:
    - TELEGRAM_BOT_TOKEN
user-invocable: true
---

# Export to Telegram

Generate platform-formatted posts and send as document files to Telegram for manual posting.

**No API keys required** - just copy/paste from the doc.

## Commands

### `/export twitter <topic>`
Generate Twitter thread and send as `.txt` file.

**Output includes:**
- Formatted thread (numbered tweets)
- Character counts per tweet
- Suggested hashtags
- Best posting times

**Example:**
```
/export twitter AI agent security best practices
```

**Sends file:** `twitter_thread_2026-03-09.txt`

---

### `/export linkedin <topic>`
Generate LinkedIn post and send as `.txt` file.

**Output includes:**
- Hook (first 2 lines)
- Full post body
- Engagement question
- Suggested hashtags

**Example:**
```
/export linkedin Why every AI agent needs a security layer
```

**Sends file:** `linkedin_post_2026-03-09.txt`

---

### `/export instagram <topic>`
Generate Instagram carousel content and send as `.txt` file.

**Output includes:**
- Slide-by-slide content (10 slides)
- Caption with hooks
- Hashtag set (15 hashtags)
- Alt text for each slide

**Example:**
```
/export instagram 5 ways AI agents get exploited
```

**Sends file:** `instagram_carousel_2026-03-09.txt`

---

### `/export threads <topic>`
Generate Threads post and send as `.txt` file.

**Example:**
```
/export threads Hot take on agent wallets
```

**Sends file:** `threads_post_2026-03-09.txt`

---

### `/export all <topic>`
Generate posts for ALL platforms in one document.

**Output:** Single file with sections for each platform.

**Example:**
```
/export all AgentARC honeypot detection feature
```

**Sends file:** `social_posts_2026-03-09.txt`

**File structure:**
```
=====================================
TWITTER THREAD
=====================================
1/ [Hook tweet]
2/ [Context]
...

=====================================
LINKEDIN POST
=====================================
[Full LinkedIn post]

=====================================
INSTAGRAM CAROUSEL
=====================================
Slide 1: [content]
...
Caption: [caption]
Hashtags: [hashtags]

=====================================
THREADS POST
=====================================
[Threads content]
```

---

### `/export tiktok <topic>`
Generate TikTok script and send as `.txt` file.

**Output includes:**
- 30-60 second script
- Timestamps
- Visual/action cues
- Hook and CTA

**Example:**
```
/export tiktok Your AI agent just got drained
```

**Sends file:** `tiktok_script_2026-03-09.txt`

---

### `/export youtube <topic>`
Generate YouTube Shorts script and send as `.txt` file.

**Example:**
```
/export youtube Quick demo of transaction simulation
```

**Sends file:** `youtube_short_2026-03-09.txt`

---

## Workflow

1. **You:** `/export all [topic]`
2. **Bot:** Generates content, sends `.txt` file to Telegram
3. **You:** Download file, copy/paste to each platform
4. **You:** Post manually (full control over timing)

## File Formats

All exports are plain `.txt` files that work on any device:
- Easy to copy/paste on mobile
- No special apps needed
- Edit in any text editor
- Save for later use

## Tips

- Use `/export all` to batch-generate everything at once
- Files are saved with date stamps for easy organization
- Content follows BRAND_VOICE.md guidelines automatically
- Each platform section is clearly separated

## No API Keys Needed

This skill only requires `TELEGRAM_BOT_TOKEN` - the same token you already have for the bot interface. No Genviral, no social media APIs.
