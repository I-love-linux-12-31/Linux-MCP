import pyautogui
from typing import Literal

from src.modules.init_system import get_mcp

mcp = get_mcp()


@mcp.tool(name="Cursor-Move")
def move(x: int, y: int, duration: float = 0) -> None:
    """
    Moves mouse cursor to specific position by absolute coordinates(x, y).
    Duration of movement is optional. Default = 0.0.
    Use duration value for slow movements or in application with mouse grab.
    """
    pyautogui.moveTo(x, y, duration=duration)


@mcp.tool(name="Cursor-Click")
def click(button: Literal['left','right','middle'] = 'left', clicks_count: int = 1) -> None:
    """
    Does cursor click(s) with specific button(left/right/middle).
    By default, clicks_count = 1.
    """
    pyautogui.click(button=button, clicks=clicks_count)
    # todo: maybe I should add integration with apps(return, what element was clicked).


@mcp.tool(name="Cursor-Drag-And-Drop")
def drag_and_drop(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
    """
    Process drag and drop between points by absolute coordinates.
    Duration of movement is optional. Default = 0.5.
    Use duration value for slow movements or in application with mouse grab.
    """
    pyautogui.moveTo(start_x, start_y, duration=duration / 2)
    pyautogui.mouseDown()
    pyautogui.dragTo(end_x, end_y, duration=duration)
    pyautogui.mouseUp()


@mcp.tool(name="Cursor-Get-Position")
def get_position() -> tuple[int, int]:
    """
    Returns current position of mouse cursor (x, y).
    """
    x, y = pyautogui.position()
    return x, y
