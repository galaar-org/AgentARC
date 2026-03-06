---
name: competitor_tracker
description: Monitor competitor content, features, and market positioning
emoji: "👁️"
requires:
  env:
    - BRAVE_API_KEY
user-invocable: true
---

# Competitor Tracker

Monitor the AI agent security and blockchain agent landscape to inform content strategy.

## Competitor Categories

### Direct Competitors
Tools specifically for AI agent transaction security:
- DIY validation implementations
- Other open-source security layers
- Enterprise custody with agent features

### Adjacent Players
- Fireblocks (institutional custody)
- Safe{Wallet} (multi-sig)
- Blowfish (consumer wallet protection)
- OpenZeppelin Defender (contract security)
- Forta (threat detection network)

### Ecosystem Players
- LangChain (we integrate with)
- AgentKit (we integrate with)
- OpenAI (function calling)
- Tenderly (we use for simulation)

## Commands

### `/competitor scan`
Run full competitor landscape scan.

**Process:**
1. Search for competitor news/updates
2. Check GitHub for new releases
3. Scan social media for announcements
4. Check job postings (signals priorities)
5. Review any new content

**Output:**
```
COMPETITOR SCAN: 2026-03-05
===========================

DIRECT COMPETITORS:
- [Competitor A]: Released v2.0 with multi-chain support
  → Opportunity: We support more chains, create comparison content

ADJACENT PLAYERS:
- Fireblocks: Announced AI agent features (enterprise only)
  → Opportunity: Position AgentARC as accessible alternative

ECOSYSTEM:
- LangChain: New security best practices guide
  → Action: Ensure AgentARC is mentioned, contribute if possible

CONTENT OPPORTUNITIES:
1. "AgentARC vs Enterprise Custody Solutions"
2. "Why Open Source Security Matters for AI Agents"
3. "Multi-Chain Agent Security Comparison"
```

### `/competitor <name>`
Deep dive on specific competitor.

**Output:**
- Product overview
- Recent updates
- Pricing model
- Target audience
- Strengths vs AgentARC
- Weaknesses vs AgentARC
- Content they're publishing
- Keywords they're targeting

### `/competitor content <name>`
Analyze competitor's content strategy.

**Output:**
- Content types (blog, social, video)
- Publishing frequency
- Top performing content
- Keywords targeted
- Gaps we can fill

### `/competitor features <name>`
Feature comparison.

**Output:**
| Feature | AgentARC | Competitor |
|---------|----------|------------|
| Honeypot detection | ✅ Automatic | ❌ No |
| Multi-wallet | ✅ 4 types | ⚠️ 2 types |
| ... | ... | ... |

### `/competitor news [timeframe]`
Recent news about competitors.

**Default:** Last 7 days
**Options:** today, week, month

### `/competitor keywords`
Keywords competitors are ranking for that we're not.

**Output:**
- Keyword
- Competitor ranking
- Our current position
- Content opportunity

## Automated Monitoring

Set up in HEARTBEAT.md:
```markdown
- Weekly competitor scan (Mondays)
- Alert on major competitor announcements
- Track competitor GitHub releases
- Monitor competitor social engagement
```

## Content Opportunities

### Comparison Content
When competitor releases feature:
1. Analyze their implementation
2. Compare to AgentARC approach
3. Create fair comparison content
4. Focus on our unique advantages

### Gap Content
When competitor is weak:
1. Identify their limitation
2. Create content showcasing our strength
3. Target their dissatisfied users

### Response Content
When competitor makes claims:
1. Fact-check their claims
2. If misleading, create counter-content
3. If valid, acknowledge and differentiate

## Tracking Database

Log to memory/competitors.md:
```markdown
## [Competitor Name]

### Updates
- 2026-03-05: Released v2.0
- 2026-02-20: Raised Series A

### Content
- Blog frequency: 2x/week
- Social: Active on Twitter, LinkedIn
- Top content: "How to secure your AI agent"

### Our Response
- Created comparison post: [link]
- Targeted their keywords: [list]
```

## Ethics Guidelines

1. **Never disparage** competitors directly by name in public content
2. **Use facts** only—no speculation or FUD
3. **Focus on our strengths** rather than their weaknesses
4. **Acknowledge** when competitors do something well
5. **Compete on product** and content quality, not negativity
