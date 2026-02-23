"""
CLI for AgentARC

Usage:
    python -m agentarc setup
    agentarc setup
"""

import click


@click.group()
def cli():
    """AgentARC CLI - Advanced policy enforcement for AI agents"""
    pass


@cli.command()
@click.option("--path", default=None, help="Project path (optional, defaults to current directory)")
def setup(path: str):
    """Interactive wizard to create an AgentARC-protected agent project."""
    from .cli.wizard import SetupWizard

    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    cli()
