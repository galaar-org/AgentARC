# Contributing to AgentARC

Thank you for your interest in contributing to AgentARC! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Contributions](#making-contributions)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to security@agentarc.dev.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip or poetry

### Quick Start

```bash
# Fork and clone the repository
git clone https://github.com/galaar-org/AgentARC.git
cd AgentARC

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/
```

## Development Setup

### Installation Options

```bash
# Using pip
pip install -e ".[dev]"

# Using poetry
poetry install --with dev
```

### Environment Setup

```bash
# Copy example environment
cp .env.example .env

# Edit with your configuration
# - RPC_URL: Your Ethereum RPC endpoint
# - TENDERLY_* : Optional Tenderly API keys
# - OPENAI_API_KEY: Optional for LLM features
```

## Project Structure

AgentARC uses a modular architecture:

```
agentarc/
├── __init__.py           # Package exports (v0.2.0)
├── __main__.py           # CLI entry point
│
├── core/                 # Core types, interfaces, errors
│   ├── config.py         # PolicyConfig
│   ├── errors.py         # Exception classes
│   ├── interfaces.py     # Protocol definitions
│   └── types.py          # Type definitions
│
├── engine/               # Validation pipeline
│   ├── legacy.py         # Full PolicyEngine
│   ├── pipeline.py       # ValidationPipeline
│   ├── context.py        # ValidationContext
│   ├── factory.py        # ComponentFactory
│   └── stages/           # Pipeline stages
│       ├── intent.py
│       ├── policy.py
│       ├── simulation.py
│       ├── honeypot.py
│       └── llm.py
│
├── validators/           # Policy validators
│   ├── base.py           # PolicyValidator ABC
│   ├── registry.py       # ValidatorRegistry
│   └── builtin/          # Built-in validators
│       ├── address.py
│       ├── limits.py
│       ├── gas.py
│       └── functions.py
│
├── wallets/              # Universal wallet support
│   ├── base.py           # WalletAdapter ABC
│   ├── factory.py        # WalletFactory
│   ├── policy_wallet.py  # PolicyWallet
│   └── adapters/         # Wallet implementations
│       ├── private_key.py
│       ├── mnemonic.py
│       └── cdp.py
│
├── frameworks/           # AI framework adapters
│   ├── base.py           # FrameworkAdapter ABC
│   ├── langchain.py
│   └── agentkit.py
│
├── analysis/             # Security analysis
│   └── llm_judge.py
│
├── simulators/           # Transaction simulation
│   ├── basic.py
│   └── tenderly.py
│
├── parsers/              # Transaction parsing
│   └── calldata.py
│
├── events/               # Event streaming
│   └── events.py
│
├── log/                  # Logging
│   └── logger.py
│
└── compat/               # Backward compatibility
    └── wallet_wrapper.py
```

## Making Contributions

### Types of Contributions

We welcome:

- **Bug Fixes**: Fix issues and improve stability
- **New Features**: Add new validators, wallet adapters, or framework integrations
- **Documentation**: Improve docs, examples, and tutorials
- **Tests**: Increase test coverage
- **Performance**: Optimize existing code


## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all public APIs
- Maximum line length: 100 characters
- Use meaningful variable names

### Formatting

```bash
# Format code
black agentarc/ tests/

# Sort imports
isort agentarc/ tests/

# Lint
flake8 agentarc/ tests/
mypy agentarc/
```

### Docstrings

Use Google-style docstrings:

```python
def validate_transaction(
    self,
    tx: Dict[str, Any],
    from_address: str
) -> Tuple[bool, str]:
    """
    Validate transaction against configured policies.

    Args:
        tx: Transaction dictionary with to, value, data fields
        from_address: Sender address for simulation

    Returns:
        Tuple of (passed, reason) where passed is True if
        transaction is allowed

    Raises:
        PolicyViolationError: If transaction violates policy
        SimulationError: If simulation fails

    Example:
        >>> engine = PolicyEngine(config_path="policy.yaml")
        >>> passed, reason = engine.validate_transaction(tx, addr)
    """
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=agentarc --cov-report=html

# Run specific test file
pytest tests/test_validators.py

# Run specific test
pytest tests/test_validators.py::test_address_denylist
```

### Test Coverage

We aim for >80% test coverage. New features should include tests for:

- Success cases
- Failure cases
- Edge cases
- Error handling

## Documentation

### Updating Documentation

1. Update docstrings in code
2. Update README.md for user-facing changes
3. Update CHANGELOG.md
4. Add examples to `examples/` directory

### CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [0.2.1] - 2024-01-15

### Added
- New `MyValidator` for custom validation

### Changed
- Improved error messages in PolicyEngine

### Fixed
- Fixed bug in address validation (#123)
```

## Submitting Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new validator for gas limits
fix: correct address validation logic
docs: update contributing guidelines
refactor: simplify pipeline stages
test: add tests for wallet factory
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run tests and linting
5. Update documentation
6. Push to your fork
7. Open a Pull Request

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or clearly documented)

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/anthropics/agentarc/discussions)
- **Bugs**: Open an [Issue](https://github.com/anthropics/agentarc/issues)
- **Security**: Email security@agentarc.dev

## Recognition

Contributors are recognized in:

- Release notes
- README.md contributors section
- GitHub contributors page

---

Thank you for contributing to AgentARC!
