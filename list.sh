#!/usr/bin/env bash
# Project CARS 1 Mod List Wrapper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/pcars_mod_installer.py" list "$@"
