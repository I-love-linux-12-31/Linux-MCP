import os
import sys
import importlib
import inspect

PLUGINS_DIR = "/usr/share/Linux-MCP/plugins"
sys.path.append("/usr/share/Linux-MCP")
sys.path.append(os.getcwd())

from src.modules.init_system import get_mcp, init
init()
mcp = get_mcp()

# Main tools
from modules.all_mcp_functions import *


def load_plugin_tools():
    if not os.path.isdir(PLUGINS_DIR):
        print(f"Directory '{PLUGINS_DIR}' does not exist — skipping plugin load.")
        return

    for entry in os.listdir(PLUGINS_DIR):
        package_path = os.path.join(PLUGINS_DIR, entry)
        if not os.path.isdir(package_path):
            continue

        tools_module_name = f"plugins.{entry}.tools"

        try:
            module = importlib.import_module(tools_module_name)
        except Exception as e:
            print(f"Failed to import module '{tools_module_name}' ({entry}): {e}")
            continue

        # Импортируем только функции
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            globals()[name] = obj
            # print(name)

        print(f"Loaded functions from {tools_module_name}")


if __name__ == "__main__":
    load_plugin_tools()
    mcp.run()