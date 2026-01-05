# Changelog

All notable changes to AgentArc will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-02

### 🎉 Initial Release

First stable release of AgentArc - A comprehensive security and policy enforcement layer for AI blockchain agents.

### ✨ Features

#### Core Security Pipeline
- **Multi-Stage Validation Pipeline**: 4-stage validation (Intent Judge → Policy Validation → Simulation → LLM Analysis)
- **Zero Agent Modifications**: Pure wrapper pattern for seamless AgentKit integration
- **3-Line Integration**: Simple API for wrapping any wallet provider

#### Policy Engine (7 Policy Types)
- **ETH Value Limit**: Prevent large ETH transfers per transaction
- **Address Denylist**: Block transactions to sanctioned/malicious addresses
- **Address Allowlist**: Whitelist mode - only allow pre-approved addresses
- **Per-Asset Limits**: Token-specific spending limits (USDC, DAI, etc.)
- **Token Amount Limit**: Global ERC20 token transfer limits
- **Gas Limit**: Prevent expensive transactions
- **Function Allowlist**: Only allow specific function calls

#### Transaction Simulation
- **Tenderly Integration**: Advanced simulation with full execution traces
- **Asset Change Tracking**: Monitor balance changes before execution
- **Gas Estimation**: Accurate gas predictions
- **Revert Detection**: Catch failures before broadcasting
- **Detailed Trace Output**: Optional `print_trace` for debugging

#### Honeypot Detection (Stage 3.5)
- **Automatic Buy/Sell Testing**: Simulates token purchase then sale
- **Zero Manual Blacklisting**: Detects unknown honeypots via simulation
- **Transfer Event Validation**: Verifies actual token movement
- **Balance Verification**: Ensures balance changes match expectations
- **Known Token Whitelist**: Skips checks for WETH, USDC, DAI, etc.

#### LLM-based Security Analysis (Stage 4)
- **AI-Powered Threat Detection**: GPT-4/Claude analysis of transactions
- **Pattern Recognition**: Detects hidden approvals, unusual fund flows, reentrancy
- **Risk Scoring**: Confidence levels and risk ratings (LOW/MEDIUM/HIGH/CRITICAL)
- **Configurable Thresholds**: Block at 70%, warn at 40% (customizable)
- **Multiple Providers**: Support for OpenAI and Anthropic

#### Logging & Observability
- **Three Logging Levels**: minimal, info, debug
- **Structured Output**: Clear stage-by-stage validation results
- **Asset Change Reporting**: Show balance changes inline
- **Error Context**: Detailed failure reasons and recommendations

#### Examples & Documentation
- **Basic Usage Example**: Mock wallet demonstration
- **OnChain Agent**: Production-ready AgentKit chatbot
- **Autonomous Portfolio Agent**: AI portfolio manager with honeypot protection
- **Comprehensive README**: Complete setup and configuration guide
- **Policy Templates**: Ready-to-use YAML configurations

### 🛠️ Technical Implementation

#### Architecture
- **PolicyEngine**: Core validation orchestrator
- **PolicyWalletProvider**: Transparent wallet wrapper
- **CalldataParser**: ABI decoding for ERC20 and custom functions
- **TenderlySimulator**: Advanced simulation client
- **LLMJudge**: AI security analysis engine
- **Rule Validators**: Modular policy enforcement

#### Compatibility
- ✅ CDP EVM Wallet Provider
- ✅ CDP Smart Wallet Provider
- ✅ Ethereum Account Wallet Provider
- ✅ Base, Base Sepolia, Ethereum Mainnet, Arbitrum, Optimism

### 📦 Dependencies

#### Required
- Python 3.10+
- web3.py
- pyyaml
- cdp-sdk (for CDP wallet integration)

#### Optional
- requests (for Tenderly simulation)
- openai / anthropic (for LLM validation)

### 🔧 Configuration

Default `policy.yaml` includes:
- ETH limit: 1 ETH per transaction
- Per-asset limits for USDC (10) and DAI (100)
- Gas limit: 500k
- Simulation enabled
- LLM validation disabled by default

### 🐛 Known Issues

- None reported in initial release

### 📝 Breaking Changes

- N/A (initial release)

### 🔒 Security

- All transactions validated before execution
- No credentials stored in logs
- Simulation uses read-only `eth_call`
- Tenderly API keys required for advanced features

### 📚 Documentation

- Comprehensive README with examples
- Inline code documentation
- Example projects with setup guides
- Policy configuration templates