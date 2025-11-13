#!/bin/bash

uv sync && uv run src/installer.py "$(pwd)"
