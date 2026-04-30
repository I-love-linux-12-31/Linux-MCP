import json
import os
import socket
from typing import Any, Dict, List, Optional, Union

from src.modules.windows_and_desktop.desktop import BaseDesktopInfo
from src.modules.windows_and_desktop.window import BaseWindow


class HyprlandIPCError(Exception):
    """Exception raised for Hyprland IPC communication errors"""
    pass


class HyprlandIPC:
    """Low-level Hyprland IPC protocol implementation.

    Hyprland exposes a text-based UNIX socket. Commands are sent as plain
    strings; prefixing a request with `j/` requests a JSON response, while
    prefixing with `/` allows multiple commands in one batch.
    """

    def __init__(self, socket_path: Optional[str] = None):
        if socket_path is None:
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
            instance = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
            if not runtime_dir or not instance:
                raise HyprlandIPCError(
                    "Hyprland environment variables not found. "
                    "Is Hyprland running and HYPRLAND_INSTANCE_SIGNATURE set?"
                )
            socket_path = os.path.join(runtime_dir, "hypr", instance, ".socket.sock")

        if not os.path.exists(socket_path):
            raise HyprlandIPCError(f"Hyprland socket not found: {socket_path}")

        self.socket_path = socket_path

    def _send(self, request: str) -> bytes:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self.socket_path)
            sock.sendall(request.encode("utf-8"))

            chunks: List[bytes] = []
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            sock.close()

    def query_json(self, command: str) -> Any:
        """Issue a query that returns JSON output (e.g. 'clients', 'monitors')."""
        raw = self._send(f"j/{command}")
        try:
            return json.loads(raw.decode("utf-8", errors="ignore"))
        except json.JSONDecodeError as e:
            raise HyprlandIPCError(
                f"Invalid JSON response for command '{command}': {e}"
            )

    def query_text(self, command: str) -> str:
        """Issue a query that returns plain text output (e.g. 'cursorpos')."""
        return self._send(command).decode("utf-8", errors="ignore").strip()

    def dispatch(self, command: str) -> str:
        """Run a Hyprland dispatcher (e.g. 'focuswindow address:0x...')."""
        result = self._send(f"dispatch {command}").decode("utf-8", errors="ignore").strip()
        if result and result.lower() != "ok":
            raise HyprlandIPCError(f"Dispatch '{command}' failed: {result}")
        return result


def _addr_to_int(address: Union[str, int]) -> int:
    """Convert Hyprland window address to integer."""
    if isinstance(address, int):
        return address
    return int(address, 16)


def _int_to_addr(value: int) -> str:
    """Convert integer to Hyprland-style hex address."""
    return hex(value)


class HyprlandWindow(BaseWindow):
    """Hyprland window wrapper.

    Hyprland identifies windows by an `address` (a hex pointer string).
    We store it as an integer in `self.id` so it interoperates with the
    base class's hex-string `__getitem__` lookup, but expose it as a hex
    string when communicating with Hyprland's IPC.
    """

    def __init__(self, client: Dict[str, Any], priority: int, ipc: HyprlandIPC):
        self._client = client
        self._ipc = ipc
        self.priority = priority
        self.id = _addr_to_int(client.get("address", "0x0"))

    @property
    def address(self) -> str:
        return _int_to_addr(self.id)

    def get_title(self) -> str:
        return self._client.get("title", "") or ""

    def get_classes(self) -> list:
        classes = []
        cls = self._client.get("class")
        initial_cls = self._client.get("initialClass")
        if cls:
            classes.append(cls)
        if initial_cls and initial_cls != cls:
            classes.append(initial_cls)
        return classes if classes else ["unknown"]

    def get_pid(self) -> Optional[int]:
        pid = self._client.get("pid")
        if pid is None or pid <= 0:
            return None
        return int(pid)

    def get_flags(self) -> List[str]:
        flags: List[str] = []

        if self._client.get("floating"):
            flags.append("FLOATING")
        else:
            flags.append("TILED")

        fullscreen = self._client.get("fullscreen", 0)
        # Newer Hyprland returns an enum-like int (0 none, 1 maximized, 2 fullscreen, 3 both)
        if isinstance(fullscreen, bool):
            if fullscreen:
                flags.append("FULLSCREEN")
        elif isinstance(fullscreen, int) and fullscreen > 0:
            flags.append("FULLSCREEN")

        if self._client.get("pinned"):
            flags.append("PINNED")
        if self._client.get("hidden"):
            flags.append("HIDDEN")
        if not self._client.get("mapped", True):
            flags.append("UNMAPPED")
        if self._client.get("xwayland"):
            flags.append("XWAYLAND")
        else:
            flags.append("WAYLAND")

        grouped = self._client.get("grouped") or []
        if grouped:
            flags.append("GROUPED")

        workspace = self._client.get("workspace") or {}
        ws_id = workspace.get("id")
        if ws_id is not None and ws_id < 0:
            flags.append("SPECIAL_WORKSPACE")

        return flags

    def get_geometry(self) -> Dict[str, Optional[int]]:
        at = self._client.get("at") or [None, None]
        size = self._client.get("size") or [None, None]
        return {
            "x": at[0] if len(at) > 0 else None,
            "y": at[1] if len(at) > 1 else None,
            "width": size[0] if len(size) > 0 else None,
            "height": size[1] if len(size) > 1 else None,
        }

    def get_geometry_str(self) -> str:
        geom = self.get_geometry()
        return f"{geom['x']}x{geom['y']}+{geom['width']},{geom['height']}"

    def serialize(self) -> dict:
        base = super().serialize()
        workspace = self._client.get("workspace") or {}
        base["workspace"] = {
            "id": workspace.get("id"),
            "name": workspace.get("name"),
        }
        base["monitor"] = self._client.get("monitor")
        return base


