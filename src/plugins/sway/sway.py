import json
import socket
import struct
import subprocess
import os
from typing import Optional, List, Dict, Any


class SwayIPCError(Exception):
    """Exception raised for Sway IPC communication errors"""
    pass


class SwayFeatureNotSupported(NotImplementedError):
    """Exception raised when feature is not supported in Sway"""
    pass


class SwayIPC:
    """Low-level Sway IPC protocol implementation"""

    MAGIC = b'i3-ipc'

    # Message types
    COMMAND = 0
    GET_WORKSPACES = 1
    SUBSCRIBE = 2
    GET_OUTPUTS = 3
    GET_TREE = 4
    GET_MARKS = 5
    GET_BAR_CONFIG = 6
    GET_VERSION = 7
    GET_BINDING_MODES = 8
    GET_CONFIG = 9
    SEND_TICK = 10
    GET_BINDING_STATE = 12
    GET_INPUTS = 100
    GET_SEATS = 101

    def __init__(self, socket_path: Optional[str] = None):
        """
        Initialize Sway IPC connection

        Args:
            socket_path: Path to Sway IPC socket. If None, auto-detect from environment
        """
        if socket_path is None:
            socket_path = os.environ.get('SWAYSOCK')
            if socket_path is None:
                # Try to get socket path from sway command
                try:
                    result = subprocess.run(
                        ['sway', '--get-socketpath'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    socket_path = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    raise SwayIPCError(
                        "Could not determine Sway socket path. "
                        "Is Sway running and SWAYSOCK set?"
                    )

        self.socket_path = socket_path

    def _pack_message(self, msg_type: int, payload: str = "") -> bytes:
        """Pack message according to i3 IPC protocol"""
        payload_bytes = payload.encode('utf-8')
        header = self.MAGIC + struct.pack('II', len(payload_bytes), msg_type)
        return header + payload_bytes

    def _unpack_message(self, data: bytes) -> tuple[int, dict]:
        """Unpack message from i3 IPC protocol"""
        if len(data) < 14:
            raise SwayIPCError("Message too short")

        magic = data[:6]
        if magic != self.MAGIC:
            raise SwayIPCError(f"Invalid magic string: {magic}")

        payload_len, msg_type = struct.unpack('II', data[6:14])
        payload = data[14:14 + payload_len].decode('utf-8')

        return msg_type, json.loads(payload) if payload else {}

    def send_command(self, msg_type: int, payload: str = "") -> Any:
        """Send command to Sway and receive response"""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self.socket_path)
            sock.sendall(self._pack_message(msg_type, payload))

            # Receive response
            header = sock.recv(14)
            if len(header) < 14:
                raise SwayIPCError("Failed to receive full header")

            payload_len = struct.unpack('II', header[6:14])[0]
            payload = b''
            while len(payload) < payload_len:
                chunk = sock.recv(payload_len - len(payload))
                if not chunk:
                    raise SwayIPCError("Connection closed while receiving payload")
                payload += chunk

            _, response = self._unpack_message(header + payload)
            return response
        finally:
            sock.close()

    def run_command(self, command: str) -> List[Dict]:
        """Execute Sway command"""
        return self.send_command(self.COMMAND, command)

    def get_tree(self) -> Dict:
        """Get window tree"""
        return self.send_command(self.GET_TREE)

    def get_outputs(self) -> List[Dict]:
        """Get display outputs"""
        return self.send_command(self.GET_OUTPUTS)

    def get_workspaces(self) -> List[Dict]:
        """Get workspaces info"""
        return self.send_command(self.GET_WORKSPACES)


from src.modules.windows_and_desktop.desktop import BaseDesktopInfo
from src.modules.windows_and_desktop.window import BaseWindow


class SwayWindow(BaseWindow):
    """Sway window wrapper"""

    def __init__(self, node: Dict, priority: int, ipc: SwayIPC):
        self.id = node.get('id', 0)
        self.priority = priority
        self._node = node
        self._ipc = ipc

    def _refresh_node(self):
        """Refresh window data from tree"""
        tree = self._ipc.get_tree()
        self._node = self._find_node_by_id(tree, self.id)
        if self._node is None:
            raise SwayIPCError(f"Window {self.id} no longer exists")

    def _find_node_by_id(self, node: Dict, target_id: int) -> Optional[Dict]:
        """Recursively find node by ID in tree"""
        if node.get('id') == target_id:
            return node
        for child in node.get('nodes', []) + node.get('floating_nodes', []):
            result = self._find_node_by_id(child, target_id)
            if result:
                return result
        return None

    def get_title(self) -> str:
        return self._node.get('name', '')

    def get_classes(self) -> list:
        app_id = self._node.get('app_id')
        window_properties = self._node.get('window_properties', {})
        wm_class = window_properties.get('class')

        classes = []
        if app_id:
            classes.append(app_id)
        if wm_class:
            classes.append(wm_class)

        return classes if classes else ['unknown']

    def get_pid(self) -> Optional[int]:
        return self._node.get('pid')

    def get_flags(self) -> List[str]:
        flags = []

        if self._node.get('focused'):
            flags.append('FOCUSED')
        if self._node.get('fullscreen_mode', 0) != 0:
            flags.append('FULLSCREEN')
        if self._node.get('floating'):
            flags.append('FLOATING')
        if self._node.get('sticky'):
            flags.append('STICKY')
        if self._node.get('urgent'):
            flags.append('URGENT')

        # Window type flags
        window_type = self._node.get('type')
        if window_type:
            flags.append(f'TYPE_{window_type.upper()}')

        return flags

    def get_geometry(self) -> Dict[str, Optional[int]]:
        rect = self._node.get('rect', {})
        return {
            'x': rect.get('x'),
            'y': rect.get('y'),
            'width': rect.get('width'),
            'height': rect.get('height')
        }

    def get_geometry_str(self) -> str:
        geom = self.get_geometry()
        return f"{geom['x']}x{geom['y']}+{geom['width']},{geom['height']}"


class SwayDesktop(BaseDesktopInfo):
    """Sway compositor desktop info"""

    def __init__(self):
        self.ipc = SwayIPC()
        self.displays = []
        self.windows = []

        # Verify Sway is running
        try:
            version = self.ipc.send_command(SwayIPC.GET_VERSION)
            print(f"Connected to Sway version: {version.get('human_readable', 'unknown')}")
        except Exception as e:
            raise SwayIPCError(f"Failed to connect to Sway: {e}")

        self.update_state()

    def update_displays_info(self):
        """Update display information from Sway"""
        outputs = self.ipc.get_outputs()

        self.displays = []
        for output in outputs:
            if not output.get('active'):
                continue

            rect = output.get('rect', {})
            self.displays.append({
                'name': output.get('name', 'Unknown'),
                'width': rect.get('width', 0),
                'height': rect.get('height', 0),
                'x': rect.get('x', 0),
                'y': rect.get('y', 0),
                'scale': output.get('scale', 1.0),
                'transform': output.get('transform', 'normal')
            })

    def load_windows(self):
        """Load all windows from Sway tree"""
        tree = self.ipc.get_tree()

        windows = []
        self._collect_windows(tree, windows)

        # Sort by stacking order (focused windows last = on top)
        # Priority assigned based on collection order
        self.windows = [
            SwayWindow(node, i, self.ipc)
            for i, node in enumerate(windows)
        ]

    def _collect_windows(self, node: Dict, windows: List[Dict]):
        """Recursively collect windows from tree"""
        node_type = node.get('type')

        # Collect actual windows (con with window property or xwayland)
        if node_type in ('con', 'floating_con'):
            if node.get('pid') is not None or node.get('window'):
                # Skip workspace/output containers
                if node.get('name') not in (None, '__i3', '__i3_scratch'):
                    windows.append(node)

        # Recurse into children
        for child in node.get('nodes', []):
            self._collect_windows(child, windows)

        # Handle floating windows separately
        for floating in node.get('floating_nodes', []):
            self._collect_windows(floating, windows)

    def __getitem__(self, item: int | str) -> SwayWindow:
        """Get window by ID"""
        if isinstance(item, str):
            # Try hex format
            if item.startswith('0x'):
                item = int(item, 16)
            else:
                item = int(item)

        for window in self.windows:
            if window.id == item:
                return window
        raise KeyError(f"No window with id: {item}")


# Helper functions for window manipulation

def _move_window(window_id: int | str, x: int, y: int):
    """
    Move window to specified position

    Args:
        window_id: Window ID (int or hex string)
        x: X coordinate
        y: Y coordinate
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        # Sway uses container IDs for commands
        cmd = f'[con_id={window.id}] move position {x} {y}'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Moved window {window_id} to position ({x}, {y})")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to move window: {error}")
    except Exception as e:
        print(f"Error moving window {window_id}: {e}")
        raise


def _resize_window(window_id: int | str, width: int, height: int):
    """
    Resize window to specified dimensions

    Args:
        window_id: Window ID
        width: New width in pixels
        height: New height in pixels
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] resize set {width} {height}'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Resized window {window_id} to {width}x{height}")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to resize window: {error}")
    except Exception as e:
        print(f"Error resizing window {window_id}: {e}")
        raise


