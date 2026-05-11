#!/bin/bash

export FASTMCP_HOST="0.0.0.0"
export FASTMCP_PORT=7447
export FASTMCP_TRANSPORT=streamable-http
uv run src/main.py
