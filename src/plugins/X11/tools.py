import json

from .desktop import X11Desktop
from src.modules.init_system import get_mcp

mcp = get_mcp()

__desktop = X11Desktop()
__desktop.x11_disp.close()
if __desktop.is_X11:
    @mcp.tool(name="Desktop-State-Common")
    def get_desktop_state() -> str:
        """
        Returns info about current session and opened windows as text. Useful to know position of window, it's title and info about displays.
        Keywords: X11, window_manager, windows, window_list, desktop_environment, window_manager, status, info, Linux-MCP
        """
        return json.dumps(X11Desktop().serialize(), indent=2)

    from .image_capture_tools import (
        get_window_image,
        get_full_desktop,
        get_full_desktop_compressed
    )


    from .windows_tools  import (
        move_window,
        resize_window,
        focus_window,
        close_window,
        toggle_fullscreen_window
    )
