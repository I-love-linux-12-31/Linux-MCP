import os
import pyautogui
import subprocess
from typing import Literal
from mcp.types import TextContent, CallToolResult

from src.modules.init_system import get_mcp

mcp = get_mcp()


@mcp.tool(name="Wait")
def wait(seconds: float = 1.5) -> None:
    """
    Pause execution for specified duration in seconds and do nothing. Default = 1.5.
    Useful for waiting for applications start or other long action complete.
    Keywords: Wait, pause, sleep, Linux-MCP
    """
    pyautogui.sleep(seconds)


@mcp.tool(name="Call-To-Open-URI")
def call_to_open_uri(uri: str) -> dict[str, str | int]:
    """
    Calls to open uri(file, directory, web-site...) with associated application.
    Default is file/directory.
    To call opening of other uri(website, ssh or ftp connection) you need specify protocol like:
    uri='http://example.com/1/2/3', uri='file:///home/user/file.txt', uri='ssh://192.168.0.123', mailto://user@example.com, etc.
    Keywords: Call, open, xdg-open, Linux-MCP
    """
    result = subprocess.run(["xdg-open", uri], capture_output=True, text=True)

    response = {"statuscode": result.returncode, "comment": result.stdout, "error_message": result.stderr}
    if result.returncode != 0:
        raise RuntimeError(response)
    return response
