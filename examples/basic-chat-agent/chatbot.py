#!/usr/bin/env python3
"""
AgentKit Chatbot with PolicyLayer Integration

This chatbot demonstrates how the PolicyLayer validates and monitors
all transactions before they are executed on-chain.

Features:
- All transactions are validated against configured policies
- Transaction details and calldata are printed before execution
- Policies can block invalid transactions
- Works with all AgentKit action providers

Usage:
    python chatbot.py
"""

import os
import sys
import time
import asyncio
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout
from rich import box
from rich.align import Align
from rich.text import Text

from setup import setup

load_dotenv()

# Initialize Rich console
console = Console()


def display_banner():
    """Display a beautiful banner for the chatbot"""
    banner = Text()
    banner.append("CDP Agent Chatbot\n", style="bold cyan")
    banner.append("with PolicyLayer Protection", style="bold magenta")

    panel = Panel(
        Align.center(banner),
        border_style="bright_blue",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(panel)
    console.print()


def display_mode_menu():
    """Display mode selection menu"""
    table = Table(
        title="[bold cyan]🎯 Choose Your Mode[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_blue",
        box=box.ROUNDED
    )

    table.add_column("Option", style="cyan", justify="center", width=10)
    table.add_column("Mode", style="green", width=20)
    table.add_column("Description", style="white", width=50)

    table.add_row(
        "1",
        "💬 Chat Mode",
        "Interactive conversation with the AI agent"
    )
    table.add_row(
        "2",
        "🤖 Auto Mode",
        "Autonomous agent executing blockchain actions"
    )

    console.print(table)
    console.print()


def display_chat_help():
    """Display helpful suggestions for chat mode"""
    help_panel = Panel(
        "[bold yellow]💡 Try These Commands:[/bold yellow]\n\n"
        "  • [cyan]Get my wallet details[/cyan]\n"
        "  • [cyan]Transfer 0.1 ETH to <address>[/cyan]\n"
        "  • [cyan]Check my balance[/cyan]\n"
        "  • [cyan]Deploy a contract[/cyan]\n\n"
        "[dim]Watch how PolicyLayer validates each transaction![/dim]",
        title="[bold green]Chat Mode Tips[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(help_panel)
    console.print()


def display_policy_status():
    """Display PolicyLayer status"""
    status_panel = Panel(
        "[bold green]✅ PolicyLayer is Active![/bold green]\n\n"
        "[yellow]All transactions will be validated before execution.[/yellow]\n"
        "[dim]Protected against malicious contracts and honeypots.[/dim]",
        border_style="green",
        box=box.ROUNDED
    )
    console.print(status_panel)
    console.print()


def format_agent_message(content, message_type="agent"):
    """Format agent messages with appropriate styling"""
    if message_type == "agent":
        style = "cyan"
        icon = "🤖"
        title = "Agent Response"
    elif message_type == "tool":
        style = "yellow"
        icon = "🔧"
        title = "Tool Output"
    else:
        style = "white"
        icon = "ℹ️"
        title = "Info"

    return Panel(
        content,
        title=f"[bold {style}]{icon} {title}[/bold {style}]",
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 2)
    )


async def run_autonomous_mode(agent_executor, config, interval=10):
    """Run the agent autonomously with specified intervals."""
    console.print("\n[bold green]🚀 Starting Autonomous Mode...[/bold green]\n")

    cycle = 0
    while True:
        try:
            cycle += 1

            # Display cycle header
            console.print(Panel(
                f"[bold cyan]Cycle #{cycle}[/bold cyan]\n"
                f"[dim]Thinking of creative blockchain actions...[/dim]",
                border_style="cyan",
                box=box.ROUNDED
            ))

            # Provide instructions autonomously
            thought = (
                "Be creative and do something interesting on the blockchain. "
                "Choose an action or set of actions and execute it that highlights your abilities."
            )

            # Run agent in autonomous mode using async streaming
            async for chunk in agent_executor.astream(
                {"messages": [HumanMessage(content=thought)]}, config
            ):
                if "agent" in chunk:
                    content = chunk["agent"]["messages"][0].content
                    console.print(format_agent_message(content, "agent"))
                elif "tools" in chunk:
                    content = chunk["tools"]["messages"][0].content
                    console.print(format_agent_message(content, "tool"))

            # Wait before the next action
            console.print(f"\n[dim]⏸️  Waiting {interval} seconds before next cycle...[/dim]\n")
            await asyncio.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n[bold red]👋 Goodbye Agent![/bold red]")
            sys.exit(0)


async def run_chat_mode(agent_executor, config):
    """Run the agent interactively based on user input."""
    console.print("\n[bold green]💬 Starting Chat Mode...[/bold green]")
    console.print("[dim]Type 'exit' to end the conversation.[/dim]\n")

    display_chat_help()

    while True:
        try:
            # Get user input with styled prompt
            user_input = Prompt.ask(
                "\n[bold cyan]You[/bold cyan]",
                default=""
            )

            if user_input.lower() == "exit":
                console.print("\n[bold yellow]👋 Thanks for chatting! Goodbye![/bold yellow]")
                break

            if not user_input.strip():
                continue

            # Show processing indicator
            console.print()
            with console.status("[bold cyan]🤔 Agent is thinking...[/bold cyan]", spinner="dots"):
                # Small delay for visual effect
                await asyncio.sleep(0.5)

            # Run agent with the user's input in chat mode using async streaming
            async for chunk in agent_executor.astream(
                {"messages": [HumanMessage(content=user_input)]}, config
            ):
                if "agent" in chunk:
                    content = chunk["agent"]["messages"][0].content
                    console.print(format_agent_message(content, "agent"))
                elif "tools" in chunk:
                    content = chunk["tools"]["messages"][0].content
                    console.print(format_agent_message(content, "tool"))

        except KeyboardInterrupt:
            console.print("\n[bold red]👋 Goodbye Agent![/bold red]")
            sys.exit(0)
        except Exception as e:
            console.print(Panel(
                f"[bold red]❌ Error:[/bold red]\n{str(e)}",
                border_style="red",
                box=box.ROUNDED
            ))


def choose_mode():
    """Choose whether to run in autonomous or chat mode based on user input."""
    while True:
        display_mode_menu()

        choice = Prompt.ask(
            "[bold cyan]Choose a mode[/bold cyan]",
            choices=["1", "2", "chat", "auto"],
            default="1"
        ).lower().strip()

        if choice in ["1", "chat"]:
            return "chat"
        elif choice in ["2", "auto"]:
            return "auto"


async def main():
    # Load environment variables
    load_dotenv()

    # Display banner
    display_banner()

    # Show initialization status
    with console.status("[bold cyan]🔧 Initializing agent with PolicyLayer...[/bold cyan]", spinner="dots"):
        # Initialize the agent with policy layer
        agent_executor, agent_config = setup(use_policy_layer=True)
        time.sleep(0.5)  # Small delay for visual effect

    console.print("[bold green]✅ Agent initialized successfully![/bold green]\n")

    # Display policy status
    display_policy_status()

    # Run the agent in the selected mode
    mode = choose_mode()

    if mode == "chat":
        await run_chat_mode(agent_executor=agent_executor, config=agent_config)
    elif mode == "auto":
        interval = Prompt.ask(
            "\n[bold cyan]Interval between actions (seconds)[/bold cyan]",
            default="10"
        )
        try:
            interval = int(interval)
        except ValueError:
            interval = 10
            console.print("[yellow]⚠️  Invalid interval, using default (10 seconds)[/yellow]")

        await run_autonomous_mode(
            agent_executor=agent_executor,
            config=agent_config,
            interval=interval
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]👋 Shutting down...[/bold red]")
        sys.exit(0)
