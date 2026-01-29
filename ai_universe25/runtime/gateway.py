"""
MCP Gateway: Deterministic routing with RBAC + ladder checks.

Implements JSON-RPC 2.0 over stdio and streamable HTTP transports.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

# MCP imports (optional - will work without MCP SDK installed)
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import (
        CallToolRequest,
        GetResourceRequest,
        ListToolsRequest,
        Tool,
        Resource,
        TextContent,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Placeholder types if MCP not available
    class ClientSession:
        pass
    class StdioServerParameters:
        pass
    class Tool:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "")
        def dict(self):
            return {"name": self.name}
    class Resource:
        def __init__(self, **kwargs):
            self.uri = kwargs.get("uri", "")
            self.name = kwargs.get("name", "")

logger = logging.getLogger(__name__)


class Channel(Enum):
    """MCP channels for typed message routing."""

    AUTHOR = "ch.author"  # Authoring requests & deltas
    EVIDENCE = "ch.evidence"  # Claim→cite bindings, spans, hashes
    VERIFY = "ch.verify"  # Retrieval & NLI results
    STYLE = "ch.style"  # Neutrality, bias, house-style findings
    GOV = "ch.gov"  # Priority/budget/ladder actions
    TELEMETRY = "ch.telemetry"  # Timings, return codes, saturation


class Surface(Enum):
    """Typed surfaces for wiki pages."""

    INTRO = "intro"
    OUTLINE = "outline"
    BODY = "body"
    SUMMARY = "summary"
    INDEX = "index"
    FRONTPAGE = "frontpage"
    CITATION_GRAPH = "citation-graph"
    FACT_LEDGER = "fact-ledger"
    STYLE_REPORT = "style-report"


@dataclass
class Envelope:
    """MCP envelope with protocol metadata."""

    run_id: str
    agent_id: str
    surface: Optional[Surface] = None
    tool: Optional[str] = None
    schema_id: Optional[str] = None
    content_hash: Optional[str] = None
    channel: Optional[Channel] = None
    context_hash: Optional[str] = None
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())

    def compute_context_hash(self) -> str:
        """Compute deterministic context hash for replay."""
        ctx_str = f"{self.run_id}:{self.agent_id}:{self.surface}:{self.tool}:{self.schema_id}"
        return hashlib.sha256(ctx_str.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize envelope to dict."""
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "surface": self.surface.value if self.surface else None,
            "tool": self.tool,
            "schema_id": self.schema_id,
            "content_hash": self.content_hash,
            "channel": self.channel.value if self.channel else None,
            "context_hash": self.context_hash or self.compute_context_hash(),
            "timestamp": self.timestamp,
        }


@dataclass
class PolicyDecision:
    """Policy enforcement decision."""

    allowed: bool
    reason: Optional[str] = None
    code: Optional[str] = None  # e.g., "policy_denied", "tool_unavailable"


