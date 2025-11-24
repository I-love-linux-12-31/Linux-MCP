import io
import pyautogui
from typing import Literal

from mcp.types import ImageContent
from mcp.server.fastmcp import Image as MCPImage

from Xlib import X, protocol

from .desktop import X11Desktop, X11Window

# from .windows_interaction import (
#     move_window as _move_window,
#     resize_window as _resize_window,
#     focus_window as _focus_window,
#     close_window as _close_window,
#     toggle_fullscreen as _toggle_fullscreen,
#     # hide_window as _hide_window, # todo: make functional more common.
# )

from src.modules.init_system import get_mcp

mcp = get_mcp()

def _move_window(window_id, x, y):
    """
    Move window to specified position

    Args:
        window_id (str or int): Window ID in hex format (e.g., '0x560012b')
        x (int): X coordinate
        y (int): Y coordinate
    """
    desktop = X11Desktop()
    try:
        window = desktop[window_id]
        window.x11_win.configure(x=x, y=y)
        window.x11_disp.sync()
        print(f"Moved window {window_id} to position ({x}, {y})")
    except Exception as e:
        print(f"Error moving window {window_id}: {e}")
    finally:
        desktop.x11_disp.close()



def _resize_window(window_id, width, height):
    """
    Resize window to specified dimensions

    Args:
        window_id (str or int): Window ID in hex format
        width (int): New width
        height (int): New height
    """
    desktop = X11Desktop()
    try:
        window = desktop[window_id]
        window.x11_win.configure(width=width, height=height)
        window.x11_disp.sync()
        print(f"Resized window {window_id} to {width}x{height}")
    except Exception as e:
        print(f"Error resizing window {window_id}: {e}")
    finally:
        desktop.x11_disp.close()


def _focus_window(window_id):
    """
    Focus (activate) window

    Args:
        window_id (str or int): Window ID in hex format
    """
    desktop = X11Desktop()
    try:
        window = desktop[window_id]

        # Raise window to top
        window.x11_win.configure(stack_mode=X.Above)

        # Set input focus
        window.x11_win.set_input_focus(X.RevertToParent, X.CurrentTime)

        _NET_ACTIVE_WINDOW = window.x11_disp.intern_atom('_NET_ACTIVE_WINDOW')

        event_act = protocol.event.ClientMessage(
            window=window.x11_win,
            client_type=_NET_ACTIVE_WINDOW,
            data=(32, [1, X.CurrentTime, 0, 0, 0])
        )

        mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        window.x11_root.send_event(event_act, event_mask=mask)

        window.x11_disp.sync()
        print(f"Focused window {window_id}")
    except Exception as e:
        print(f"Error focusing window {window_id}: {e}")
    finally:
        desktop.x11_disp.close()


def _close_window(window_id):
    """
    Close window gracefully

    Args:
        window_id (str or int): Window ID in hex format
    """
    desktop = X11Desktop()
    try:
        window = desktop[window_id]

        # Try WM_DELETE_WINDOW protocol first (graceful close)
        protocols = window.x11_win.get_wm_protocols()
        WM_DELETE_WINDOW = desktop.x11_disp.intern_atom('WM_DELETE_WINDOW')

        if WM_DELETE_WINDOW in protocols:
            event = protocol.event.ClientMessage(
                window=window.x11_win,
                client_type=desktop.x11_disp.intern_atom('WM_PROTOCOLS'),
                data=(32, [WM_DELETE_WINDOW, X.CurrentTime, 0, 0, 0])
            )
            window.x11_win.send_event(event)
        else:
            # Force close if WM_DELETE_WINDOW not supported
            window.x11_win.kill_client()

        desktop.x11_disp.sync()
        print(f"Closed window {window_id}")
    except Exception as e:
        print(f"Error closing window {window_id}: {e}")
    finally:
        desktop.x11_disp.close()


def _toggle_fullscreen(window_id):
    """
    Toggle window fullscreen state

    Args:
        window_id (str or int): Window ID in hex format
    """
    desktop = X11Desktop()
    try:
        window = desktop[window_id]

        # Send _NET_WM_STATE message to toggle fullscreen
        _NET_WM_STATE = window.x11_disp.intern_atom('_NET_WM_STATE')
        _NET_WM_STATE_FULLSCREEN = window.x11_disp.intern_atom('_NET_WM_STATE_FULLSCREEN')

        event = protocol.event.ClientMessage(
            window=window.x11_win,
            client_type=_NET_WM_STATE,
            data=(32, [2, _NET_WM_STATE_FULLSCREEN, 0, 1, 0])  # 2 = toggle
        )

        mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        window.x11_root.send_event(event, event_mask=mask)

        window.x11_disp.sync()
        print(f"Toggled fullscreen for window {window_id}")
    except Exception as e:
        print(f"Error toggling fullscreen for window {window_id}: {e}")
    finally:
        desktop.x11_disp.close()


def _hide_window(window_id):
    """
    Hide window (minimize/iconify)
    Args:
        window_id (str or int): Window ID in hex format
    """
    raise Warning("Unexcepted behavior! Fix not implemented yet.")
    desktop = X11Desktop()
    try:
        window = desktop[window_id]

        # Unmap window (hide it)
        window.x11_win.unmap()
        # todo: strange behavior of this! Window likes closed, but it is NOT. Run app to show it.

        # Also send iconify message for proper window manager handling
        event = protocol.event.ClientMessage(
            window=window,
            client_type=window.x11_disp.intern_atom('WM_CHANGE_STATE'),
            data=(32, [X.IconicState, 0, 0, 0, 0])
        )

        mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        window.x11_root.send_event(event, event_mask=mask)

        window.x11_disp.sync()
        print(f"Hidden window {window_id}")
    except Exception as e:
        print(f"Error hiding window {window_id}: {e}")
    finally:
        desktop.x11_disp.close()


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






