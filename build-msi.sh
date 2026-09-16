#!/bin/bash
# Windows MSI 安装包 (wixl 生成, 无需 Windows 环境)
# 用法: ./build-msi.sh <cli.exe> <gui.exe> <版本号>
# 输出: 1b1t-open-server_<版本>_windows.msi
set -euo pipefail

CLI_EXE="$1"; GUI_EXE="$2"; VER="$3"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/1b1t-open-server_${VER}_windows.msi"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp "$CLI_EXE" "$WORK/1b1t.exe"
cp "$GUI_EXE" "$WORK/1b1t-gui.exe"
cp "$ROOT/setpath.bat" "$WORK/setpath.bat"
cp "$ROOT/1b1t.wxs" "$WORK/main.wxs"

(cd "$WORK" && wixl -D "Version=$VER" -o "out.msi" main.wxs)
cp "$WORK/out.msi" "$OUT"
echo "已生成: $OUT ($(du -h "$OUT" | cut -f1))"
