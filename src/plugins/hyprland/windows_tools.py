from typing import Union

from .hyprland import (
    _move_window,
    _resize_window,
    _focus_window,
    _close_window,
    _toggle_fullscreen,
    _toggle_floating,
    _toggle_pin,
    _move_to_workspace,
    _move_to_workspace_silent,
    _switch_workspace,
    HyprlandDesktop,
)

from src.modules.init_system import get_mcp

mcp = get_mcp()


@mcp.tool(name="Window-Move")
def move_window(window_id: str, position_x: int, position_y: int) -> None:
    """
    Moves window to specified absolute screen position. Arguments: window_id(hex address like 0x55a8...), position_x, position_y.
    Note: In Hyprland tiled windows are positioned by the layout. If the target window is tiled it will be promoted to floating before being moved.
    Keywords: Hyprland, Wayland, window, window_move, window_manager, Linux-MCP
    """
    _move_window(window_id, position_x, position_y)


@mcp.tool(name="Window-Resize")
def resize_window(window_id: str, width: int, height: int) -> None:
    """
    Resizes window to exact pixel dimensions. Arguments: window_id(hex address), width, height.
    Works on both tiled and floating windows.
    Keywords: Hyprland, Wayland, window, window_resize, resize, window_manager, Linux-MCP
    """
    _resize_window(window_id, width, height)


@mcp.tool(name="Window-Focus")
def focus_window(window_id: str) -> None:
    """
    Sets window focused (and switches to its workspace if needed). Arguments: window_id(hex address).
    Keywords: Hyprland, Wayland, window, window_focus, focus, window_manager, Linux-MCP
    """
    _focus_window(window_id)


@mcp.tool(name="Window-Close")
def close_window(window_id: str) -> None:
    """
    Sends close signal to window. Arguments: window_id(hex address).
    Important: Tool not guarantee that window will be closed. App can ask confirmation or ignore signal.
    Keywords: Hyprland, Wayland, window, window_close, close, stop, window_manager, Linux-MCP
    """
    _close_window(window_id)


@mcp.tool(name="Window-Toggle-Fullscreen")
def toggle_fullscreen_window(window_id: str) -> None:
    """
    Toggles fullscreen state of the window and sets it focused. Arguments: window_id(hex address).
    Keywords: Hyprland, Wayland, window, window_focus, focus, window_resize, resize, window_manager, fullscreen, screen, Linux-MCP
    """
    _toggle_fullscreen(window_id)


@mcp.tool(name="Window-Toggle-Floating")
def toggle_floating_window(window_id: str) -> None:
    """
    Toggles floating/tiled state of the window. Hyprland-specific: lets the window escape the tiling layout (or rejoin it).
    Arguments: window_id(hex address).
    Keywords: Hyprland, Wayland, window, floating, tiling, layout, window_manager, Linux-MCP
    """
    _toggle_floating(window_id)


@mcp.tool(name="Window-Toggle-Pin")
def toggle_pin_window(window_id: str) -> None:
    """
    Pins or unpins a floating window so it stays visible across all workspace switches.
    Arguments: window_id(hex address).
    Note: Only works on floating windows. Use Window-Toggle-Floating first if needed.
    Keywords: Hyprland, Wayland, window, pin, sticky, always_on_top, workspaces, Linux-MCP
    """
    _toggle_pin(window_id)


@mcp.tool(name="Window-Move-To-Workspace")
def move_window_to_workspace(window_id: str, workspace: str, follow: bool = True) -> None:
    """
    Move window to the specified workspace.

    Arguments:
        window_id: hex address of the window
        workspace: workspace identifier — number ('1'..'10'), name ('special:scratch'),
                   or relative ('+1', '-1', 'e+1', 'e-1' for the next/previous existing workspace)
        follow: if True (default), focus follows the window to that workspace; if False the window moves silently.

    Keywords: Hyprland, Wayland, window, workspace, move, Linux-MCP
    """
    if follow:
        _move_to_workspace(window_id, workspace)
    else:
        _move_to_workspace_silent(window_id, workspace)


@mcp.tool(name="Workspace-Switch")
def switch_workspace(workspace: str) -> None:
    """
    Switch to the specified workspace on the current monitor.

    Arguments:
        workspace: workspace identifier — number ('1'..'10'), name ('special:scratch'),
                   or relative ('+1', '-1', 'e+1', 'e-1', 'previous').

    Keywords: Hyprland, Wayland, workspace, switch, navigation, Linux-MCP
    """
    _switch_workspace(workspace)


@mcp.tool(name="Workspace-List")
def list_workspaces() -> str:
    """
    Returns the list of currently existing workspaces with their monitors and window counts as JSON.
    Keywords: Hyprland, Wayland, workspace, list, info, Linux-MCP
    """
    import json
    desktop = HyprlandDesktop()
    return json.dumps(
        [
            {
                "id": ws.get("id"),
                "name": ws.get("name"),
                "monitor": ws.get("monitor"),
                "windows": ws.get("windows"),
                "has_fullscreen": ws.get("hasfullscreen"),
                "last_window_title": ws.get("lastwindowtitle"),
            }
            for ws in desktop.workspaces
        ],
        indent=2,
    )
