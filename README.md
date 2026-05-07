# Linux-MCP

MCP server that exposes a wide set of tools to let an LLM interact with a Linux desktop — windows, input, clipboard, filesystem, and applications.

> [!CAUTION]
> This MCP server gives the LLM tools that **can damage your data or device**. You run this software at your own risk.

## Functionality

> [!WARNING]
> Wayland support is partial. X11 preferred.

### Applications
+ [X] Interact with GUI applications
+ [X] Interact with CLI applications / run shell commands
+ [X] List installed applications and read `.desktop` metadata
+ [X] Launch by application name or by path to a `.desktop` file
+ [X] List running processes

### UI automation
+ [X] Cursor manipulation (move, click, drag-and-drop, position)
+ [X] Keyboard manipulation (single keys, hotkeys, text typing)
+ [X] Window manipulation (move, resize, focus, close, fullscreen)
+ [X] Workspace switching
+ [X] Clipboard interaction (text and images)
+ [X] Screenshot capture (window, desktop)

### Filesystem
+ [X] Read file
+ [X] Write file
+ [X] Update file (in-place edit)
+ [X] Copy / move
+ [X] List directory
+ [X] Open file or URI in the default application (`xdg-open`)

### Session support
| Session                    | Status       |
|----------------------------|--------------|
| X11                        | Supported    |
| Hyprland (Wayland)         | Experimental |
| Sway (Wayland)             | Experimental |
| Other Wayland compositors  | Limited      |

For an overview of the architecture, see [HowItWorks.md](docs/HowItWorks.md).

## Install

### Ubuntu / Debian
> [!WARNING]
> On Ubuntu you need to install [uv](https://github.com/astral-sh/uv) manually.

```bash
sudo apt update
sudo apt install python3-full gnome-screenshot imagemagick
cd /path/to/Linux-MCP
./install.sh    # registers Linux-MCP in supported clients and installs default plugins
```

### Fedora
```bash
sudo dnf install python3 uv gnome-screenshot ImageMagick
cd /path/to/Linux-MCP
./install.sh    # registers Linux-MCP in supported clients and installs default plugins
```

### Wayland (Hyprland / Sway / generic)
Additional packages required for Wayland sessions:
* `wayland-utils`
* `grim` (image capture)
* `wtype` and/or `ydotool` (keyboard/cursor input via the [`wayland-automation`](https://pypi.org/project/wayland-automation/) library)

### What the installer does
`install.sh` runs `uv sync`, then `src/installer.py`, which writes a Linux-MCP entry into the config files of supported client applications. It also copies the default plugins to `/usr/share/Linux-MCP/plugins/`, where the server discovers them at startup.

For a system-wide install (project copied into `/opt/Linux-MCP/`), use `install_global.sh` as root.

### Supported client applications
The installer adds Linux-MCP to:
* Claude Desktop
* VS Code
* Kiro
* LM Studio


### Manual configuration (other clients)
For any other MCP-compatible client, add Linux-MCP to its config file manually. Don't forget to forward your session's environment variables — without them the server can't access to your display, clipboard, compositor...

```json
{
  "mcpServers": {
    "Linux-MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/folder/of/Linux-MCP",
        "run",
        "src/main.py"
      ],
      "env": {
        "DISPLAY": "your value",
        "XAUTHORITY": "your value",
        "DBUS_SESSION_BUS_ADDRESS": "your value",
        "XDG_RUNTIME_DIR": "your value",
        "XDG_DATA_DIRS": "your value",
        "XDG_SESSION_CLASS": "your value",
        "XDG_SESSION_TYPE": "your value",
        "XDG_SESSION_DESKTOP": "your value",
        "XDG_CURRENT_DESKTOP": "your value",
        "LANG": "your value",
        "HOME": "your value",

        "WAYLAND_DISPLAY": "if using Wayland",
        "HYPRLAND_INSTANCE_SIGNATURE": "if using Hyprland"
      }
    }
  }
}
```

## Author
Yaroslav Kuznetsov
