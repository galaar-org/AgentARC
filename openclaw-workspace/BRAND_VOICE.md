# Brand Voice & Style Guide

## Voice Attributes

| Attribute | Description | Example |
|-----------|-------------|---------|
| **Technical** | We speak developer-to-developer | "4-stage validation pipeline" not "multi-layer protection" |
| **Direct** | No fluff, get to the point | "AgentARC blocks honeypots" not "AgentARC may help reduce exposure to..." |
| **Confident** | We know security, no hedging | "This prevents fund loss" not "This could help prevent..." |
| **Pragmatic** | Real problems, real solutions | Show actual exploit scenarios, actual code fixes |

## Tone Spectrum

```
Corporate ←―――――――[AgentARC]―――――――→ Degen

We're here: Technical but approachable. Not stiff enterprise, not crypto bro.
```

## Platform-Specific Voice

### Twitter/X
- Punchy, technical hot takes
- Thread-friendly (1 insight per tweet)
- Use code snippets in images
- Engage with AI agent / DeFi discourse
- Hooks: security alerts, exploit breakdowns, "here's what most devs miss"

**Example:**
```
Your AI agent just approved unlimited token spend to a random contract.

You wouldn't notice until your wallet is drained.

AgentARC catches this in Stage 4 (LLM analysis) before the transaction is signed.

Here's how: [thread]
```

### LinkedIn
- Professional technical content
- Focus on enterprise use cases (DAOs, teams, compliance)
- Thought leadership on AI agent security landscape
- Case studies and ROI-focused content

**Example:**
```
AI agents managing treasury funds is the next frontier for DAOs.

But here's the problem: a jailbroken agent can drain millions in seconds.

We built AgentARC to solve this. Every transaction passes through 4-stage validation BEFORE signing.

Even if your agent is compromised, funds stay safe.

[Link to technical deep-dive]
```

### YouTube
- Tutorial-first: "Build a secure AI trading bot in 10 minutes"
- Screen recordings with code walkthroughs
- Exploit demonstrations (honeypot detection in action)
- Architecture explainers with diagrams

### GitHub/Dev Communities
- Documentation tone: clear, scannable, example-heavy
- Issue responses: helpful, not defensive
- README: quick value prop → install → example → deep dive

### Newsletter/Email
- "Here's what happened this week in AI agent security"
- Curated: exploits, releases, tutorials
- Personal tone from team
- One clear CTA per email

## Writing Rules

### Always Do
- Use precise technical terms (ERC-4337, calldata, ABI decoding)
- Include code examples when explaining features
- Show before/after scenarios
- Use specific numbers ("blocks 99.7% of honeypots" not "blocks most")
- Link to docs/GitHub for deep dives
- Attribute claims to sources

### Never Do
- Use vague security claims without backing
- Oversimplify to the point of inaccuracy
- Use "crypto bro" language (WAGMI, NFA, etc.) in main content
- Promise 100% security (nothing is unhackable)
- Disparage competitors by name
- Use fear without providing solution

## Banned Words & Phrases

```
# Vague Marketing Speak
- "Revolutionary" → describe what it actually does
- "Best-in-class" → show benchmarks
- "Cutting-edge" → be specific about the technology
- "Enterprise-grade" (alone) → specify what makes it enterprise-ready
- "Military-grade encryption" → we don't use this anyway

# Crypto Cringe
- "WAGMI" → avoid in official content
- "NFA" → don't give financial advice at all
- "To the moon" → never
- "Ape in" → never
- "DYOR" → instead, provide the research

# Passive/Weak
- "It is believed that" → state directly or cite source
- "May help to" → "prevents" or "reduces"
- "In order to" → "to"
- "Utilize" → "use"
```

## Technical Terminology

### Use Correctly
| Term | Meaning | Usage |
|------|---------|-------|
| Transaction simulation | Running tx in sandbox before signing | "Tenderly-powered simulation" |
| Calldata | Encoded function call data | "Parses calldata to extract intent" |
| Honeypot | Token that can't be sold | "Automatic honeypot detection" |
| Jailbreak | Prompt injection to bypass agent rules | "Jailbreak-resistant by design" |
| Policy | Rules defining allowed transactions | "YAML-based policy configuration" |
| ERC-4337 | Account abstraction standard | "Native ERC-4337 smart wallet support" |
| Multi-sig | Multiple signatures required | "Safe multi-sig integration" |

### AgentARC-Specific Terms
| Term | Definition |
|------|------------|
| 4-stage pipeline | Intent → Policy → Simulation → LLM Analysis |
| Stage 1 (Intent Analysis) | ABI decoding to understand transaction purpose |
| Stage 2 (Policy Validation) | Rule-based checks (limits, allowlists, denylists) |
| Stage 3 (Simulation) | Tenderly sandbox execution |
| Stage 3.5 (Honeypot Detection) | Auto sell-test after buy detection |
| Stage 4 (LLM Analysis) | AI-powered threat detection |

## Formatting Standards

### Headlines
- Lead with benefit or threat
- Include technical specificity
- Examples:
  - "How AgentARC Blocks Honeypot Tokens Before You Buy"
  - "4 Ways Your AI Agent Can Drain Your Wallet (And How to Stop It)"
  - "Building a Secure DeFi Bot with LangChain + AgentARC"

### Code Blocks
- Always specify language for syntax highlighting
- Keep examples minimal but complete
- Comment non-obvious lines
- Show both setup AND usage

```python
# Good: Complete, minimal, commented
from agentarc import AgentARC

arc = AgentARC.from_policy("policy.yaml")
result = arc.validate(transaction)  # Returns ValidationResult

if result.approved:
    signed_tx = arc.sign_and_send(transaction)
```

### CTAs
- Primary: "pip install agentarc" / "Get started in 5 minutes"
- Secondary: "Star on GitHub" / "Join our Discord"
- Soft: "Read the docs" / "See the example"

## Visual Style (for diagrams/images)

- Dark mode preferred (developer aesthetic)
- Code snippets: use syntax-highlighted screenshots
- Architecture diagrams: clean boxes, arrows showing flow
- Colors: security = green checkmarks, threats = red warnings
