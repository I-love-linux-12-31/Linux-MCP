#!/bin/bash

is_user_root ()
{
    [ "$(id -u)" -eq 0 ]
}


if ! is_user_root; then
  echo "Please, run as root!"
  exit
fi

mkdir /opt/Linux-MCP -m 755 -p
cp -r ./* /opt/Linux-MCP/

echo "Installing dependencies..."
uv sync --directory /opt/Linux-MCP/
echo "Creating plugins directory..."
mkdir /usr/share/Linux-MCP/plugins -p -m 775
echo "Installing default plugins..."
cp -r src/plugins/* /usr/share/Linux-MCP/plugins/
echo "DONE!"
