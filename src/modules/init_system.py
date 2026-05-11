import os
from mcp.server.fastmcp import FastMCP, server

__mcp: FastMCP = None


def init():
    global __mcp

    __mcp = FastMCP(
        name="Linux-MCP server",
        host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("FASTMCP_PORT", 7447)),
    )


def get_mcp() -> FastMCP:
    if not __mcp:
        init()
    return __mcp
