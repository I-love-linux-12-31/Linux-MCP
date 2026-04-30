from wayland_automation import Mouse
from typing import Literal
from time import sleep

from src.modules.init_system import get_mcp

mcp = get_mcp()


@mcp.tool(name="Cursor-Move")
def move(x: int, y: int, duration: float = 0) -> None:
    """
    Moves mouse cursor to specific position by absolute coordinates(x, y).
    Note: Not all of DEs are supported.

    Keywords: cursor, move, cursor_move, mouse, mouse_move, pointer, coordinate, mousemove, wayland, Linux-MCP
    """
    mouse = Mouse()
    mouse.click(x, y, button="nothing")


@mcp.tool(name="Cursor-Click-Wayland")
def click_wa(x: int, y: int, button: Literal['left','right','middle'] = 'left', clicks_count: int = 1) -> None:
    """
    Does cursor click(s) with specific button(left/right/middle).
    By default, clicks_count = 1.

    Note: Not all of DEs are supported.

    Keywords: cursor, move, cursor_click, mouse, mouse_click, click, left click, right click, double click, press, wayland, Linux-MCP
    """
    mouse = Mouse()
    for _ in range(clicks_count):
        mouse.click(x, y, button=button)
        sleep(0.05)


# @mcp.tool(name="Cursor-Drag-And-Drop")
# def drag_and_drop(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
#     """
#     Process drag and drop between points by absolute coordinates.
#     Duration of movement is optional. Default = 0.5.
#     Use duration value for slow movements or in application with mouse grab.
#     Keywords: cursor, move, cursor_move, mouse, mouse_move, drag&drop, drag_and_drop, pointer, coordinate, mousemove, Linux-MCP
#     """
#     raise NotImplementedError("This functional is not supported by wayland_automation yet.")
#     pyautogui.moveTo(start_x, start_y, duration=duration / 2)
#     pyautogui.mouseDown()
#     pyautogui.dragTo(end_x, end_y, duration=duration)
#     pyautogui.mouseUp()


# @mcp.tool(name="Cursor-Get-Position")
# def get_position() -> tuple[int, int]:
#     """
#     Returns current position of mouse cursor (x, y).
#     Keywords: cursor, move, cursor_position, mouse, mouse_position, position, location, pointer, coordinate, Linux-MCP
#     """
#     raise NotImplementedError("This functional is not supported by wayland_automation yet.")
#     x, y = pyautogui.position()
#     return x, y
