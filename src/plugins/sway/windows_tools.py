import io
import pyautogui
from typing import Literal

from mcp.types import ImageContent
from mcp.server.fastmcp import Image as MCPImage



from .sway import (
    SwayDesktop,
    SwayWindow,

    _move_window,
    _resize_window,
    _focus_window,
    _close_window,
    _toggle_fullscreen,
)


from src.modules.init_system import get_mcp

mcp = get_mcp()


@mcp.tool(name="Window-Move")
def move_window(window_id, position_x, position_y) -> None:
    """
    Moves window to specified position. Arguments: window_id(in hex form), position_x, position_y.
    Warning: tool doesn't change window priority, focus state or other params!
    """
    _move_window(window_id, position_x, position_y)


@mcp.tool(name="Window-Resize")
def resize_window(window_id, width, height) -> None:
    """
    Resizes window. Arguments: window_id(in hex form), width, height.
    Warning: tool doesn't change window priority, focus state or other params!
    """
    _resize_window(window_id, width, height)


@mcp.tool(name="Window-Focus")
def focus_window(window_id) -> None:
    """
    Sets window focused. Arguments: window_id(in hex form).
    """
    _focus_window(window_id)


@mcp.tool(name="Window-Close")
def close_window(window_id) -> None:
    """
    Sends close signal to window. Arguments: window_id(in hex form).
    Important: Tool not guarantee that window will be closed. App can ask confirmation or ignore signal.
    """
    _close_window(window_id)


@mcp.tool(name="Window-Toggle-Fullscreen")
def toggle_fullscreen_window(window_id) -> None:
    """
    Changes fullscreen state of window and set it focused. Arguments: window_id(in hex form).
    """
    _toggle_fullscreen(window_id)






