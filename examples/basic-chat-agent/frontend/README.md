# AgentARC

A chat interface that demonstrates secure crypto transaction validation. When you ask the agent to make a transaction, it runs security checks before executing - blocking scams like honeypot tokens and suspicious approvals.

## What This Does

You chat with an agent that can:
- Check your wallet balance
- Transfer ETH to addresses
- Buy tokens

Before any transaction executes, the agent validates it through multiple security checks:
- **Intent Analysis** - Understands what the transaction will do
- **Policy Validation** - Checks against security rules
- **Simulation** - Runs the transaction in a sandbox
- **Honeypot Detection** - Identifies scam tokens you can buy but can't sell
- **LLM Validation** - Catches suspicious patterns like unlimited token approvals

If something looks wrong, the transaction gets blocked and you see exactly why.

## Try It Out

### 1. Install

```bash
pnpm install
```

### 2. Run

```bash
pnpm dev
```

Open http://localhost:3000

### 3. Test Commands

The chat has suggestion buttons, or type these:

- `Check my balance` - Shows wallet balance
- `What is my wallet address?` - Shows wallet details
- `Transfer 0.001 ETH to 0x...` - Runs a transfer (passes validation)
- `Buy honeypot tokens` - Attempts to buy a scam token (gets blocked)
- `Approve unlimited tokens` - Attempts a dangerous approval (gets blocked)

## Project Structure

```
app/
  page.tsx              # Chat interface
  api/
    chat/route.ts       # Backend connection

components/
  ValidationEvents.tsx  # Displays security check results
  ai-elements/          # Chat UI components
  ui/                   # Base UI components (buttons, cards, etc.)

lib/
  types.ts              # TypeScript types
  utils.ts              # Helper functions
```

## How It Works

1. You send a message
2. The backend parses your intent
3. If it's a transaction, it runs through validation stages
4. Results stream back as the checks complete
5. You see each check pass/fail with details
6. Transaction either executes or gets blocked

## Backend API

The app connects to a backend specified in `app/api/chat/route.ts`. The backend should:

1. Accept POST requests with `{ message: string, thread_id: string }`
2. Return Server-Sent Events (SSE) with these event types:

```typescript
// Text from the agent
{ type: 'agent', content: 'I will check your balance.' }

// Tool/command output
{ type: 'tool', content: 'Balance: 0.5 ETH' }

// Validation events (array of checks)
{ type: 'events', events: [...] }

// Errors
{ type: 'error', content: 'Something went wrong' }

// Stream complete
{ type: 'done' }
```

Each validation event has:

```typescript
{
  stage: 'honeypot_detection',  // Which check
  status: 'failed',             // passed, failed, warning, info
  message: 'Honeypot detected', // Human-readable result
  timestamp: 1234567890,        // Unix timestamp
  details: { ... }              // Extra data
}
```

## Tech Stack

- **Next.js 14** - React framework
- **Tailwind CSS 4** - Styling
- **shadcn/ui** - UI components
- **Vercel AI SDK** - Chat streaming