def _focus_window(window_id: int | str):
    """
    Focus (activate) window

    Args:
        window_id: Window ID
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] focus'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Focused window {window_id}")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to focus window: {error}")
    except Exception as e:
        print(f"Error focusing window {window_id}: {e}")
        raise


def _close_window(window_id: int | str):
    """
    Close window gracefully

    Args:
        window_id: Window ID
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] kill'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Closed window {window_id}")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to close window: {error}")
    except Exception as e:
        print(f"Error closing window {window_id}: {e}")
        raise


def _toggle_fullscreen(window_id: int | str):
    """
    Toggle window fullscreen state

    Args:
        window_id: Window ID
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] fullscreen toggle'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Toggled fullscreen for window {window_id}")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to toggle fullscreen: {error}")
    except Exception as e:
        print(f"Error toggling fullscreen for window {window_id}: {e}")
        raise


def _hide_window(window_id: int | str):
    """
    Hide window (move to scratchpad)

    Args:
        window_id: Window ID

    Note: In Sway, hiding means moving to scratchpad.
    Use 'scratchpad show' to restore.
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] move scratchpad'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Hidden window {window_id} (moved to scratchpad)")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to hide window: {error}")
    except Exception as e:
        print(f"Error hiding window {window_id}: {e}")
        raise


