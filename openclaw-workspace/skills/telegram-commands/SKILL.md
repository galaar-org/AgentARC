---
name: telegram_commands
description: Quick commands optimized for Telegram mobile interface
emoji: "📱"
user-invocable: true
---

# Telegram Commands

Quick commands designed for mobile-first interaction via Telegram.

## Content Commands

### `/q <topic>`
Quick research on a topic (abbreviated for mobile).

**Example:**
```
/q honeypot tokens 2026
```
Returns: 3-5 bullet summary with sources.

### `/idea`
Generate one content idea based on recent trends.

**Example:**
```
/idea
```
Returns: Single content idea with title, angle, and platforms.

### `/draft <type> <topic>`
Start a draft (saves to workspace, notifies when ready for review).

**Types:** `blog`, `thread`, `post`

**Example:**
```
/draft thread AI agent jailbreak prevention
```
Returns: "Draft started. I'll notify you when ready for review."

### `/publish <platform>`
Publish last approved content to platform.

**Example:**
```
/publish twitter
```

### `/status`
Current content pipeline status.

Returns:
```
📊 Content Status

Drafts pending review: 2
Scheduled posts: 5
Published today: 3

Next deadline: Blog post (Tomorrow 9am)
```

## Quick Actions

### `/approve`
Approve the last item waiting for approval.

### `/reject [reason]`
Reject with optional reason.

### `/pause`
Pause all scheduled posts.

### `/resume`
Resume scheduled posts.

## Voice Notes

Send any voice note → automatically processed:

1. Transcribed
2. You're asked: "Blog, Thread, or Notes?"
3. Tap to select
4. Content generated
5. Tap to approve & publish

## Alerts You'll Receive

### Content Alerts
```
📝 Draft Ready for Review

"5 Ways AI Agents Get Hacked"
Type: Blog post
Words: 1,847

[Review] [Approve] [Reject]
```

### Performance Alerts
```
🔥 High Performer Alert

Your thread on honeypot detection is trending:
- 15K impressions
- 342 engagements
- 89 link clicks

[Repurpose] [Boost] [Dismiss]
```

### Competitor Alerts
```
👁️ Competitor Alert

[Competitor] just announced multi-chain support.

[Create Response] [View Details] [Dismiss]
```

### Deadline Reminders
```
⏰ Content Deadline

Newsletter due in 4 hours.
Status: Draft incomplete

[Complete Now] [Extend] [Skip This Week]
```

## Settings

### `/notify on|off`
Toggle notifications.

### `/quiet <hours>`
Mute for specified hours.

### `/schedule`
View upcoming scheduled content.

### `/metrics [period]`
Quick performance summary.

**Example:**
```
/metrics week
```

## Mobile Optimizations

- All responses formatted for small screens
- Inline buttons for quick actions
- Voice note support for hands-free
- Abbreviated commands (`/q` instead of `/research`)
- Push notifications for approvals needed

## Conversation Mode

Just chat naturally:

```
You: What should I post about today?
Bot: Based on trends and your calendar, I suggest:
     "Thread on the new Ethereum agent exploit from yesterday"
     [Create Thread] [Different Idea]

You: Create it
Bot: [Generates thread, shows preview]
     Ready to post?
     [Post Now] [Edit] [Schedule]
```
