import os
import json

from .hyprland import HyprlandDesktop
from src.modules.init_system import get_mcp

mcp = get_mcp()


def _is_hyprland_session() -> bool:
    """Hyprland always sets HYPRLAND_INSTANCE_SIGNATURE for its session.
    Fall back to XDG_CURRENT_DESKTOP for unusual setups.
    """
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return True
    de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    return "hyprland" in de


if _is_hyprland_session():
    @mcp.tool(name="Desktop-State-Common")
    def get_desktop_state() -> str:
        """
        Returns info about current Hyprland session, monitors, workspaces and opened windows as JSON.
        Useful to know position of windows, their titles, workspace assignments and info about displays.
        Keywords: Hyprland, Wayland, window_manager, windows, window_list, desktop_environment, status, info, Linux-MCP
        """
        return json.dumps(HyprlandDesktop().serialize(), indent=2)

    from .windows_tools import (
        move_window,
        resize_window,
        focus_window,
        close_window,
        toggle_fullscreen_window,
        toggle_floating_window,
        toggle_pin_window,
        move_window_to_workspace,
        switch_workspace,
        list_workspaces,
    )

    from .image_capture_tools import (
        get_window_image,
        get_full_desktop,
        get_full_desktop_compressed,
    )
