# AgentARC Content Marketing Agent

OpenClaw-powered content marketing system for AgentARC.

## Quick Start

### Local Development
```bash
# 1. Install OpenClaw
npm install -g openclaw@latest

# 2. Set workspace
openclaw config set agents.defaults.workspace "$(pwd)"

# 3. Configure .env (see deploy/local-setup.md)

# 4. Start
openclaw gateway start
```

See **[deploy/local-setup.md](deploy/local-setup.md)** for detailed instructions.

### Production (GCP)
```bash
gcloud compute instances create openclaw-agent --machine-type=e2-medium ...
```

See **[deploy/gcp-setup.md](deploy/gcp-setup.md)** for full deployment guide.

---

## Workspace Structure

```
├── SOUL.md                 # Agent persona & behavior
├── BRAND_VOICE.md          # Voice & style guidelines
├── TOOLS.md                # API configurations
├── CALENDAR.md             # Editorial calendar
├── HEARTBEAT.md            # Proactive monitoring
│
├── config/
│   └── openclaw.json       # OpenClaw configuration
│
├── deploy/
│   ├── local-setup.md      # Local development guide
│   └── gcp-setup.md        # GCP deployment guide
│
├── knowledge/              # Product knowledge base
│   ├── product-overview.md
│   ├── features.md
│   ├── use-cases.md
│   ├── competitors.md
│   ├── faq.md
│   └── messaging.md
│
├── memory/                 # Agent memory
│   ├── memory.md           # Persistent learnings
│   └── content-performance.md
│
├── skills/                 # Custom skills
│   ├── content-machine/    # Full content pipeline
│   ├── seo-optimizer/      # SEO tools
│   ├── social-poster/      # Multi-platform posting
│   ├── wordpress-publisher/
│   ├── fact-checker/
│   ├── ai-trace-remover/
│   ├── voice-to-content/
│   ├── telegram-commands/
│   └── competitor-tracker/
│
└── workflows/              # Lobster pipelines
    ├── full-content-pipeline.lobster
    ├── quick-social.lobster
    ├── newsletter-weekly.lobster
    └── voice-to-publish.lobster
```

---

## Available Skills

| Skill | Commands | Description |
|-------|----------|-------------|
| **content-machine** | `/content research`, `/content write`, `/content repurpose` | Full-stack content pipeline |
| **seo-optimizer** | `/seo keywords`, `/seo optimize`, `/seo analyze` | SEO research & optimization |
| **social-poster** | `/post twitter`, `/post linkedin`, `/post all` | 6-platform posting via Genviral |
| **wordpress-publisher** | `/wp publish`, `/wp draft`, `/wp schedule` | Blog publishing |
| **fact-checker** | `/factcheck <content>` | Verify claims before publish |
| **ai-trace-remover** | `/humanize <content>` | Remove AI-detectable patterns |
| **voice-to-content** | `/voice blog`, `/voice social`, `/voice clips` | Audio → multi-format |
| **telegram-commands** | `/q`, `/idea`, `/status`, `/approve` | Mobile-optimized shortcuts |
| **competitor-tracker** | `/competitor scan`, `/competitor <name>` | Monitor competition |

---

## Telegram Commands (Quick Reference)

```
/q <topic>           Quick research (3-5 bullets)
/idea                Generate content idea
/draft blog <topic>  Start blog draft
/status              Pipeline status
/approve             Approve pending content
/reject              Reject pending content
[voice note]         Auto-transcribe & process
```

---

## Workflows

### full-content-pipeline.lobster
Complete pipeline: Research → Ideas → Write → Fact-check → SEO → Humanize → Repurpose → Approve → Publish

### quick-social.lobster
Fast social posting: Generate → Format per platform → Approve → Publish

### newsletter-weekly.lobster
Weekly newsletter: Gather updates → Compile → Generate subject lines → Approve → Send

### voice-to-publish.lobster
Voice note pipeline: Transcribe → Generate content → Fact-check → Humanize → Publish

---

## Environment Variables

**Required:**
- `TELEGRAM_BOT_TOKEN`
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- `BRAVE_API_KEY`

**Recommended:**
- `GENVIRAL_API_KEY`
- `WP_SITE_URL`, `WP_USERNAME`, `WP_APPLICATION_PASSWORD`
- `DEEPGRAM_API_KEY`

See [TOOLS.md](TOOLS.md) for full list.

---

## Key Files to Customize

1. **SOUL.md** - Agent persona (change for different products)
2. **BRAND_VOICE.md** - Voice guidelines (tone, banned words)
3. **knowledge/** - Product-specific information
4. **CALENDAR.md** - Your editorial schedule

---

## Swappable Components

| Component | Current | Alternatives |
|-----------|---------|--------------|
| LLM | Claude/GPT | DeepSeek, Gemini, local |
| Social | Genviral | Direct APIs, Post Bridge |
| Blog | WordPress | Ghost, Medium, Notion |
| Search | Brave | Perplexity, Gemini |
| Transcription | Deepgram | Whisper, AssemblyAI |

Change in `config/openclaw.json` - no code changes needed.

---

## Support

- **OpenClaw Docs:** https://docs.openclaw.ai
- **AgentARC Docs:** https://github.com/BuildBear/AgentARC
