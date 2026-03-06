# AgentARC Product Overview

## What is AgentARC?

AgentARC is an **advanced security and policy enforcement layer for AI blockchain agents**. It sits between an AI agent and the blockchain network, intercepting every transaction the agent wants to send and validating it through a rigorous 4-stage security pipeline **before the transaction is signed and sent on-chain**.

## The Problem We Solve

AI agents managing crypto wallets are high-value targets. Without AgentARC, agents can be exploited through:

- **Jailbreak attacks**: Prompt injection bypasses agent rules
- **Honeypot tokens**: Tokens that can be bought but not sold
- **Hidden approvals**: Unlimited token spend permissions to malicious contracts
- **Phishing contracts**: Legitimate-looking contracts that drain funds
- **Flash loan exploits**: Complex multi-step attacks
- **Reentrancy attacks**: Recursive calls that drain funds

**Key insight**: If an agent is compromised, every transaction it sends is compromised. AgentARC ensures no transaction executes without validation, regardless of agent state.

## Core Value Proposition

"Every transaction validated before signing"

Even if your AI agent is completely jailbroken or compromised:
1. AgentARC intercepts the transaction
2. Runs it through 4-stage validation
3. Blocks malicious transactions before signing
4. Funds stay safe

## Product Details

- **Package Name**: agentarc
- **PyPI**: https://pypi.org/project/agentarc/
- **GitHub**: https://github.com/BuildBear/AgentARC
- **License**: MIT (open source)
- **Current Version**: 0.3.0 (February 2026)
- **Python Support**: 3.10, 3.11, 3.12

## Installation

```bash
# Basic installation
pip install agentarc

# With framework support
pip install agentarc[openai]      # OpenAI SDK
pip install agentarc[langchain]   # LangChain/LangGraph
pip install agentarc[agentkit]    # Coinbase AgentKit

# With wallet support
pip install agentarc[smart-wallets]  # ERC-4337
pip install agentarc[safe]           # Gnosis Safe

# Everything
pip install agentarc[all]
```

## Quick Start

```python
from agentarc import AgentARC

# Initialize with policy
arc = AgentARC.from_policy("policy.yaml")

# Validate any transaction
result = arc.validate(transaction)

if result.approved:
    signed_tx = arc.sign_and_send(transaction)
else:
    print(f"Blocked: {result.reason}")
```

## Key Differentiators

| Feature | AgentARC | Manual Validation | No Protection |
|---------|----------|-------------------|---------------|
| Automatic honeypot detection | Yes | No | No |
| Policy-based rules | YAML config | Custom code | None |
| Transaction simulation | Tenderly-powered | DIY | None |
| LLM threat analysis | Optional, $0.003/tx | Expensive | None |
| Multi-wallet support | 4 types, 1 API | Per-wallet code | N/A |
| Framework adapters | 3 frameworks | DIY integration | N/A |

## Target Users

1. **AI Agent Developers** - Building autonomous blockchain agents
2. **DeFi Teams** - Deploying trading bots, portfolio managers
3. **DAO Treasury Managers** - AI-assisted fund management
4. **Crypto Startups** - Building agent-powered products
5. **Enterprise Blockchain Apps** - Compliance-focused deployments
