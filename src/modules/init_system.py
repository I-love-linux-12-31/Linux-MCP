from mcp.server.fastmcp import FastMCP

__mcp: FastMCP = None


def init():
    global __mcp
    __mcp = FastMCP(name="Linux-MCP server")


def get_mcp() -> FastMCP:
    if not __mcp:
        init()
    return __mcp
