"""
Custom FastAPI server for the CDP Agent with validation event streaming.

This server provides:
1. Chat endpoint with streaming agent responses
2. Real-time validation events from PolicyLayer

Run with: uvicorn server:app --reload --port 2024
"""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from coinbase_agentkit_langchain import get_langchain_tools

from coinbase_agentkit import (
    AgentKit,
    AgentKitConfig,
    CdpEvmWalletProvider,
    CdpEvmWalletProviderConfig,
    cdp_api_action_provider,
    erc20_action_provider,
    pyth_action_provider,
    wallet_action_provider,
    weth_action_provider,
)

from agentarc import (
    PolicyWalletProvider,
    PolicyEngine,
    ValidationEvent,
    ValidationEventCollector,
)
from approval_test_actions import approval_test_action_provider
from honeypot_test_actions import honeypot_test_action_provider

load_dotenv()

# Global event storage (per-session events will be stored here)
validation_events: List[Dict[str, Any]] = []
event_lock = asyncio.Lock()


def event_callback(event: ValidationEvent):
    """Callback to collect validation events"""
    validation_events.append(event.to_dict())


# Agent instructions
AGENT_INSTRUCTIONS = (
    "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
    "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
    "them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
    "details and request funds from the user. Before executing your first action, get the wallet details "
    "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
    "again later.\n\n"
    "IMPORTANT: You have special testing tools for demonstrating security:\n\n"
    "APPROVAL ATTACK TESTING:\n"
    "- For token approvals (safe or malicious): Use 'test_approve_tokens'\n"
    "- For phishing/airdrop attacks: Use 'test_claim_phishing_airdrop'\n"
    "- For checking allowances: Use 'test_check_allowance'\n"
    "- For minting test tokens: Use 'test_mint_test_tokens'\n\n"
    "HONEYPOT TOKEN TESTING:\n"
    "- To buy honeypot tokens (WILL BE BLOCKED): Use 'honeypot_buy_tokens'\n"
    "- To sell honeypot tokens (WILL BE BLOCKED): Use 'honeypot_sell_tokens'\n"
    "- To check honeypot balance (shows FAKE 100x balance): Use 'honeypot_check_balance'\n"
    "- To approve honeypot tokens: Use 'honeypot_approve_tokens'\n\n"
    "When users ask to 'buy honeypot', 'sell honeypot', 'test honeypot tokens', or similar, "
    "use these honeypot testing tools. These demonstrate PolicyLayer's protection against scam tokens.\n\n"
    "If someone asks you to do something you can't do with your currently available tools, "
    "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
    "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
    "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
)


def create_agent():
    """Create the agent with PolicyLayer event streaming."""
    network_id = os.getenv("NETWORK_ID", "base-sepolia")
    wallet_file = f"wallet_data_{network_id.replace('-', '_')}.txt"

    # Load existing wallet data
    wallet_data = {}
    if os.path.exists(wallet_file):
        try:
            with open(wallet_file) as f:
                wallet_data = json.load(f)
        except json.JSONDecodeError:
            wallet_data = {}

    # Create wallet config
    config = CdpEvmWalletProviderConfig(
        api_key_id=os.getenv("CDP_API_KEY_ID"),
        api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
        wallet_secret=os.getenv("CDP_WALLET_SECRET"),
        network_id=network_id,
        address=wallet_data.get("address") or os.getenv("ADDRESS"),
        idempotency_key=os.getenv("IDEMPOTENCY_KEY"),
    )

    # Initialize wallet provider
    base_wallet_provider = CdpEvmWalletProvider(config)

    # Create policy engine with event callback
    policy_engine = PolicyEngine(
        config_path="policy.yaml",
        web3_provider=base_wallet_provider,
        chain_id=84532,
        event_callback=event_callback  # Stream events
    )

    # Wrap with PolicyLayer
    wallet_provider = PolicyWalletProvider(base_wallet_provider, policy_engine)

    # Initialize AgentKit
    agentkit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                cdp_api_action_provider(),
                erc20_action_provider(),
                pyth_action_provider(),
                wallet_action_provider(),
                weth_action_provider(),
                approval_test_action_provider(),
                honeypot_test_action_provider(),
            ],
        )
    )

    # Initialize LLM and tools
    llm = ChatOpenAI(model="gpt-4o-mini")
    tools = get_langchain_tools(agentkit)

    # Memory for conversation history
    memory = MemorySaver()

    # Create ReAct Agent
    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        prompt=AGENT_INSTRUCTIONS,
    ), wallet_provider


