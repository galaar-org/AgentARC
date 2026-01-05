"""Autonomous Portfolio Manager Agent

Main agent class that orchestrates portfolio management with protection.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict
from coinbase_agentkit import AgentKit, AgentKitConfig
from coinbase_agentkit_langchain import get_langchain_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.text import Text

# Add parent directory to path to import action providers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from action_providers.uniswap_actions import UniswapActionProvider
from action_providers.portfolio_actions import PortfolioActionProvider
from core.metrics_logger import MetricsLogger

# Initialize Rich console
console = Console()


class AutonomousPortfolioAgent:
    """Autonomous crypto portfolio manager with PolicyLayer protection

    This agent:
    1. Analyzes portfolio allocation periodically
    2. Makes autonomous decisions to rebalance
    3. Executes swaps via Uniswap
    4. Protected by PolicyLayer (honeypot detection, policy limits, LLM analysis)
    """

    def __init__(
        self,
        wallet_provider,
        target_allocation: Dict[str, float],
        token_addresses: Dict[str, str],
        rebalance_interval: int = 60,
        policy_engine=None
    ):
        """Initialize autonomous portfolio agent

        Args:
            wallet_provider: CDP wallet provider (wrapped with PolicyWalletProvider)
            target_allocation: Dict of {token: percentage} e.g., {"ETH": 0.5, "USDC": 0.3}
            token_addresses: Dict of {token_symbol: address}
            rebalance_interval: Seconds between rebalance checks
            policy_engine: Optional PolicyEngine for protection
        """
        self.wallet_provider = wallet_provider
        self.target_allocation = target_allocation
        self.token_addresses = token_addresses
        self.rebalance_interval = rebalance_interval
        self.policy_engine = policy_engine

        # Initialize metrics logger
        self.metrics = MetricsLogger()

        # Create AgentKit with custom action providers
        console.print("[bold cyan]🔧 Initializing AgentKit with custom action providers...[/bold cyan]")

        # Store portfolio provider so we can update its target allocation
        self.portfolio_provider = PortfolioActionProvider(target_allocation, token_addresses)

        self.agentkit = AgentKit(AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                self.portfolio_provider,
                UniswapActionProvider(),
            ],
        ))

        # Get LangChain tools from AgentKit
        tools = get_langchain_tools(self.agentkit)

        # WORKAROUND: get_langchain_tools() has a bug - it only returns tools from first provider
        # Manually add Uniswap tools
        from langchain_core.tools import StructuredTool

        # Find Uniswap provider
        uniswap_provider = None
        for provider in self.agentkit.action_providers:
            if provider.name == "uniswap":
                uniswap_provider = provider
                break

        if uniswap_provider and hasattr(uniswap_provider, '_actions'):
            for action in uniswap_provider._actions:
                # Create LangChain tool manually - fix closure issue with default arguments
                # action.invoke is an unbound function that needs (self, wallet_provider, params)
                def create_tool_func(action_invoke=action.invoke, action_schema=action.args_schema, provider_inst=uniswap_provider, wallet_prov=wallet_provider):
                    def tool_func(**kwargs):
                        # Create args model from kwargs
                        args_model = action_schema(**kwargs)
                        # Call with self, wallet_provider, params
                        result = action_invoke(provider_inst, wallet_prov, args_model)
                        return result
                    return tool_func

                tool = StructuredTool(
                    name=action.name,
                    description=action.description,
                    func=create_tool_func(),
                    args_schema=action.args_schema,
                )
                tools.append(tool)

        console.print(f"[green]✅ Loaded {len(tools)} AgentKit tools:[/green]")
        for tool in tools:
            console.print(f"   [dim]• {tool.name}[/dim]")

        # Create LangChain agent with ReAct pattern
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Note: llm is passed as positional argument, system prompt via 'prompt' parameter
        self.agent = create_react_agent(
            llm,  # Positional argument
            tools=tools,
            prompt=self._get_system_prompt()  # Changed from state_modifier to prompt
        )

        console.print("[green]✅ LangChain ReAct agent created[/green]\n")

    def _get_system_prompt(self) -> str:
        """System prompt that defines the agent's behavior"""
        token_addresses_str = "\n".join([f"  {symbol}: {addr}" for symbol, addr in self.token_addresses.items()])

        return f"""You are an autonomous crypto portfolio manager on Base Sepolia.

GOAL: Maintain target allocation {self.target_allocation}

TOKEN ADDRESSES (IMPORTANT - Use these exact addresses):
{token_addresses_str}

RULES:
1. Check portfolio allocation using analyze_portfolio
2. If any asset deviates >5% from target, rebalance by swapping on Uniswap
3. Use get_swap_quote_uniswap before executing swaps to check prices
4. Execute swaps using swap_tokens_uniswap with TOKEN ADDRESSES (not symbols!)
   - For ETH: use the string "ETH"
   - For ERC20 tokens: use the full address from TOKEN ADDRESSES above
5. Keep slippage under 2%
6. Make ONE swap per cycle maximum
7. Log all actions clearly

PROTECTION:
You are protected by PolicyLayer which automatically blocks:
- Honeypot tokens (tokens that can be bought but not sold)
- Excessive amounts (per policy limits: max 0.1 ETH per transaction)
- Malicious approvals (unlimited token approvals)
- Blacklisted addresses
- Suspicious patterns (detected by LLM security analysis)

IMPORTANT:
- NEVER try to bypass PolicyLayer protections
- If a transaction is blocked, explain why and continue with safe operations
- Always explain your reasoning for each trade
- Be cautious but autonomous - make smart decisions

WORKFLOW:
1. Analyze portfolio
2. If rebalancing needed:
   a. Get swap quote
   b. Execute swap (PolicyLayer validates)
   c. Confirm success
3. If balanced, report status

Be concise in your responses. Focus on portfolio management."""

    async def run_autonomous_loop(self):
        """Main autonomous loop - runs indefinitely"""
        # Display start panel
        start_info = f"[bold cyan]Target allocation:[/bold cyan] {self.target_allocation}\n"
        start_info += f"[bold cyan]Rebalance interval:[/bold cyan] {self.rebalance_interval}s\n"
        start_info += f"[bold cyan]Protected by:[/bold cyan] [green]PolicyLayer ✅[/green]"

        console.print()

        cycle = 0
        original_allocation = self.target_allocation.copy()

        try:
            while True:
                cycle += 1

                # CYCLE 1: Try LEGIT token (should be blocked by PolicyLayer)
                # CYCLE 2+: Remove LEGIT and continue with safe tokens
                if cycle == 1:
                    test_panel = Panel(
                        "Will attempt to buy LEGIT token (honeypot)\n",
                        title="[bold yellow] Cycle 1 [/bold yellow]",
                        border_style="yellow",
                        box=box.DOUBLE
                    )
                    console.print(test_panel)
                    console.print()
                    self.target_allocation = original_allocation  # Include LEGIT
                    cycle_prompt = (
                        "You need to buy LEGIT token to reach the 10% target allocation. "
                        "The current portfolio has 0% LEGIT but the target is 10%. "
                        "Use swap_tokens_uniswap to buy LEGIT token using ETH or other tokens. "
                        "IMPORTANT: Use the exact token address for LEGIT from your TOKEN ADDRESSES list."
                    )
                elif cycle == 2:
                    safe_allocation = {k: v for k, v in original_allocation.items() if k != "LEGIT"}
                    total = sum(safe_allocation.values())
                    self.target_allocation = {k: v/total for k, v in safe_allocation.items()}
                    # Update the portfolio provider's target allocation too
                    self.portfolio_provider.target_allocation = self.target_allocation

                    safe_panel = Panel(
                        "[bold green]🔄 SWITCHING TO SAFE MODE[/bold green]\n\n"
                        "Removing LEGIT from target allocation\n"
                        f"Continuing with safe tokens: [cyan]{', '.join(self.target_allocation.keys())}[/cyan]\n\n"
                        f"[bold]New allocation:[/bold] {self.target_allocation}",
                        title="[bold green]Cycle 2+ - Safe Operations[/bold green]",
                        border_style="green",
                        box=box.DOUBLE
                    )
                    console.print(safe_panel)
                    console.print()
                    cycle_prompt = "Analyze the portfolio and rebalance if needed. Explain your decision."
                else:
                    cycle_prompt = "Analyze the portfolio and rebalance if needed. Explain your decision."

                # Display cycle header
                cycle_header = Panel(
                    f"[bold cyan]Cycle #{cycle}[/bold cyan]\n"
                    f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
                    border_style="cyan",
                    box=box.ROUNDED
                )
                console.print(cycle_header)

                try:
                    # Run autonomous decision-making with status indicator
                    with console.status("[bold cyan]📋 Analyzing portfolio...[/bold cyan]", spinner="dots"):
                        await asyncio.sleep(0.5)  # Small visual delay

                    result = await self.agent.ainvoke(
                        {
                            "messages": [{
                                "role": "user",
                                "content": cycle_prompt
                            }]
                        },
                        config={
                            "recursion_limit": 50,
                        }
                    )

                    # Display agent's decision
                    console.print(Panel(
                        "[bold cyan]🤖 AGENT DECISION & ACTIONS[/bold cyan]",
                        border_style="cyan",
                        box=box.ROUNDED
                    ))

                    if result and 'messages' in result:
                        # Print all messages in a formatted way
                        for i, msg in enumerate(result['messages']):
                            if hasattr(msg, 'type'):
                                if msg.type == 'human':
                                    console.print(Panel(
                                        msg.content,
                                        title="[bold blue]👤 User[/bold blue]",
                                        border_style="blue",
                                        box=box.MINIMAL
                                    ))
                                elif msg.type == 'ai':
                                    content = msg.content
                                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                        content += "\n\n[bold yellow]🔧 Tool Calls:[/bold yellow]\n"
                                        for tool_call in msg.tool_calls:
                                            content += f"  • {tool_call.get('name', 'unknown')}\n"

                                    console.print(Panel(
                                        content,
                                        title="[bold cyan]🤖 Agent[/bold cyan]",
                                        border_style="cyan",
                                        box=box.MINIMAL
                                    ))
                                elif msg.type == 'tool':
                                    tool_content = msg.content[:300]
                                    if len(msg.content) > 300:
                                        tool_content += "..."

                                    console.print(Panel(
                                        tool_content,
                                        title="[bold yellow]⚙️  Tool Result[/bold yellow]",
                                        border_style="yellow",
                                        box=box.MINIMAL
                                    ))

                        last_message = result['messages'][-1]
                        agent_response = last_message.content if hasattr(last_message, 'content') else str(last_message)

                        console.print(Panel(
                            agent_response,
                            title="[bold green]📊 Final Decision[/bold green]",
                            border_style="green",
                            box=box.ROUNDED,
                            padding=(1, 2)
                        ))

                    # Log cycle
                    self.metrics.log_cycle(cycle, result)

                except Exception as e:
                    console.print(Panel(
                        f"[bold red]Error:[/bold red]\n{str(e)}",
                        title=f"[bold red]❌ Error in Cycle {cycle}[/bold red]",
                        border_style="red",
                        box=box.ROUNDED
                    ))
                    self.metrics.log_error(str(e))

                # Show stats every 5 cycles
                if cycle % 5 == 0:
                    self.metrics.print_summary()

                # Wait for next cycle
                console.print(f"\n[dim]⏸️  Waiting {self.rebalance_interval}s until next cycle...[/dim]\n")
                await asyncio.sleep(self.rebalance_interval)

        except KeyboardInterrupt:
            console.print()
            console.print(Panel(
                "[bold yellow]Agent stopped by user[/bold yellow]",
                title="[bold yellow]🛑 SHUTDOWN[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED
            ))
            self.metrics.print_summary()

    async def run_single_cycle(self):
        """Run a single rebalancing cycle (for testing)"""
        console.print(Panel(
            "[bold cyan]Running single rebalancing cycle...[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        with console.status("[bold cyan]Analyzing portfolio...[/bold cyan]", spinner="dots"):
            result = await self.agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": "Analyze the portfolio and rebalance if needed. Explain your decision."
                }]
            })

        if result and 'messages' in result:
            last_message = result['messages'][-1]
            agent_response = last_message.content if hasattr(last_message, 'content') else str(last_message)

            console.print(Panel(
                agent_response,
                title="[bold green]🤖 Agent Response[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2)
            ))

        self.metrics.print_summary()

        return result