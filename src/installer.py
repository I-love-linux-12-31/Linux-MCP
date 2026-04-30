import os
import json
import sys

env_override = [
    "DISPLAY",
    "XAUTHORITY",
    "DBUS_SESSION_BUS_ADDRESS",
    "XDG_RUNTIME_DIR",
    "XDG_DATA_DIRS",
    "XDG_SESSION_CLASS",
    "XDG_SESSION_TYPE",
    "XDG_SESSION_DESKTOP",
    "XDG_CURRENT_DESKTOP",
    "XDG_MENU_PREFIX"

    "WAYLAND_DISPLAY",

    "LANG",
    "HOME",

    "HYPRLAND_INSTANCE_SIGNATURE",
]

config = {
    "Claude": {
        "path": "~/.config/Claude/claude_desktop_config.json",
        "env_override": True,
        "auto_approve": False,
        "json_path": ["mcpServers"],
               },
    "VSCode": {
        "path": "~/.config/Code/User/settings.json",
        "env_override": False,
        "auto_approve": False,
        "json_path": ["mcp", "servers"],
    },
    "Kiro": {
        "path": "~/.kiro/settings/mcp.json",
        "env_override": True,
        "auto_approve": False,
        "json_path": ["mcpServers"],
    },
    "console-chat-gpt": {
        "path": "/opt/console-chat-gpt/mcp_config.json",
        "env_override": True,
        "auto_approve": False,
        "json_path": ["mcpServers"],
    },
    "LM-Studio": {
        "path": "~/.lmstudio/mcp.json",
        "env_override": True,
        "auto_approve": False,
        "json_path": ["mcpServers"],
    },
}


def install_for(software_name, software_config: dict, server_path) -> None:
    path = os.path.expanduser(software_config["path"])
    do_env_override = software_config["env_override"]
    json_path = software_config["json_path"]
    auto_approve = software_config["auto_approve"]

    if not os.path.exists(path):
        print(f"\033[31mMCP configuration file for {software_name} NOT found!\033[0m: {path}")
        return

    with open(path, "rt") as f:
        data = json.load(f)

    mcp_root = data
    try:
        for key in json_path:
            new_root = mcp_root.get(key, None)
            if new_root is None:
                mcp_root[key] = dict()
                new_root = mcp_root[key]
            mcp_root = new_root
    except KeyError:
        print(f"\033[31mBad file structure!\033[0m Update json_path or fix file: {path} ")
        return

    mcp_root["Linux-MCP"] = {
        "command": "uv",
        "args": [
            "--directory",
            server_path,
            "run",
            "src/main.py",
        ],
    }

    if do_env_override:
        mcp_root["Linux-MCP"]["env"] = dict()
        for key in env_override:
            value = os.environ.get(key, None)
            if value is not None:
                mcp_root["Linux-MCP"]["env"][key] = value

    if auto_approve:
        mcp_root["Linux-MCP"]["autoApprove"] = [
            "Clipboard-Get-Text",
            "Clipboard-Set-Text",
            "Clipboard-Get-Image",
            "Clipboard-Copy-Image",
            "Clipboard-Paste-CtrlV",
            "Clipboard-Paste-CtrlShiftV",

            "Cursor-Move",
            "Cursor-Click",
            "Cursor-Drag-And-Drop",
            "Cursor-Get-Position",

            "Keyboard-Single-Key-Press",
            "Keyboard-Hotkey-Press",
            "Keyboard-Type-Line-Of-Text",
            "Keyboard-Type-Text",

            "Wait",
            "Call-To-Open-URI",

            "Desktop-State-Common",
            "Window-Get-Image",
            "Desktop-Get-Image",
            "Desktop-Get-Image-Compressed",

            "Applications-Get-List",
            "Applications-Get-Info",
            "Applications-Start",
        ]

    with open(path, "wt") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    for i in config:
        srv_path = os.getcwd()
        if len(sys.argv) > 1:
            srv_path = sys.argv[1]
        install_for(i, config[i], srv_path)
        print(f"Updated MCP list for {i}")
