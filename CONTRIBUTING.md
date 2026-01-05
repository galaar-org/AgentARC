# Contributing to AgentARC

Thank you for your interest in contributing to AgentARC! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or poetry

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/agentarc.git
cd agentarc

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Or with poetry
poetry install --with dev
```

## Project Structure

```
agentarc/
├── agentarc/           # Main package source code
│   ├── __init__.py        # Package exports
│   ├── __main__.py        # CLI entry point
│   ├── policy_engine.py   # Core validation engine
│   ├── wallet_wrapper.py  # Wallet provider wrapper
│   ├── calldata_parser.py # Transaction parsing
│   ├── simulator.py       # Transaction simulation
│   ├── logger.py          # Logging system
│   └── rules/             # Policy validators
│       ├── __init__.py
│       └── validators.py  # All policy validators
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation
└── pyproject.toml         # Package configuration
```

## Testing

### Running Tests

```bash
# Run all tests
cd tests
python test_complete_system.py

# Run specific test
python test_fix.py
```

### Writing Tests

When adding new features, please include tests:

1. Create test file in `tests/`
2. Test all success and failure cases
3. Verify logging output
4. Check edge cases

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where applicable
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose

### Example

```python
def validate_transaction(self, tx: Dict[str, Any], from_address: str) -> tuple[bool, str]:
    """
    Validate transaction against all configured policies.

    Args:
        tx: Transaction dictionary with to, value, data, etc.
        from_address: Sender address for simulation

    Returns:
        Tuple of (passed: bool, reason: str)
    """
    # Implementation
    pass
```

## Adding New Policy Types

To add a new policy validator:

1. Create validator class in `agentarc/rules/validators.py`
2. Inherit from `PolicyValidator` base class
3. Implement `validate()` method
4. Register in `PolicyEngine._create_validators()`
5. Add configuration example to default policy.yaml
6. Write tests
7. Update documentation

### Example

```python
class MyCustomValidator(PolicyValidator):
    """Description of what this validator does"""

    def validate(self, parsed_tx: ParsedTransaction) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        # Your validation logic here
        if some_condition:
            return ValidationResult(
                passed=False,
                reason="Description of why it failed",
                rule_name="my_custom_rule"
            )

        return ValidationResult(passed=True)
```

## Submitting Changes

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Run tests to ensure they pass
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include test coverage for new features
- Update CHANGELOG.md
- Ensure all tests pass
- Follow existing code style

## Documentation

When adding new features:

1. Update README.md if needed
2. Add examples to `examples/`
3. Update CHANGELOG.md
4. Add inline code documentation
5. Update configuration examples

## Reporting Issues

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- AgentARC version
- Python version
- Error messages/logs

### Feature Requests

Include:
- Clear description of the feature
- Use case / motivation
- Proposed implementation (if any)
- Examples

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Focus on constructive feedback
- Accept differing viewpoints
- Prioritize community benefit

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Trolling or insulting comments
- Publishing private information

## Questions?

- Open an issue for questions
- Check existing documentation
- Review examples in `examples/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AgentARC! 🎉