def _show_window(window_id: int | str):
    """
    Show window from scratchpad

    Args:
        window_id: Window ID
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] scratchpad show'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Showed window {window_id} from scratchpad")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to show window: {error}")
    except Exception as e:
        print(f"Error showing window {window_id}: {e}")
        raise


def _set_window_floating(window_id: int | str, floating: bool = True):
    """
    Set window floating state

    Args:
        window_id: Window ID
        floating: True to make floating, False to tile
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        state = 'enable' if floating else 'disable'
        cmd = f'[con_id={window.id}] floating {state}'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Set window {window_id} floating: {floating}")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to set floating state: {error}")
    except Exception as e:
        print(f"Error setting floating state for window {window_id}: {e}")
        raise


def _move_window_to_workspace(window_id: int | str, workspace: str | int):
    """
    Move window to specific workspace

    Args:
        window_id: Window ID
        workspace: Workspace name or number
    """
    desktop = SwayDesktop()
    try:
        window = desktop[window_id]

        cmd = f'[con_id={window.id}] move container to workspace {workspace}'
        result = desktop.ipc.run_command(cmd)

        if result and result[0].get('success'):
            print(f"Moved window {window_id} to workspace {workspace}")
        else:
            error = result[0].get('error', 'Unknown error') if result else 'No response'
            raise SwayIPCError(f"Failed to move to workspace: {error}")
    except Exception as e:
        print(f"Error moving window {window_id} to workspace: {e}")
        raise


# Example usage
if __name__ == '__main__':
    try:
        desktop = SwayDesktop()
        print(json.dumps(desktop.serialize(), indent=2))

        print("\n=== Windows ===")
        for win in desktop.windows:
            print(f"ID: {win.id} | Title: {win.get_title()} | Classes: {win.get_classes()}")
    except SwayIPCError as e:
        print(f"Sway error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")