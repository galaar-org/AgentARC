# Local Development Setup

Run the OpenClaw content marketing agent locally on your Mac.

## Prerequisites

- macOS (tested on macOS 13+)
- Node.js 22+
- Telegram account (for bot interface)
- API keys (see TOOLS.md)

## Step 1: Install Node.js

```bash
# Using Homebrew (recommended)
brew install node@22

# Or using nvm
nvm install 22
nvm use 22

# Verify
node --version  # Should be 22.x
```

## Step 2: Install OpenClaw

```bash
# Install globally
npm install -g openclaw@latest

# Verify installation
openclaw --version

# Run doctor to check system
openclaw doctor
```

## Step 3: Setup Workspace

```bash
# Set workspace path in your shell profile
echo 'export OPENCLAW_WORKSPACE="[your path to agentarc]/AgentARC/openclaw-workspace"' >> ~/.zshrc
source ~/.zshrc

# Or configure directly
openclaw config set agents.defaults.workspace "[your path to agentarc]/AgentARC/openclaw-workspace"
```

## Step 4: Configure Environment Variables

Create `.env` file in workspace:

```bash
cat > [your path to agentarc]/AgentARC/openclaw-workspace/.env << 'EOF'
# === REQUIRED ===

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# LLM Provider (at least one)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Web Research
BRAVE_API_KEY=your_key_here

# === RECOMMENDED ===

# Social Media Publishing
GENVIRAL_API_KEY=your_key_here

# WordPress
WP_SITE_URL=https://blog.agentarc.dev
WP_USERNAME=your_username
WP_APPLICATION_PASSWORD=your_app_password

# Voice Transcription
DEEPGRAM_API_KEY=your_key_here

# === OPTIONAL ===

# SEO Tools
SEMRUSH_API_KEY=
SERPAPI_KEY=

# AI Detection
ORIGINALITY_API_KEY=

# Newsletter
CONVERTKIT_API_KEY=

# Analytics
GA_PROPERTY_ID=
EOF
```

Load environment variables:

```bash
# Add to ~/.zshrc for persistence
echo 'source [[your path to agentarc]]AgentARC/openclaw-workspace/.env' >> ~/.zshrc
source ~/.zshrc

# Or use direnv (recommended)
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
cd [your path to agentarc]/AgentARC/openclaw-workspace
mv .env .envrc
direnv allow
```

## Step 5: Create Telegram Bot

1. **Open Telegram** and search for `@BotFather`

2. **Create new bot:**
   ```
   /newbot
   ```
   - Name: `AgentARC Content Bot`
   - Username: `agentarc_content_bot` (must be unique)

3. **Save the token** - looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

4. **Get your Telegram user ID:**
   - Message `@userinfobot` on Telegram
   - Copy your numeric ID (e.g., `123456789`)

5. **Update config:**
   ```bash
   # Edit openclaw.json
   nano /Users/arjun/BuildBear/AgentARC/openclaw-workspace/config/openclaw.json

   # Add your Telegram ID to allowedUsers array:
   # "allowedUsers": ["YOUR_TELEGRAM_ID"]
   ```

## Step 6: Run OpenClaw

### Option A: Interactive Mode (Development)

```bash
# Start gateway in foreground
cd /Users/arjun/BuildBear/AgentARC/openclaw-workspace
openclaw gateway start

# In another terminal, test with CLI
openclaw agent --message "Hello, test connection"
```

### Option B: Background Daemon (Recommended)

```bash
# Install and start daemon
openclaw onboard --install-daemon

# Or manually start daemon
openclaw gateway start --daemon

# Check status
openclaw gateway status

# View logs
openclaw gateway logs -f
```

### Option C: Using launchd (Auto-start on boot)

```bash
# Create launch agent
cat > ~/Library/LaunchAgents/com.openclaw.agent.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/openclaw</string>
        <string>gateway</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/arjun/BuildBear/AgentARC/openclaw-workspace</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/arjun/BuildBear/AgentARC/openclaw-workspace/logs/openclaw.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/arjun/BuildBear/AgentARC/openclaw-workspace/logs/openclaw-error.log</string>
</dict>
</plist>
EOF

# Create logs directory
mkdir -p /Users/arjun/BuildBear/AgentARC/openclaw-workspace/logs

# Load the agent
launchctl load ~/Library/LaunchAgents/com.openclaw.agent.plist

# Check if running
launchctl list | grep openclaw

# To stop
launchctl unload ~/Library/LaunchAgents/com.openclaw.agent.plist
```