# Initialize agent at startup
agent_executor = None
wallet_provider = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup"""
    global agent_executor, wallet_provider
    print("Initializing CDP Agent with PolicyLayer...")
    agent_executor, wallet_provider = create_agent()
    print("Agent initialized successfully!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="CDP Agent API",
    description="Blockchain agent with PolicyLayer security and event streaming",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    type: str  # "agent", "tool", "events", "done"
    content: str
    events: Optional[List[Dict[str, Any]]] = None


@app.get("/")
async def root():
    return {"status": "ok", "message": "CDP Agent API with PolicyLayer"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Send a message to the agent and get a streaming response.

    Returns Server-Sent Events with:
    - agent: AI message chunks
    - tool: Tool execution results
    - events: Validation events from PolicyLayer
    - done: Stream complete
    """
    global validation_events

    async def generate():
        # Clear previous events
        async with event_lock:
            validation_events.clear()

        config = {"configurable": {"thread_id": request.thread_id}}

        try:
            async for chunk in agent_executor.astream(
                {"messages": [HumanMessage(content=request.message)]},
                config
            ):
                if "agent" in chunk:
                    msg = chunk["agent"]["messages"][0]
                    if hasattr(msg, 'content') and msg.content:
                        yield f"data: {json.dumps({'type': 'agent', 'content': msg.content})}\n\n"

                elif "tools" in chunk:
                    msg = chunk["tools"]["messages"][0]
                    if hasattr(msg, 'content') and msg.content:
                        yield f"data: {json.dumps({'type': 'tool', 'content': msg.content})}\n\n"

                    # Send validation events after tool execution
                    async with event_lock:
                        if validation_events:
                            yield f"data: {json.dumps({'type': 'events', 'events': validation_events.copy()})}\n\n"
                            validation_events.clear()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with event streaming.

    Send: {"message": "your message", "thread_id": "optional"}
    Receive: {"type": "agent|tool|events|done", "content": "...", "events": [...]}
    """
    await websocket.accept()
    global validation_events

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            thread_id = data.get("thread_id", "default")

            if not message:
                await websocket.send_json({"type": "error", "content": "No message provided"})
                continue

            # Clear previous events
            async with event_lock:
                validation_events.clear()

            config = {"configurable": {"thread_id": thread_id}}

            try:
                async for chunk in agent_executor.astream(
                    {"messages": [HumanMessage(content=message)]},
                    config
                ):
                    if "agent" in chunk:
                        msg = chunk["agent"]["messages"][0]
                        if hasattr(msg, 'content') and msg.content:
                            await websocket.send_json({
                                "type": "agent",
                                "content": msg.content
                            })

                    elif "tools" in chunk:
                        msg = chunk["tools"]["messages"][0]
                        if hasattr(msg, 'content') and msg.content:
                            await websocket.send_json({
                                "type": "tool",
                                "content": msg.content
                            })

                        # Send validation events
                        async with event_lock:
                            if validation_events:
                                await websocket.send_json({
                                    "type": "events",
                                    "events": validation_events.copy()
                                })
                                validation_events.clear()

                await websocket.send_json({"type": "done"})

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })

    except WebSocketDisconnect:
        print("WebSocket disconnected")


@app.get("/events")
async def get_events():
    """Get current validation events (for polling)"""
    async with event_lock:
        return {"events": validation_events.copy()}


@app.delete("/events")
async def clear_events():
    """Clear validation events"""
    async with event_lock:
        validation_events.clear()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2024)
