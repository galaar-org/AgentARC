---
name: fact_checker
description: Verify claims, statistics, and technical accuracy in content before publishing
emoji: "✅"
requires:
  env:
    - BRAVE_API_KEY
user-invocable: true
---

# Fact Checker

Verify all claims in AgentARC content before publishing. Critical for maintaining technical credibility.

## Commands

### `/factcheck <content>`
Full fact-check of content.

**Process:**
1. Extract all factual claims from content
2. Categorize claims:
   - Product claims (verify against knowledge/)
   - Technical claims (verify against docs/codebase)
   - Statistics (verify source)
   - Quotes (verify attribution)
   - External claims (web search verification)
3. Flag issues with severity (critical, warning, suggestion)
4. Provide corrections or sources

**Output:**
```
FACT CHECK REPORT
=================

✅ VERIFIED (12 claims)
- "4-stage validation pipeline" - Confirmed in knowledge/features.md
- "MIT licensed" - Confirmed in pyproject.toml

⚠️ NEEDS SOURCE (2 claims)
- "blocks 99% of honeypots" - No source found. Suggest removing or adding "in testing"
- "247K GitHub stars" - Outdated, current count is [X]

❌ INCORRECT (1 claim)
- "Works with Python 3.9" - INCORRECT. Only 3.10+ supported per docs
  Correction: "Works with Python 3.10+"

📝 SUGGESTIONS
- Add source for Tenderly integration claim
- Link to documentation for technical claims
```

### `/factcheck product <content>`
Check product-specific claims only.

**Verifies against:**
- knowledge/product-overview.md
- knowledge/features.md
- knowledge/faq.md
- AgentARC README and docs

**Common issues:**
- Feature claims not in current version
- Incorrect syntax in code examples
- Outdated pricing/stats
- Missing wallet types or frameworks

### `/factcheck code <code-block>`
Verify code examples work.

**Process:**
1. Check syntax validity
2. Verify imports exist in AgentARC
3. Check API matches current version
4. Verify configuration options are valid
5. Flag deprecated methods

### `/factcheck stats <content>`
Verify statistics and numbers.

**Process:**
1. Extract all numbers/percentages
2. Search for original sources
3. Check if stats are current
4. Verify context is accurate

### `/factcheck quote <quote> <attribution>`
Verify quote attribution.

**Process:**
1. Search for exact quote
2. Verify speaker/source
3. Check context
4. Provide original source link

## AgentARC-Specific Checks

### Product Claims Checklist
- [ ] Features exist in current version (0.3.0)
- [ ] Wallet types listed correctly (EOA, ERC-4337, Safe, CDP)
- [ ] Frameworks listed correctly (OpenAI, LangChain, AgentKit)
- [ ] Blockchain support accurate (Ethereum, Base, Arbitrum, Optimism)
- [ ] Python version requirements correct (3.10+)
- [ ] Installation commands accurate
- [ ] Pricing claims accurate (MIT free, LLM ~$0.003/tx)

### Technical Claims Checklist
- [ ] Pipeline stages described correctly
- [ ] Policy options match documentation
- [ ] Code examples use correct API
- [ ] Security claims are defensible
- [ ] Performance claims have basis

### External Claims Checklist
- [ ] Competitor comparisons are fair
- [ ] Industry statistics have sources
- [ ] Ecosystem claims are current
- [ ] Regulatory/compliance claims are accurate

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| CRITICAL | Factually wrong, could damage credibility | Must fix before publish |
| WARNING | Unverified or potentially outdated | Should verify or remove |
| SUGGESTION | Could be stronger with source | Nice to have |

## Integration

Before any content goes to social-poster or wordpress-publisher:
1. Run `/factcheck <content>`
2. Address all CRITICAL issues
3. Review WARNING issues
4. Document any accepted risks

Log fact-check results to memory/fact-checks.md for audit trail.
