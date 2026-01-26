#!/usr/bin/env bash
set -euo pipefail

# Build and install locally via makepkg (Arch). If you don't want to use makepkg,
# install Python dependencies manually using the generated requirements.txt.

if ! command -v makepkg >/dev/null 2>&1; then
	echo "Please install 'base-devel' (contains makepkg). On Arch: sudo pacman -S --needed base-devel"
	exit 1
fi

echo "Building and installing package..."
makepkg -si --noconfirm

echo "If you prefer to install Python dependencies into your user environment instead of the package, run:"
echo "  python3 -m pip install --user -r requirements.txt"

echo "Done. You can now run: code-writer [args]"

