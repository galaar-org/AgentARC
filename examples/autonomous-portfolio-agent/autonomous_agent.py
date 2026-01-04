#!/usr/bin/env python3
"""Autonomous Portfolio Manager - Main Entry Point

This script creates an autonomous AI agent that:
1. Manages a crypto portfolio on Base Sepolia
2. Automatically rebalances to maintain target allocation
3. Protected by PolicyLayer (honeypot detection, policy limits, LLM analysis)

Usage:
    python autonomous_agent.py
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.align import Align
from rich.text import Text
from rich.layout import Layout

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coinbase_agentkit import CdpEvmWalletProvider, CdpEvmWalletProviderConfig

# Import PolicyLayer components
from agentguard import PolicyWalletProvider, PolicyEngine

from core.agent import AutonomousPortfolioAgent
from config.portfolio_config import TARGET_ALLOCATION, TOKENS, REBALANCE_INTERVAL

# Initialize Rich console
console = Console()


def display_banner():
    """Display a beautiful banner"""
    banner = Text()
    banner.append("🚀 AUTONOMOUS PORTFOLIO MANAGER\n", style="bold cyan")
    banner.append("with Honeypot Protection & PolicyLayer", style="bold magenta")

    panel = Panel(
        Align.center(banner),
        border_style="bright_blue",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(panel)
    console.print()


def display_environment_check(required_vars):
    """Display environment variable status"""
    table = Table(
        title="[bold cyan]🔍 Environment Variables Check[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_blue",
        box=box.ROUNDED
    )

    table.add_column("Variable", style="cyan", width=30)
    table.add_column("Status", justify="center", width=10)

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            table.add_row(var, "[green]✅ Set[/green]")
        else:
            table.add_row(var, "[red]❌ Missing[/red]")
            missing_vars.append(var)

    console.print(table)
    console.print()

    return missing_vars


def display_setup_steps():
    """Display setup progress steps"""
    steps = [
        ("1️⃣", "Create CDP Server Wallet", [
            "→ Keys managed by Coinbase (AWS Nitro Enclaves)",
            "→ Sub-200ms signing latency",
            "→ 99.9% availability"
        ]),
        ("2️⃣", "Add PolicyLayer Protection", [
            "→ Stage 1: Intent Judge (parse transactions)",
            "→ Stage 2: Policy Validation (limits, rules)",
            "→ Stage 3: Tenderly Simulation (pre-execute)",
            "→ Stage 3.5: Honeypot Detection (automatic!) 🛡️",
            "→ Stage 4: LLM Security Analysis (pattern detection)"
        ]),
        ("3️⃣", "Launch Autonomous Agent", [
            f"→ Target allocation: {TARGET_ALLOCATION}",
            f"→ Rebalance interval: {REBALANCE_INTERVAL}s",
            f"→ Tokens: {list(TOKENS.keys())}"
        ])
    ]

    return steps


def display_step(step_num, title, details, status="in_progress"):
    """Display a setup step with status"""
    if status == "in_progress":
        icon = "⏳"
        style = "yellow"
    elif status == "completed":
        icon = "✅"
        style = "green"
    else:
        icon = "❌"
        style = "red"

    content = f"[bold {style}]{step_num} {title}[/bold {style}]\n\n"
    for detail in details:
        content += f"[dim]{detail}[/dim]\n"

    panel = Panel(
        content.strip(),
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)


def display_wallet_info(wallet_address):
    """Display wallet information"""
    info_panel = Panel(
        f"[bold green]Wallet Address:[/bold green]\n"
        f"[cyan]{wallet_address}[/cyan]",
        title="[bold green]✅ CDP Wallet Ready[/bold green]",
        border_style="green",
        box=box.ROUNDED
    )
    console.print(info_panel)
    console.print()


def display_start_message():
    """Display autonomous loop start message"""
    start_panel = Panel(
        "[bold cyan]🤖 Starting Autonomous Loop...[/bold cyan]\n\n"
        "[yellow]The agent will continuously monitor and rebalance your portfolio.[/yellow]\n"
        "[dim]Press Ctrl+C to stop gracefully[/dim]",
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(start_panel)
    console.print()


async def main():
    """Main entry point for autonomous portfolio manager"""

    # Load environment variables
    load_dotenv()

    # Display banner
    display_banner()

    # Verify required environment variables
    # Note: ADDRESS and CDP_WALLET_SECRET are optional
    # If ADDRESS is not set, a new wallet will be created
    required_env_vars = [
        "CDP_API_KEY_ID",
        "CDP_API_KEY_SECRET",
        "OPENAI_API_KEY",
        "TENDERLY_API_KEY",
        "TENDERLY_ACCOUNT_SLUG",
        "TENDERLY_PROJECT_SLUG"
    ]

    missing_vars = display_environment_check(required_env_vars)

    if missing_vars:
        console.print(Panel(
            "[bold red]❌ Missing Required Environment Variables[/bold red]\n\n"
            f"Please set the following variables in your .env file:\n"
            + "\n".join([f"  • {var}" for var in missing_vars]),
            border_style="red",
            box=box.ROUNDED
        ))
        sys.exit(1)

    console.print("[bold green]✅ All environment variables configured![/bold green]\n")

    # Get setup steps
    steps = display_setup_steps()

    # Step 1: Initialize CDP Wallet
    with console.status("[bold yellow]Creating CDP Server Wallet...[/bold yellow]", spinner="dots"):
        time.sleep(0.5)  # Visual delay

    display_step(
        steps[0][0],
        steps[0][1],
        steps[0][2],
        "in_progress"
    )

    # Check if ADDRESS is provided
    existing_address = os.getenv("ADDRESS")
    if existing_address:
        console.print(f"[bold cyan]📍 Using existing wallet: {existing_address}[/bold cyan]\n")
    else:
        console.print("[bold yellow]🆕 No ADDRESS provided - creating new CDP wallet...[/bold yellow]\n")

    cdp_wallet = CdpEvmWalletProvider(CdpEvmWalletProviderConfig(
        api_key_id=os.getenv("CDP_API_KEY_ID"),
        api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
        wallet_secret=os.getenv("CDP_WALLET_SECRET"),
        network_id="base-sepolia",
        address=existing_address,  # None if not set → creates new wallet
    ))

    wallet_address = cdp_wallet.get_address()

    # If a new wallet was created, inform the user
    if not existing_address:
        console.print(f"[bold green]✨ New wallet created![/bold green]")
        console.print(f"[yellow]💡 Tip: Add this to your .env to reuse this wallet:[/yellow]")
        console.print(f"[cyan]ADDRESS={wallet_address}[/cyan]\n")

    display_wallet_info(wallet_address)

    # Step 2: Wrap with PolicyLayer protection
    with console.status("[bold yellow]Adding PolicyLayer protection...[/bold yellow]", spinner="dots"):
        time.sleep(0.5)  # Visual delay

    display_step(
        steps[1][0],
        steps[1][1],
        steps[1][2],
        "in_progress"
    )

    policy_config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config/policy.yaml"
    )

    policy_engine = PolicyEngine(
        config_path=policy_config_path,
        web3_provider=cdp_wallet,
        chain_id=84532  # Base Sepolia
    )

    protected_wallet = PolicyWalletProvider(
        base_provider=cdp_wallet,
        policy_engine=policy_engine
    )

    console.print("[bold green]   ✅ PolicyLayer enabled[/bold green]\n")

    # Step 3: Create autonomous agent
    with console.status("[bold yellow]Launching autonomous agent...[/bold yellow]", spinner="dots"):
        time.sleep(0.5)  # Visual delay

    display_step(
        steps[2][0],
        steps[2][1],
        steps[2][2],
        "in_progress"
    )

    agent = AutonomousPortfolioAgent(
        wallet_provider=protected_wallet,  # CDP Wallet + PolicyLayer!
        target_allocation=TARGET_ALLOCATION,
        token_addresses=TOKENS,
        rebalance_interval=REBALANCE_INTERVAL,
        policy_engine=policy_engine
    )

    console.print("[bold green]   ✅ Agent ready[/bold green]\n")

    # Step 4: Run autonomous loop
    display_start_message()

    await agent.run_autonomous_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n")
        console.print(Panel(
            "[bold yellow]👋 Shutting down gracefully...[/bold yellow]\n"
            "[dim]Thank you for using Autonomous Portfolio Manager![/dim]",
            border_style="yellow",
            box=box.ROUNDED
        ))
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ Fatal Error:[/bold red]\n\n{str(e)}",
            border_style="red",
            box=box.ROUNDED
        ))
        import traceback
        traceback.print_exc()
        sys.exit(1)
