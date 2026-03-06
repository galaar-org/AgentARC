---
name: social_poster
description: Post content to Twitter, LinkedIn, Instagram, TikTok, YouTube, and Threads via Genviral
emoji: "📱"
requires:
  env:
    - GENVIRAL_API_KEY
user-invocable: true
---

# Social Poster

Post AgentARC content across 6 platforms using Genviral's 42 APIs.

## Supported Platforms

| Platform | Content Types | Best For |
|----------|---------------|----------|
| Twitter/X | Threads, single tweets, images | Tech discussions, announcements |
| LinkedIn | Long posts, articles, carousels | B2B, professional audience |
| Instagram | Carousels, Reels, Stories | Visual content, tutorials |
| TikTok | Short videos, trending formats | Viral potential, younger devs |
| YouTube | Shorts, full videos | Tutorials, deep dives |
| Threads | Text posts, threads | Casual tech talk |

## Commands

### `/post twitter <content>`
Post to Twitter/X.

**Process:**
1. Check content length (280 chars for single, thread for longer)
2. Load BRAND_VOICE.md Twitter guidelines
3. Format for Twitter (line breaks, no markdown)
4. Add relevant hashtags (max 2-3)
5. Post via Genviral API
6. Log to memory/content-performance.md

**Thread Format:**
```
1/ Hook tweet (strongest statement)

2/ Context/problem

3/ Solution (AgentARC)

4/ How it works

5/ Code example or visual

6/ CTA (try it, star repo)
```

### `/post linkedin <content>`
Post to LinkedIn.

**Process:**
1. Format for LinkedIn (line breaks, professional tone)
2. Add hook in first 2 lines (before "see more")
3. Include relevant emojis sparingly
4. End with engagement question
5. Post via Genviral API
6. Log performance

**Format:**
```
[Hook - make them click "see more"]

[Problem statement]

[Solution - AgentARC]

[Key benefits - bullet points]

[Personal insight or story]

[CTA + question for engagement]
```

### `/post instagram <carousel-content>`
Post Instagram carousel.

**Process:**
1. Parse content into 8-10 slides
2. Generate slide descriptions for design
3. Create alt text for each slide
4. Write caption with hooks
5. Add hashtags (10-15, mix of sizes)
6. Post via Genviral API

**Carousel Structure:**
```
Slide 1: Hook/Title
Slide 2: Problem
Slide 3-7: Solution points
Slide 8: Summary
Slide 9: CTA
Slide 10: Follow prompt
```

### `/post tiktok <script>`
Post TikTok video script.

**Process:**
1. Format as 30-60 second script
2. Include hook in first 3 seconds
3. Add visual/action cues
4. End with CTA
5. Log script for video production

**Script Format:**
```
[0-3s] HOOK: "Your AI agent just got hacked..."

[3-15s] PROBLEM: Show the vulnerability

[15-45s] SOLUTION: AgentARC demo

[45-60s] CTA: "Link in bio to try it"
```

### `/post youtube <type> <content>`
Post YouTube content.

**Types:** short (60s), video (script for longer)

**Shorts Process:**
1. Format as vertical video script
2. Hook in first second
3. Fast-paced information
4. End screen CTA

### `/post threads <content>`
Post to Threads.

**Process:**
1. Format for Threads (casual, conversational)
2. Can be longer than Twitter
3. Less hashtag-focused
4. Post via Genviral API

### `/post all <content>`
Post to all platforms with platform-specific formatting.

**Process:**
1. Take source content
2. Adapt for each platform per BRAND_VOICE.md
3. Queue all posts
4. Get human approval for batch
5. Post to all platforms
6. Log all to memory/content-performance.md

## Scheduling

### `/post schedule <platform> <content> <datetime>`
Schedule post for future.

**Format:** datetime as "YYYY-MM-DD HH:MM" or relative ("tomorrow 9am")

### `/post queue`
Show scheduled posts.

### `/post cancel <post-id>`
Cancel scheduled post.

## Analytics

### `/post analytics <platform> [timeframe]`
Get performance metrics.

**Metrics tracked:**
- Impressions
- Engagement rate
- Clicks
- Shares/Retweets
- Comments
- Follower growth

## Best Practices

### Timing (EST)
- Twitter: 9am, 12pm, 5pm
- LinkedIn: 8am, 12pm, 5pm (Tue-Thu best)
- Instagram: 11am, 1pm, 7pm
- TikTok: 7pm, 9pm
- YouTube: 2pm, 4pm

### Hashtags
**Twitter:** #AIAgents #Web3Security #DeFi (max 3)
**LinkedIn:** #ArtificialIntelligence #BlockchainSecurity #DeFi (max 5)
**Instagram:** Mix of sizes, 10-15 total

### Content Mix
- 40% Educational (tutorials, how-tos)
- 30% Engagement (questions, polls, discussions)
- 20% Product (features, updates, announcements)
- 10% Community (reposts, user content, memes)