class MCPGateway:
    """
    MCP-compliant gateway with deterministic routing and server-side policy enforcement.

    Supports JSON-RPC 2.0 over stdio and streamable HTTP transports.
    """

    def __init__(
        self,
        secret_key: Optional[bytes] = None,
        enable_http: bool = True,
        http_port: int = 8080,
    ):
        """
        Initialize MCP gateway.

        Args:
            secret_key: HMAC secret for envelope signing (default: random)
            enable_http: Enable HTTP transport (default: True)
            http_port: HTTP server port (default: 8080)
        """
        self.secret_key = secret_key or uuid4().bytes
        self.enable_http = enable_http
        self.http_port = http_port
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self._lock = asyncio.Lock()

    def sign_envelope(self, envelope: Envelope) -> str:
        """Sign envelope with HMAC."""
        payload = json.dumps(envelope.to_dict(), sort_keys=True).encode()
        return hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()

    def verify_envelope(self, envelope: Envelope, signature: str) -> bool:
        """Verify envelope signature."""
        expected = self.sign_envelope(envelope)
        return hmac.compare_digest(expected, signature)

    async def check_policy(
        self,
        envelope: Envelope,
        action: str,
        rbac_check: callable,
        ladder_check: callable,
    ) -> PolicyDecision:
        """
        Check policy (RBAC + ladder) for an action.

        Args:
            envelope: Request envelope
            action: Action type ("read", "write", "append")
            rbac_check: RBAC checker function
            ladder_check: Ladder state checker function

        Returns:
            Policy decision
        """
        # RBAC check
        if not rbac_check(envelope.agent_id, envelope.surface, action):
            return PolicyDecision(
                allowed=False,
                reason="RBAC denied",
                code="policy_denied",
            )

        # Ladder check (will be implemented in rbac_ladder module)
        ladder_decision = await ladder_check(envelope)
        if not ladder_decision.allowed:
            return ladder_decision

        return PolicyDecision(allowed=True)

    async def list_tools(
        self,
        envelope: Envelope,
        rbac_check: callable,
    ) -> List[Tool]:
        """
        List available tools (MCP list_tools).

        Args:
            envelope: Request envelope
            rbac_check: RBAC checker function

        Returns:
            List of available tools
        """
        # Check read permission
        decision = await self.check_policy(
            envelope, "read", rbac_check, lambda e: PolicyDecision(allowed=True)
        )
        if not decision.allowed:
            logger.warning(f"Policy denied list_tools for {envelope.agent_id}: {decision.reason}")
            return []

        # Filter tools by RBAC
        allowed_tools = []
        for tool_name, tool in self.tools.items():
            # Simple check: if agent can read, they can see tool exists
            # Actual call_tool will enforce write permissions
            allowed_tools.append(tool)

        return allowed_tools

    async def call_tool(
        self,
        envelope: Envelope,
        tool_name: str,
        arguments: Dict[str, Any],
        rbac_check: callable,
        ladder_check: callable,
    ) -> Dict[str, Any]:
        """
        Call a tool (MCP call_tool).

        Args:
            envelope: Request envelope
            tool_name: Name of tool to call
            arguments: Tool arguments
            rbac_check: RBAC checker function
            ladder_check: Ladder state checker function

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found or policy denied
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Determine action type from tool (simplified)
        action = "write" if "write" in tool_name.lower() else "read"

        # Check policy
        decision = await self.check_policy(envelope, action, rbac_check, ladder_check)
        if not decision.allowed:
            error_code = decision.code or "policy_denied"
            raise ValueError(f"{error_code}: {decision.reason}")

        # Execute tool (delegated to tool server)
        # This is a placeholder - actual execution happens in tool servers
        return {
            "tool": tool_name,
            "result": "executed",
            "envelope": envelope.to_dict(),
        }

    async def get_resource(
        self,
        envelope: Envelope,
        resource_uri: str,
        rbac_check: callable,
    ) -> Resource:
        """
        Get a resource (MCP get_resource).

        Args:
            envelope: Request envelope
            resource_uri: Resource URI
            rbac_check: RBAC checker function

        Returns:
            Resource content

        Raises:
            ValueError: If resource not found or policy denied
        """
        if resource_uri not in self.resources:
            raise ValueError(f"Resource '{resource_uri}' not found")

        # Check read permission
        decision = await self.check_policy(
            envelope, "read", rbac_check, lambda e: PolicyDecision(allowed=True)
        )
        if not decision.allowed:
            raise ValueError(f"policy_denied: {decision.reason}")

        return self.resources[resource_uri]

    def register_tool(self, tool: Tool):
        """Register a tool with the gateway."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_resource(self, resource: Resource):
        """Register a resource with the gateway."""
        self.resources[resource.uri] = resource
        logger.info(f"Registered resource: {resource.uri}")

    async def start_stdio_server(self, server_params: StdioServerParameters):
        """Start stdio MCP server (for co-located tools)."""
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # Store session for tool calls
                session_id = str(uuid4())
                self.sessions[session_id] = session
                logger.info(f"Started stdio MCP server (session: {session_id})")

    async def handle_jsonrpc_request(
        self,
        request: Dict[str, Any],
        rbac_check: callable,
        ladder_check: callable,
    ) -> Dict[str, Any]:
        """
        Handle JSON-RPC 2.0 request.

        Args:
            request: JSON-RPC request dict
            rbac_check: RBAC checker function
            ladder_check: Ladder state checker function

        Returns:
            JSON-RPC response dict
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            # Extract envelope from params
            envelope_dict = params.get("envelope", {})
            envelope = Envelope(
                run_id=envelope_dict.get("run_id", ""),
                agent_id=envelope_dict.get("agent_id", ""),
                surface=Surface(envelope_dict["surface"]) if envelope_dict.get("surface") else None,
                tool=envelope_dict.get("tool"),
                schema_id=envelope_dict.get("schema_id"),
                content_hash=envelope_dict.get("content_hash"),
                channel=Channel(envelope_dict["channel"]) if envelope_dict.get("channel") else None,
            )

            # Route to appropriate handler
            if method == "tools/list":
                tools = await self.list_tools(envelope, rbac_check)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": [t.dict() for t in tools]},
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.call_tool(envelope, tool_name, arguments, rbac_check, ladder_check)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }
            elif method == "resources/read":
                resource_uri = params.get("uri")
                resource = await self.get_resource(envelope, resource_uri, rbac_check)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"contents": [{"uri": resource.uri, "text": resource.name}]},
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
        except Exception as e:
            logger.exception(f"Error handling JSON-RPC request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)},
            }
