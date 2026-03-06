# Heartbeat Tasks

Proactive monitoring and maintenance tasks. Run every 30 minutes during active hours.

**Notification Target:** Telegram (primary)

All alerts and reports are sent to Telegram. Critical alerts send push notifications.

## Content Monitoring

- [ ] Check for new AgentARC GitHub issues/discussions that could inspire content
- [ ] Monitor Twitter mentions of AgentARC, AI agent security, honeypot attacks
- [ ] Check if any scheduled posts failed to publish
- [ ] Review engagement on recent posts (flag high-performers for repurposing)

## Competitor & Industry Watch

- [ ] Scan for major AI agent security news
- [ ] Check competitor social accounts for new content
- [ ] Monitor blockchain security incident reports
- [ ] Flag trending topics in AI/crypto space

## Calendar & Deadlines

- [ ] Check CALENDAR.md for content due today or tomorrow
- [ ] Alert if any scheduled content is missing draft
- [ ] Remind about newsletter if it's Thursday (due Friday)

## Performance Tracking

- [ ] Log engagement metrics for posts older than 24 hours
- [ ] Flag underperforming content for analysis
- [ ] Note high-performing hooks/formats for reuse

## Memory Maintenance

- [ ] Update memory/content-performance.md with new metrics
- [ ] Add learnings to memory/memory.md if patterns emerge
- [ ] Clean up old research files (>30 days)

---

## Alert Thresholds

### Immediate Alert
- Security incident in AI agent space (content opportunity)
- AgentARC mentioned by major account
- Competitor major announcement
- Negative mention requiring response

### Daily Summary
- Engagement metrics summary
- Upcoming deadlines
- Content ideas from monitoring

### Weekly Report
- Full performance analysis
- Competitor activity summary
- Keyword ranking changes
- Content backlog status

---

## Active Hours

```yaml
activeHours:
  start: "08:00"
  end: "22:00"
  timezone: "America/New_York"
```

Outside active hours: Only alert on critical items (security incidents, viral mentions).

---

## Response Templates

### Positive Mention
"Thanks for the shoutout! [personalized response based on context]"

### Question About AgentARC
"Great question! [answer or link to docs]. Let us know if you need help getting started."

### Bug Report
"Thanks for reporting this. I've flagged it for the team. In the meantime, [workaround if available]."

### Feature Request
"Interesting idea! I've added it to our backlog. Would love to hear more about your use case."
