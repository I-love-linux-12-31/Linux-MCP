#!/bin/bash

echo "Installing dependencies and writing Linux-MCP in known applications..."
uv sync && uv run src/installer.py "$(pwd)"
echo "Creating plugins directory..."
sudo mkdir /usr/share/Linux-MCP/plugins -p -m 775
echo "Installing default plugins..."
sudo cp -r src/plugins/* /usr/share/Linux-MCP/plugins/
echo "DONE!"
