---
name: seo_optimizer
description: Optimize content for search engines with keyword research and on-page SEO
emoji: "📈"
requires:
  env:
    - BRAVE_API_KEY
user-invocable: true
---

# SEO Optimizer

Optimize AgentARC content for search engine visibility and organic traffic.

## Commands

### `/seo keywords <topic>`
Research keywords for a topic.

**Process:**
1. Search for topic + related terms
2. Analyze top-ranking content
3. Identify primary, secondary, and long-tail keywords
4. Check search intent (informational, transactional, navigational)
5. Estimate difficulty based on competition

**Output:**
```
Primary Keywords:
- "ai agent security" (high volume, medium difficulty)
- "blockchain agent protection" (medium volume, low difficulty)

Secondary Keywords:
- "transaction validation ai"
- "honeypot detection crypto"

Long-Tail Keywords:
- "how to secure ai trading bot"
- "prevent jailbreak attack crypto agent"
- "agentarc tutorial python"
```

### `/seo analyze <url-or-content>`
Analyze content for SEO issues.

**Checks:**
- Title tag (length, keyword presence)
- Meta description (length, CTA, keyword)
- H1, H2, H3 structure
- Keyword density and placement
- Internal/external link opportunities
- Image alt text
- Content length vs competitors
- Readability score

**Output:** Scorecard with specific fixes.

### `/seo optimize <content>`
Rewrite content with SEO improvements.

**Process:**
1. Identify target keyword
2. Analyze current optimization level
3. Suggest/apply improvements:
   - Title optimization
   - Header restructuring
   - Keyword insertion (natural)
   - Add FAQ schema opportunities
   - Internal link suggestions to other AgentARC content
4. Preserve brand voice (check BRAND_VOICE.md)

**Output:** Optimized version with changelog.

### `/seo competitors <keyword>`
Analyze competitor content for a keyword.

**Process:**
1. Search keyword
2. Analyze top 5-10 results
3. Extract:
   - Content length
   - Structure patterns
   - Keywords used
   - Content gaps
   - Backlink opportunities

**Output:** Competitor analysis with actionable insights.

### `/seo brief <keyword>`
Generate content brief for SEO-optimized article.

**Output includes:**
- Target keyword and variants
- Search intent analysis
- Recommended length
- Required sections (based on competitors)
- Questions to answer (People Also Ask)
- Internal links to include
- External authority sources

## AgentARC-Specific Keywords

### Primary Terms
- ai agent security
- blockchain agent protection
- transaction validation ai
- crypto agent security
- defi bot security

### Product Terms
- agentarc
- agentarc python
- agentarc tutorial
- agentarc vs [competitor]

### Problem Terms
- ai agent jailbreak
- honeypot token detection
- crypto agent hack
- ai wallet security
- prevent defi exploit

### Long-Tail Opportunities
- how to secure langchain blockchain agent
- erc-4337 security best practices
- ai trading bot security python
- prevent prompt injection crypto agent

## Integration Notes

- Always check knowledge/messaging.md for approved keywords
- Use BRAND_VOICE.md to maintain tone while optimizing
- Log successful keywords to memory/content-performance.md
- Track rankings over time in memory/seo-rankings.md