class HyprlandDesktop(BaseDesktopInfo):
    """Hyprland compositor desktop info"""

    def __init__(self):
        self.ipc = HyprlandIPC()
        self.displays: List[Dict[str, Any]] = []
        self.windows: List[HyprlandWindow] = []
        self.workspaces: List[Dict[str, Any]] = []
        self._active_window_address: Optional[str] = None

        self.update_state()

    def find_session_info(self):
        # Hyprland is always Wayland; honour env vars but force Wayland=True.
        super().find_session_info()
        self.is_Wayland = True
        self.is_X11 = False

    def update_displays_info(self):
        monitors = self.ipc.query_json("monitors")
        self.displays = []
        for monitor in monitors:
            self.displays.append({
                "name": monitor.get("name", "Unknown"),
                "width": int(monitor.get("width", 0)),
                "height": int(monitor.get("height", 0)),
                "x": int(monitor.get("x", 0)),
                "y": int(monitor.get("y", 0)),
                "scale": monitor.get("scale", 1.0),
                "transform": monitor.get("transform", 0),
                "refresh_rate": monitor.get("refreshRate"),
                "active_workspace": monitor.get("activeWorkspace", {}),
                "special_workspace": monitor.get("specialWorkspace", {}),
                "focused": bool(monitor.get("focused", False)),
            })

    def load_windows(self):
        clients = self.ipc.query_json("clients")

        # Hyprland orders clients arbitrarily. Sort by focusHistoryID so the
        # most-recently-focused window has priority 0 (top of stack).
        clients.sort(key=lambda c: c.get("focusHistoryID", 9_999))

        self.windows = [
            HyprlandWindow(client, i, self.ipc)
            for i, client in enumerate(clients)
        ]

        try:
            active = self.ipc.query_json("activewindow")
            addr = active.get("address") if isinstance(active, dict) else None
            self._active_window_address = addr if addr else None
        except HyprlandIPCError:
            self._active_window_address = None

        try:
            self.workspaces = self.ipc.query_json("workspaces") or []
        except HyprlandIPCError:
            self.workspaces = []

    def __getitem__(self, item: Union[int, str]) -> HyprlandWindow:
        if isinstance(item, str):
            target = _addr_to_int(item)
        else:
            target = int(item)
        for window in self.windows:
            if window.id == target:
                return window
        raise KeyError(f"No window with address: {item}")

    def serialize(self) -> dict:
        focused = self._active_window_address or "Unknown"
        return {
            "session_info": {
                "X11 display": self.is_X11,
                "Wayland": self.is_Wayland,
                "Desktop environment": self.desktop_environment,
                "compositor": "Hyprland",
                "default_display": "unknown",
                "Displays": [
                    {
                        "name": disp["name"],
                        "size": [disp["width"], disp["height"]],
                        "position": [disp["x"], disp["y"]],
                        "scale": disp.get("scale"),
                        "active_workspace": disp.get("active_workspace", {}).get("name"),
                        "focused": disp.get("focused", False),
                    }
                    for disp in self.displays
                ],
            },
            "workspaces": [
                {
                    "id": ws.get("id"),
                    "name": ws.get("name"),
                    "monitor": ws.get("monitor"),
                    "windows": ws.get("windows"),
                    "has_fullscreen": ws.get("hasfullscreen"),
                    "last_window_title": ws.get("lastwindowtitle"),
                }
                for ws in self.workspaces
            ],
            "windows_data": {
                "active_window_id": focused,
                "windows_top_to_bottom_order": [
                    win.serialize() for win in self.windows
                ],
            },
        }


