#!/usr/bin/env bash
set -euo pipefail

PKG_ROOT="/opt/code-writer"
WRAPPER="/usr/bin/code-writer"

if [ $(id -u) -ne 0 ]; then
  echo "This script requires sudo privileges to remove installed files."
fi

if [ -d "$PKG_ROOT" ]; then
  echo "Removing $PKG_ROOT"
  sudo rm -rf "$PKG_ROOT"
else
  echo "$PKG_ROOT not found"
fi

if [ -f "$WRAPPER" ]; then
  echo "Removing $WRAPPER"
  sudo rm -f "$WRAPPER"
else
  echo "$WRAPPER not found"
fi

echo "Uninstall finished."
