# GCP Compute Deployment Guide

Deploy OpenClaw content marketing agent on Google Cloud Platform.

## Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed locally
- Telegram Bot Token (from @BotFather)
- API keys ready (see TOOLS.md)

## Step 1: Create GCP Compute Instance

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Create instance
gcloud compute instances create openclaw-agent \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=openclaw

# Allow outbound HTTPS (for APIs)
gcloud compute firewall-rules create allow-openclaw-outbound \
  --direction=EGRESS \
  --action=ALLOW \
  --rules=tcp:443 \
  --target-tags=openclaw
```

**Recommended specs:**
- **Dev/Testing:** e2-small (2 vCPU, 2GB RAM) ~$15/month
- **Production:** e2-medium (2 vCPU, 4GB RAM) ~$25/month
- **Heavy usage:** e2-standard-2 (2 vCPU, 8GB RAM) ~$50/month

## Step 2: SSH and Install Dependencies

```bash
# SSH into instance
gcloud compute ssh openclaw-agent --zone=us-central1-a

# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version  # Should be 22.x

# Install OpenClaw
sudo npm install -g openclaw@latest

# Create workspace directory
sudo mkdir -p /home/openclaw/workspace
sudo chown $USER:$USER /home/openclaw/workspace
```

## Step 3: Upload Workspace

From your local machine:

```bash
# Upload workspace files
gcloud compute scp --recurse \
  /Users/arjun/BuildBear/AgentARC/openclaw-workspace/* \
  openclaw-agent:/home/openclaw/workspace/ \
  --zone=us-central1-a
```

## Step 4: Configure Environment Variables

On the GCP instance:

```bash
# Create env file
sudo nano /etc/openclaw/env

# Add your keys:
TELEGRAM_BOT_TOKEN=your_bot_token
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
BRAVE_API_KEY=your_key
GENVIRAL_API_KEY=your_key
DEEPGRAM_API_KEY=your_key
WP_SITE_URL=https://blog.agentarc.dev
WP_USERNAME=your_user
WP_APPLICATION_PASSWORD=your_app_password

# Secure it
sudo chmod 600 /etc/openclaw/env
```

## Step 5: Setup Telegram Bot

1. **Create bot** with @BotFather on Telegram:
   ```
   /newbot
   Name: AgentARC Content Bot
   Username: agentarc_content_bot
   ```

2. **Get your Telegram user ID**:
   - Message @userinfobot
   - Copy your numeric ID

3. **Update config** to allow your user:
   ```bash
   nano /home/openclaw/workspace/config/openclaw.json
   # Add your ID to allowedUsers array
   ```

## Step 6: Create Systemd Service

```bash
sudo nano /etc/systemd/system/openclaw.service
```

Content:
```ini
[Unit]
Description=OpenClaw Content Marketing Agent
After=network.target

[Service]
Type=simple
User=ubuntu
EnvironmentFile=/etc/openclaw/env
WorkingDirectory=/home/openclaw/workspace
ExecStart=/usr/bin/openclaw gateway start
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/openclaw/agent.log
StandardError=append:/var/log/openclaw/error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/openclaw
sudo chown ubuntu:ubuntu /var/log/openclaw

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw

# Check status
sudo systemctl status openclaw
```

## Step 7: Setup Cron Jobs

```bash
# SSH into instance
gcloud compute ssh openclaw-agent --zone=us-central1-a

# Add cron jobs
openclaw cron add \
  --name "morning-research" \
  --cron "0 8 * * *" \
  --tz "America/New_York" \
  --message "Research trending AI agent security topics and summarize"

openclaw cron add \
  --name "competitor-scan" \
  --cron "0 9 * * 1" \
  --tz "America/New_York" \
  --message "Run weekly competitor scan"

openclaw cron add \
  --name "newsletter-prep" \
  --cron "0 10 * * 4" \
  --tz "America/New_York" \
  --message "Prepare weekly newsletter draft"

openclaw cron add \
  --name "performance-report" \
  --cron "0 18 * * 0" \
  --tz "America/New_York" \
  --message "Generate weekly content performance report"
```

## Step 8: Test Telegram Connection

1. Open Telegram
2. Start chat with your bot
3. Send: `/start`
4. Bot should respond with pairing code
5. Approve pairing on server or via code

Test commands:
```
/status
/q AI agent security
/idea
```

## Maintenance Commands

```bash
# View logs
sudo tail -f /var/log/openclaw/agent.log

# Restart service
sudo systemctl restart openclaw

# Update OpenClaw
sudo npm update -g openclaw@latest
sudo systemctl restart openclaw

# Update workspace (from local)
gcloud compute scp --recurse \
  /Users/arjun/BuildBear/AgentARC/openclaw-workspace/* \
  openclaw-agent:/home/openclaw/workspace/ \
  --zone=us-central1-a
```

## Cost Optimization

### Preemptible Instance (70% cheaper)
```bash
gcloud compute instances create openclaw-agent \
  --preemptible \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  # ... rest of flags
```
Note: Instance may restart every 24h. Use with systemd for auto-recovery.

### Committed Use Discount
For production: 1-year commitment = 37% discount

### Auto-Shutdown (if not 24/7)
```bash
# Stop at night (11pm)
gcloud compute instances add-metadata openclaw-agent \
  --metadata=shutdown-script='#!/bin/bash
  if [ $(date +%H) -eq 23 ]; then
    shutdown -h now
  fi'
```

## Security Hardening

```bash
# Firewall: Block all inbound except SSH
gcloud compute firewall-rules create deny-all-inbound \
  --direction=INGRESS \
  --action=DENY \
  --rules=all \
  --target-tags=openclaw \
  --priority=1000

gcloud compute firewall-rules create allow-ssh \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=YOUR_IP/32 \
  --target-tags=openclaw \
  --priority=100

# Use Secret Manager for API keys (recommended)
gcloud secrets create openclaw-env --data-file=/etc/openclaw/env
```

## Monitoring

```bash
# Setup Cloud Monitoring alert for instance down
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL \
  --display-name="OpenClaw Agent Down" \
  --condition-display-name="Instance not running" \
  --condition-filter='resource.type="gce_instance" AND metric.type="compute.googleapis.com/instance/uptime"'
```
