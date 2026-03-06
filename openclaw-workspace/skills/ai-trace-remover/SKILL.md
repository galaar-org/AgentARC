---
name: ai_trace_remover
description: Remove AI-detectable patterns from content while preserving quality and voice
emoji: "🔍"
user-invocable: true
---

# AI Trace Remover

Transform AI-generated content to be indistinguishable from human-written content while maintaining quality and brand voice.

## Why This Matters

AI detectors look for patterns:
- Predictable sentence structures
- Overuse of certain phrases
- Lack of personal voice/opinion
- Perfect grammar (too perfect)
- Generic transitions
- Hedging language

Human content has:
- Varied sentence lengths
- Personal asides
- Occasional informal phrasing
- Strong opinions
- Specific examples
- Natural flow

## Commands

### `/humanize <content>`
Full humanization pass on content.

**Process:**
1. Analyze for AI patterns
2. Vary sentence structure
3. Add voice and personality
4. Insert specific examples
5. Remove hedge words
6. Add natural transitions
7. Maintain BRAND_VOICE.md compliance
8. Verify technical accuracy preserved

**Before:**
```
It is important to note that AI agents can be vulnerable to various attack vectors.
In order to mitigate these risks, developers should implement proper security measures.
Transaction validation is one approach that can help prevent unauthorized actions.
```

**After:**
```
Here's the thing most developers miss: your AI agent is one prompt injection away from
draining the wallet. I've seen it happen. The fix? Validate every transaction before
signing. Not after. Before. AgentARC does exactly this—four validation stages,
all running before the private key ever touches the transaction.
```

### `/humanize light <content>`
Light touch—fix obvious AI patterns only.

**Targets:**
- "It is important to note"
- "In order to"
- "One approach that can"
- "It should be noted"
- "This serves to"

### `/humanize aggressive <content>`
Heavy rewrite—maximum humanization.

**Process:**
- Rewrite most sentences
- Add personal anecdotes/opinions
- Insert colloquialisms
- Break grammar rules intentionally
- Add rhetorical questions

### `/detect <content>`
Check content for AI patterns without changing it.

**Output:**
```
AI DETECTION ANALYSIS
=====================

Risk Score: 7/10 (High)

Patterns Found:
- Sentence structure repetition (lines 3, 7, 12)
- Hedge phrases: "may help", "could potentially" (5 instances)
- Generic transitions: "Furthermore", "Additionally" (4 instances)
- Lack of specific examples
- No personal voice markers

Recommendations:
1. Vary paragraph lengths
2. Add specific code examples
3. Include personal opinion/stance
4. Replace formal transitions
5. Add rhetorical question in intro
```

## Pattern Replacements

### Hedge Words (Remove or Strengthen)
| AI Pattern | Human Alternative |
|------------|-------------------|
| "may help to" | "fixes" or remove |
| "could potentially" | "will" or "can" |
| "it is possible that" | State directly |
| "tends to be" | "is" |
| "in some cases" | Be specific or remove |

### Formal Transitions (Naturalize)
| AI Pattern | Human Alternative |
|------------|-------------------|
| "Furthermore" | "And here's the thing" |
| "Additionally" | "Plus" or just continue |
| "In conclusion" | "Bottom line" |
| "It is worth noting" | "Worth noting:" or remove |
| "As mentioned previously" | Reference directly |

### Structure Patterns (Vary)
| AI Pattern | Human Alternative |
|------------|-------------------|
| Same sentence length | Mix short. Then longer ones that build. |
| [Topic]. [Explanation]. [Example]. | Vary the order, skip some |
| Bullet points only | Mix bullets with narrative |
| Perfect paragraphs | Occasional one-sentence paragraphs. For impact. |

## Voice Injection

Add personality markers from BRAND_VOICE.md:
- Direct statements ("This is the answer")
- Questions to reader ("Sound familiar?")
- Personal experience ("I've seen this happen")
- Strong opinions ("Most solutions miss this")
- Specific examples (real code, real numbers)

## Technical Content Rules

When humanizing technical content:
1. Keep technical accuracy 100%
2. Don't simplify code examples
3. Preserve all facts and figures
4. Only modify the prose around technical elements
5. Add developer-relatable comments

## Quality Check

After humanization, verify:
- [ ] Technical accuracy preserved
- [ ] Brand voice maintained
- [ ] All facts still correct
- [ ] Code examples unchanged
- [ ] CTAs still clear
- [ ] Flow is natural

## Integration

Run before:
- social-poster (all platforms)
- wordpress-publisher
- newsletter publishing

Run after:
- content-machine writing
- content repurposing
