#!/bin/sh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INSTALL_DIR=${CODEX_SWAP_INSTALL_DIR:-"$HOME/.local/bin"}

mkdir -p "$INSTALL_DIR"
cp "$SOURCE_DIR/codex-swap" "$INSTALL_DIR/codex-swap"
chmod 755 "$INSTALL_DIR/codex-swap"

echo "Installed codex-swap to $INSTALL_DIR/codex-swap"
case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *) echo "Add $INSTALL_DIR to PATH, then open a new shell." ;;
esac