## Step 7: Connect Telegram

1. **Start the gateway** (if not already running)

2. **Open Telegram** and message your bot

3. **Send `/start`** - bot will respond with pairing instructions

4. **Complete pairing** - either:
   - Enter pairing code shown in terminal, OR
   - Bot auto-approves if your ID is in `allowedUsers`

5. **Test connection:**
   ```
   /status
   /q AI agent security
   ```

## Step 8: Setup Cron Jobs (Optional)

```bash
# Morning research (8 AM)
openclaw cron add \
  --name "morning-research" \
  --cron "0 8 * * *" \
  --message "Research trending AI agent security topics"

# Competitor scan (Mondays 9 AM)
openclaw cron add \
  --name "competitor-scan" \
  --cron "0 9 * * 1" \
  --message "Run weekly competitor scan and summarize"

# Newsletter prep (Thursdays 10 AM)
openclaw cron add \
  --name "newsletter-prep" \
  --cron "0 10 * * 4" \
  --message "Prepare weekly newsletter draft"

# List all cron jobs
openclaw cron list

# Remove a job
openclaw cron remove morning-research
```

## Step 9: Test Skills

### Via Terminal
```bash
# Quick research
openclaw agent --message "/q honeypot detection 2026"

# Generate content idea
openclaw agent --message "/idea"

# Check status
openclaw agent --message "/status"
```

### Via Telegram
```
/q honeypot detection
/idea
/status
[Send voice note] → auto-processes
```

## Directory Structure After Setup

```
/Users/arjun/BuildBear/AgentARC/openclaw-workspace/
├── .env (or .envrc)          # Environment variables
├── config/
│   └── openclaw.json         # OpenClaw configuration
├── logs/                     # Log files (if using launchd)
│   ├── openclaw.log
│   └── openclaw-error.log
├── memory/                   # Agent memory (auto-updated)
├── skills/                   # Custom skills
├── workflows/                # Lobster pipelines
└── knowledge/                # Product knowledge base
```

## Common Commands

```bash
# Gateway management
openclaw gateway start          # Start in foreground
openclaw gateway start --daemon # Start as daemon
openclaw gateway stop           # Stop daemon
openclaw gateway status         # Check status
openclaw gateway logs -f        # Follow logs

# Agent interaction
openclaw agent --message "..."  # Send message via CLI
openclaw agent                  # Interactive mode

# Cron management
openclaw cron list              # List scheduled jobs
openclaw cron add ...           # Add new job
openclaw cron remove <name>     # Remove job

# Skills management
openclaw skills list            # List available skills
openclaw skills refresh         # Reload skills

# Configuration
openclaw config get             # View current config
openclaw config set key value   # Set config value
openclaw doctor                 # Check system health
```

## Troubleshooting

### Bot not responding
```bash
# Check gateway is running
openclaw gateway status

# Check logs for errors
openclaw gateway logs

# Verify Telegram token
echo $TELEGRAM_BOT_TOKEN
```

### Skills not loading
```bash
# Refresh skills
openclaw skills refresh

# Check workspace path
openclaw config get agents.defaults.workspace

# Verify skill files exist
ls -la /Users/arjun/BuildBear/AgentARC/openclaw-workspace/skills/
```

### API errors
```bash
# Test API keys
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check environment loaded
env | grep -E "(OPENAI|ANTHROPIC|BRAVE|TELEGRAM)"
```

### Gateway won't start
```bash
# Check port availability
lsof -i :18789

# Kill existing process if needed
pkill -f "openclaw gateway"

# Try fresh start
openclaw gateway start
```

## Development Workflow

1. **Edit skills** in `skills/` folder
2. **Run `openclaw skills refresh`** to reload
3. **Test via Telegram** or CLI
4. **Check logs** for errors
5. **Iterate**

When ready for production, follow `deploy/gcp-setup.md` to deploy to GCP.

## Useful Aliases

Add to `~/.zshrc`:

```bash
# OpenClaw shortcuts
alias oc="openclaw"
alias ocg="openclaw gateway"
alias oca="openclaw agent --message"
alias ocl="openclaw gateway logs -f"

# Quick commands
alias oc-start="openclaw gateway start --daemon"
alias oc-stop="openclaw gateway stop"
alias oc-status="openclaw gateway status"
alias oc-research="openclaw agent --message '/q'"
```

Then use:
```bash
oc-start                    # Start daemon
oca "/q AI agent trends"    # Quick research
ocl                         # Follow logs
```