# ---------------------------------------------------------------------------
# Helpers for window manipulation
# ---------------------------------------------------------------------------

def _resolve_address(window_id: Union[str, int]) -> str:
    """Coerce any accepted window-id form to the `address:0x...` Hyprland string."""
    if isinstance(window_id, int):
        return f"address:{_int_to_addr(window_id)}"
    s = str(window_id).strip()
    if s.startswith("address:"):
        return s
    if not s.startswith("0x"):
        # Decimal int as string -> hex
        try:
            return f"address:{_int_to_addr(int(s))}"
        except ValueError:
            raise HyprlandIPCError(f"Invalid window address: {window_id}")
    return f"address:{s}"


def _move_window(window_id: Union[str, int], x: int, y: int) -> None:
    """Move window to absolute screen coordinates.

    Hyprland's `movewindowpixel` only works for floating windows. For tiled
    windows the layout decides position, so we first promote to floating if
    needed (no-op if already floating).
    """
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)

    desktop = HyprlandDesktop()
    win = desktop[window_id]
    if "FLOATING" not in win.get_flags():
        ipc.dispatch(f"setfloating {addr}")

    # `exact` keyword switches movewindowpixel to absolute coordinates.
    ipc.dispatch(f"movewindowpixel exact {int(x)} {int(y)},{addr}")


def _resize_window(window_id: Union[str, int], width: int, height: int) -> None:
    """Resize window to exact pixel size (works on tiled and floating)."""
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"resizewindowpixel exact {int(width)} {int(height)},{addr}")


def _focus_window(window_id: Union[str, int]) -> None:
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"focuswindow {addr}")


def _close_window(window_id: Union[str, int]) -> None:
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"closewindow {addr}")


def _toggle_fullscreen(window_id: Union[str, int]) -> None:
    """Toggle fullscreen for the target window.

    Hyprland's `fullscreen` dispatcher acts on the active window only, so we
    focus the target first, then toggle.
    """
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"focuswindow {addr}")
    # mode 0 = real fullscreen, 1 = maximize. We use 0 for "true" fullscreen.
    ipc.dispatch("fullscreen 0")


def _toggle_floating(window_id: Union[str, int]) -> None:
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"togglefloating {addr}")


def _toggle_pin(window_id: Union[str, int]) -> None:
    """Pin a floating window so it stays visible across workspace switches."""
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"pin {addr}")


def _move_to_workspace(window_id: Union[str, int], workspace: Union[str, int]) -> None:
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"movetoworkspace {workspace},{addr}")


def _move_to_workspace_silent(window_id: Union[str, int], workspace: Union[str, int]) -> None:
    """Move window without following it (no workspace switch)."""
    ipc = HyprlandIPC()
    addr = _resolve_address(window_id)
    ipc.dispatch(f"movetoworkspacesilent {workspace},{addr}")


def _switch_workspace(workspace: Union[str, int]) -> None:
    ipc = HyprlandIPC()
    ipc.dispatch(f"workspace {workspace}")


def get_cursor_position() -> Optional[Dict[str, int]]:
    """Return cursor position via Hyprland IPC (Wayland-native, unlike pyautogui)."""
    try:
        ipc = HyprlandIPC()
        text = ipc.query_text("cursorpos")
        # format: "X, Y"
        parts = [p.strip() for p in text.replace(",", " ").split()]
        if len(parts) >= 2:
            return {"x": int(parts[0]), "y": int(parts[1])}
    except (HyprlandIPCError, ValueError):
        pass
    return None


if __name__ == "__main__":
    desktop = HyprlandDesktop()
    print(json.dumps(desktop.serialize(), indent=2))
