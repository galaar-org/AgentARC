# Onchain Agent Powered by AgentKit

This is a Python chatbot project bootstrapped with `create-onchain-agent`.  
It integrates [AgentKit](https://github.com/coinbase/agentkit) to provide AI-driven interactions with on-chain capabilities.

## Prerequisites

Before using `create-onchain-agent`, ensure you have the following installed:

- **Python** (3.10 - 3.12) – [Download here](https://www.python.org/downloads/)
- **Poetry** (latest version) – [Installation guide](https://python-poetry.org/docs/#installation)

## Getting Started

First, install dependencies:

`poetry install`

Then, configure your environment variables:

```sh
mv .env.local .env
```

Finally, run the chatbot:

`poetry run python chatbot.py`


## Configuring Your Agent

You can [modify your agent configuration](https://github.com/coinbase/agentkit/tree/main/typescript/agentkit#usage) in the `chatbot.py` file.

### 1. Select Your LLM  
Modify the `ChatOpenAI` instantiation to use the model of your choice.

### 2. Select Your Wallet Provider  
AgentKit requires a **Wallet Provider** to interact with blockchain networks.

### 3. Select Your Action Providers
Action Providers define what your agent can do. You can use built-in providers or create your own.

### 4. PolicyLayer Integration (AgentARC)
This example includes **PolicyLayer** - a security framework that validates transactions before execution.

**Features:**
- **Rule-based policies**: Spending limits, address allow/deny lists, gas limits
- **Transaction simulation**: Test transactions before sending them on-chain
- **Intelligent validation** (optional): AI-powered malicious activity detection

**Configuration:**

Edit `policy.yaml` to configure your security policies. By default, PolicyLayer uses basic rule-based validation.

**Enable Intelligent Features:**

For advanced security with AI-powered analysis:

1. **Tenderly Simulation** - Get detailed call traces and asset changes:
   ```yaml
   # In policy.yaml
   tenderly:
     enabled: true
   ```
   Add Tenderly credentials to your `.env` file:
   ```bash
   TENDERLY_ACCESS_KEY=your-access-key
   TENDERLY_ACCOUNT_SLUG=your-account
   TENDERLY_PROJECT_SLUG=your-project
   ```
   Get these from [dashboard.tenderly.co](https://dashboard.tenderly.co)

2. **LLM Judge** - Detect malicious patterns like hidden approvals, reentrancy, phishing:
   ```yaml
   # In policy.yaml
   llm_judge:
     enabled: true
     provider: "openai"  # or "anthropic"
     model: "gpt-4o-mini"
     block_threshold: 0.70
   ```
   Ensure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set in `.env`

**How it works:**
1. **Intent Judge** - Parses transaction calldata
2. **Policy Validation** - Checks against configured rules
3. **Simulation** - Tests execution (Sentio or basic)
4. **LLM Analysis** - AI detects sophisticated attacks (if enabled)

Cost: ~$0.003 per transaction with GPT-4-mini

If API keys are not set, intelligent features are gracefully skipped.

---

## Next Steps

- Explore the AgentKit README: [AgentKit Documentation](https://github.com/coinbase/agentkit)
- Learn more about available Wallet Providers & Action Providers.
- Experiment with custom Action Providers for your specific use case.

## Learn More

- [Learn more about CDP](https://docs.cdp.coinbase.com/)
- [Learn more about AgentKit](https://docs.cdp.coinbase.com/agentkit/docs/welcome)


## Contributing

Interested in contributing to AgentKit? Follow the contribution guide:

- [Contribution Guide](https://github.com/coinbase/agentkit/blob/main/CONTRIBUTING.md)
- Join the discussion on [Discord](https://discord.gg/CDP)
