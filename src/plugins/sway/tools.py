import os
import json

from .sway import SwayDesktop
from src.modules.init_system import get_mcp

mcp = get_mcp()

if os.environ.get("XDG_CURRENT_DESKTOP", "None").lower() == "sway":
    @mcp.tool(name="Desktop-State-Common")
    def get_desktop_state() -> str:
        """
        Returns info about current session and opened windows as text. Useful to know position of window, it's title and info about displays.
        Keywords: X11, window_manager, windows, window_list, desktop_environment, window_manager, status, info, Linux-MCP
        """
        return json.dumps(SwayDesktop().serialize(), indent=2)

    from .windows_tools  import (
        move_window,
        resize_window,
        focus_window,
        close_window,
        toggle_fullscreen_window
    )

    # todo: implement single window image capture
    from .image_capture_tools import (
        # get_window_image,
        get_full_desktop,
        get_full_desktop_compressed,
    )
