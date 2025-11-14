import os

from modules.init_system import get_mcp, init
init()
mcp = get_mcp()

from modules.all_mcp_functions import *

if __name__ == "__main__":
    mcp.run()