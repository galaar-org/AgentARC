# Frequently Asked Questions

## General

### What is AgentARC?
AgentARC is a security and policy enforcement layer for AI blockchain agents. It validates every transaction through a 4-stage pipeline before signing, preventing exploits even if the agent is compromised.

### Is AgentARC free?
Yes. AgentARC is open source under the MIT license. The only optional cost is LLM analysis (Stage 4) at ~$0.003 per transaction if you enable it.

### What blockchains does AgentARC support?
Ethereum, Base, Arbitrum, and Optimism (mainnet and testnets). More chains coming based on demand.

### What Python versions are supported?
Python 3.10, 3.11, and 3.12.

---

## Security

### How does AgentARC prevent jailbreak attacks?
AgentARC validates transactions independent of the agent's state. Even if an attacker jailbreaks your agent and makes it generate malicious transactions, AgentARC blocks them before signing. The validation layer can't be bypassed via prompt injection.

### What is honeypot detection?
Honeypot tokens are scam tokens that can be bought but not sold. When AgentARC detects a buy transaction, it automatically simulates the corresponding sell. If the sell would fail, the buy is blocked.

### How accurate is the LLM security analysis?
Stage 4 catches sophisticated attacks that rule-based checks miss, like hidden approvals and reentrancy patterns. It's not 100% (nothing is), which is why we use it alongside rule-based policies and simulation.

### Can AgentARC be bypassed?
AgentARC must be integrated into your transaction signing flow. If transactions go through AgentARC, they're validated. The security comes from architectural integration, not magic.

---

## Technical

### How do I install AgentARC?
```bash
pip install agentarc

# With extras
pip install agentarc[openai]      # OpenAI SDK
pip install agentarc[langchain]   # LangChain
pip install agentarc[all]         # Everything
```

### How do I configure policies?
Create a `policy.yaml` file:
```yaml
version: "1.0"
validation:
  intent_analysis: true
  policy_check: true
  simulation: true
  honeypot_detection: true
  llm_analysis: false

policies:
  eth_value_limit: 1.0
  gas_limit: 500000
```

### Does AgentARC work with my existing agent?
Yes. AgentARC provides framework adapters for OpenAI SDK, LangChain, and AgentKit. For other frameworks, use the core API directly.

### What's the latency overhead?
- Stage 1 (Intent): ~10ms
- Stage 2 (Policy): ~5ms
- Stage 3 (Simulation): ~500-2000ms (Tenderly API)
- Stage 4 (LLM): ~500-1500ms (if enabled)

Total: 0.5-4 seconds depending on configuration. Simulation is the main factor.

### Can I use AgentARC without simulation?
Yes. You can disable any stage in `policy.yaml`. Without simulation, you lose honeypot detection and execution safety checks, but gain speed.

---

## Wallets

### What wallet types are supported?
- EOA (standard private key wallets)
- ERC-4337 (smart wallets with gas sponsorship)
- Safe (multi-signature wallets)
- CDP (Coinbase Developer Platform)

### Can I switch wallet types without changing my agent code?
Yes. The wallet abstraction means you change one line of configuration, and your agent code stays the same.

### How do I use ERC-4337 with gas sponsorship?
```python
from agentarc.wallets import SmartWallet

wallet = SmartWallet(
    bundler_url="https://api.pimlico.io/v1/...",
    paymaster_url="https://api.pimlico.io/v1/..."
)
arc = AgentARC(wallet=wallet, policy="policy.yaml")
```

### How does Safe integration work?
AgentARC can propose transactions to a Safe, handling the multi-sig flow. Transactions still go through the 4-stage pipeline before being proposed.

---

## Integration

### How do I integrate with OpenAI function calling?
```python
from agentarc.frameworks.openai import OpenAIAdapter

adapter = OpenAIAdapter(arc)
tools = adapter.get_tools()
# Pass tools to OpenAI chat completion
```

### How do I integrate with LangChain?
```python
from agentarc.frameworks.langchain import LangChainAdapter

adapter = LangChainAdapter(arc)
tools = adapter.get_langchain_tools()
# Use with any LangChain agent
```

### Can I use AgentARC with AutoGPT/CrewAI/other frameworks?
Yes. Use the core AgentARC API directly. If there's demand, we'll add native adapters.

---

## Troubleshooting

### My transaction was blocked unexpectedly
1. Check logs for the specific stage that blocked it
2. Review your `policy.yaml` settings
3. If honeypot detection blocked it, verify the token is legitimate
4. For false positives, adjust policies or contact support

### Simulation is failing
1. Ensure `TENDERLY_API_KEY` is set
2. Check the transaction has valid parameters
3. Verify the target contract exists on the network

### LLM analysis isn't working
1. Ensure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
2. Enable `llm_analysis: true` in policy.yaml
3. Check API rate limits/billing

---

## Business

### Who built AgentARC?
AgentARC is built by Galaar (dipeshsukhani.dev), backed by BuildBear.

### How do I get support?
- GitHub Issues: Bug reports and feature requests
- Discord: Community support and discussions
- Email: For enterprise inquiries

### Is there an enterprise version?
The open source version is full-featured. For enterprise support, SLAs, or custom development, contact us.

### Can I contribute?
Yes! AgentARC is MIT licensed. See CONTRIBUTING.md in the repository.
