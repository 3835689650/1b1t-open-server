#!/bin/bash
# 构建 deb + APT 仓库, 推送到 GitHub (main + gh-pages)
# 用法: ./build-apt.sh [版本号]   默认 1.0.0
set -euo pipefail

VER="${1:-1.0.0}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "==> 1/4 打包 deb"
mkdir -p "$WORK/deb/usr/local/bin" "$WORK/deb/DEBIAN"
install -m755 "$ROOT/1b1t" "$WORK/deb/usr/local/bin/1b1t"
ln -s 1b1t "$WORK/deb/usr/local/bin/1b1t-open-server"
cat > "$WORK/deb/DEBIAN/control" <<EOF
Package: 1b1t-open-server
Version: $VER
Section: utils
Priority: optional
Architecture: all
Depends: python3
Maintainer: 1b1t <3835689650@users.noreply.github.com>
Homepage: https://github.com/3835689650/1b1t-open-server
Description: Minecraft 一键开服工具 (1b1t)
 向导式开服: 选择版本/目录/端口/常见配置, 高级选项可编辑
 server.properties 全部项; 自动下载服务端核心、自动匹配 Java、
 doctor 自主排查问题; 支持 start/stop/restart/status/console。
EOF
dpkg-deb --root-owner-group -b "$WORK/deb" "$WORK/1b1t-open-server_${VER}_all.deb"

echo "==> 2/4 生成 APT 仓库索引"
rm -rf "$ROOT/apt"
mkdir -p "$ROOT/apt/pool/main/1b1t-open-server" \
         "$ROOT/apt/dists/stable/main/binary-all"
cp "$WORK/1b1t-open-server_${VER}_all.deb" "$ROOT/apt/pool/main/1b1t-open-server/"
(cd "$ROOT/apt" && dpkg-scanpackages --arch all pool/ \
    > dists/stable/main/binary-all/Packages)
gzip -9kf "$ROOT/apt/dists/stable/main/binary-all/Packages"

echo "==> 3/4 签名 Release"
cd "$ROOT/apt/dists/stable"
{
    echo "Origin: 1b1t"
    echo "Label: 1b1t apt repo"
    echo "Suite: stable"
    echo "Codename: stable"
    echo "Architectures: all"
    echo "Components: main"
    echo "Date: $(date -R -u)"
    echo "SHA256:"
    sha256sum main/binary-all/Packages main/binary-all/Packages.gz \
        | sed 's|\./||; s|^| |; s|  | |'
} > Release
gpg --batch --yes --digest-algo SHA256 \
    --clearsign -o InRelease Release
cd "$ROOT"

echo "==> 4/4 推送 GitHub"
git add -A
git commit -m "release $VER" --quiet || true
git push origin main --quiet

# gh-pages 只放 apt/ 目录内容
git worktree add -B gh-pages "$WORK/pages" --quiet
rm -rf "$WORK/pages"/* "$WORK/pages"/.[!.]* 2>/dev/null || true
cp -r "$ROOT"/apt/. "$WORK/pages/"
git -C "$WORK/pages" add -A
git -C "$WORK/pages" commit -m "apt $VER" --quiet
git -C "$WORK/pages" push -f origin gh-pages --quiet
git worktree remove "$WORK/pages" --force

echo "完成! 安装方法:"
echo "  curl -fsSL https://github.com/3835689650/1b1t-open-server/raw/main/1b1t-apt-key.gpg | sudo tee /etc/apt/keyrings/1b1t.gpg >/dev/null"
echo "  echo 'deb [signed-by=/etc/apt/keyrings/1b1t.gpg] https://3835689650.github.io/1b1t-open-server/ stable main' | sudo tee /etc/apt/sources.list.d/1b1t.list"
echo "  sudo apt update && sudo apt install 1b1t-open-server"
