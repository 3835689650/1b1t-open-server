#!/bin/bash
# 构建 deb + APT 仓库 + 更新官网更新日志, 推送到 GitHub (main + gh-pages)
# 用法: ./build-apt.sh [版本号]   默认 1.0.0
# 发布前先编辑 CHANGELOG.md, 在顶部加 "## vX.Y.Z - 日期" 条目(### 新增/### 修复)
set -euo pipefail

VER="${1:-1.0.0}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
SITE_SRC="${SITE_SRC:-$ROOT/../openmc-pan-build/1b1t/index.html}"
SITE_DST="/www/wwwroot/openmcserver.cn/1b1t/index.html"
REPO="3835689650/1b1t-open-server"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "==> 1/5 打包 deb"
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
Homepage: https://openmcserver.cn/1b1t/
Description: Minecraft 一键开服工具 (1b1t)
 向导式开服: 选择版本/目录/端口/常见配置, 高级选项可编辑
 server.properties 全部项; 自动下载服务端核心、自动匹配 Java、
 doctor 自主排查问题; 支持 start/stop/restart/status/console。
EOF
dpkg-deb --root-owner-group -b "$WORK/deb" "$WORK/1b1t-open-server_${VER}_all.deb"

echo "==> 2/5 生成 APT 仓库索引"
rm -rf "$ROOT/apt"
mkdir -p "$ROOT/apt/pool/main/1b1t-open-server" \
         "$ROOT/apt/dists/stable/main/binary-all"
cp "$WORK/1b1t-open-server_${VER}_all.deb" "$ROOT/apt/pool/main/1b1t-open-server/"
(cd "$ROOT/apt" && dpkg-scanpackages --arch all pool/ \
    > dists/stable/main/binary-all/Packages)
gzip -9kf "$ROOT/apt/dists/stable/main/binary-all/Packages"

echo "==> 3/5 签名 Release"
cd "$ROOT/apt/dists/stable"
{
    echo "Origin: 1b1t"
    echo "Label: 1b1t apt repo"
    echo "Suite: stable"
    echo "Codename: stable"
    echo "Architectures: all"
    echo "Components: main"
    echo "Date: $(date -R -u)"
    echo "Valid-Until: $(date -R -u -d '+1 year')"
    for algo in sha256sum sha512sum; do
        echo "${algo%sum}:"
        for f in main/binary-all/Packages main/binary-all/Packages.gz; do
            read h _ <<< "$($algo "$f")"
            echo " $h $(stat -c%s "$f") $f"
        done
    done
} > Release
gpg --batch --yes --digest-algo SHA512 --personal-digest-preferences SHA512 \
    --clearsign -o InRelease Release
cd "$ROOT"

echo "==> 4/5 推送 GitHub (git push 失败时自动走 API)"
# API 上传单文件 (github.com 被墙时的替代)
api_put() { # 本地文件 仓库路径 分支
    local sha b64
    sha=$(gh api "repos/$REPO/contents/$2?ref=$3" --jq '.sha' 2>/dev/null || true)
    b64=$(base64 -w0 "$1")
    if [ -n "$sha" ]; then
        gh api "repos/$REPO/contents/$2" -X PUT -f message="release $VER" \
            -f branch="$3" -f sha="$sha" -f content="$b64" --jq '.commit.sha' >/dev/null
    else
        gh api "repos/$REPO/contents/$2" -X PUT -f message="release $VER" \
            -f branch="$3" -f content="$b64" --jq '.commit.sha' >/dev/null
    fi
}
# main 分支全量文件 (脚本/文档/apt 目录)
MAIN_FILES=()
for f in 1b1t README.md LICENSE CHANGELOG.md build-apt.sh 1b1t-apt-key.gpg \
         $(cd apt && find . -type f | sed 's|^\./||'); do
    [ -f "$ROOT/$f" ] && MAIN_FILES+=("$f")
done
if git add -A && git commit -m "release $VER" --quiet 2>/dev/null \
   && git push origin main --quiet 2>/dev/null; then
    echo "  main: git push 成功"
else
    echo "  main: git push 失败, 走 API"
    for f in "${MAIN_FILES[@]}"; do api_put "$ROOT/$f" "$f" main; done
fi
# gh-pages 只放 apt/ 目录内容
git worktree prune
if git worktree add -B gh-pages "$WORK/pages" --quiet 2>/dev/null; then
    find "$WORK/pages" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
    cp -r "$ROOT"/apt/. "$WORK/pages/"
    if git -C "$WORK/pages" add -A && git -C "$WORK/pages" commit -m "apt $VER" --quiet \
       && git -C "$WORK/pages" push -f origin gh-pages --quiet 2>/dev/null; then
        echo "  gh-pages: git push 成功"
    else
        echo "  gh-pages: git push 失败, 走 API"
        for f in $(cd apt && find . -type f | sed 's|^\./||'); do
            api_put "$ROOT/apt/$f" "$f" gh-pages
        done
    fi
    git worktree remove "$WORK/pages" --force
else
    echo "  gh-pages: git push 失败, 走 API"
    for f in $(cd apt && find . -type f | sed 's|^\./||'); do
        api_put "$ROOT/apt/$f" "$f" gh-pages
    done
fi

echo "==> 5/5 更新官网更新日志并部署"
if [ -f "$SITE_SRC" ]; then
    python3 - "$ROOT" "$SITE_SRC" <<'PY'
import re, sys
root, site = sys.argv[1], sys.argv[2]
cl = open(root + "/CHANGELOG.md").read()
entries = re.findall(r"^## (v[\d.]+) - (\d{4}-\d{2}-\d{2})\n(.*?)(?=^## |\Z)", cl, re.S | re.M)
def render(ver, date, body):
    html = [f'<div class="rel"><b>{ver}</b> · {date}</div>']
    for m in re.finditer(r"^### (\S+)\n((?:- .*\n?)+)", body, re.M):
        items = "".join(f"<li>{i[2:]}</li>" for i in m.group(2).strip().splitlines())
        html.append(f'<div class="tag">{m.group(1)}</div><ul>{items}</ul>')
    return "\n".join(html)
rendered = "\n".join(render(*e) for e in entries[:3])
page = open(site).read()
assert "<!-- CHANGELOG -->" in page, "官网缺少 <!-- CHANGELOG --> 标记"
open(site, "w").write(page.replace("<!-- CHANGELOG -->", rendered))
print("  已注入最新 3 个版本条目")
PY
    sudo cp "$SITE_SRC" "$SITE_DST" && sudo chown www:www "$SITE_DST"
    echo "  官网已部署: https://openmcserver.cn/1b1t/"
else
    echo "  未找到官网源码, 跳过 ($SITE_SRC)"
fi

echo "完成! 安装方法:"
echo "  curl -fsSL https://raw.githubusercontent.com/$REPO/main/1b1t-apt-key.gpg | sudo tee /etc/apt/keyrings/1b1t.gpg >/dev/null"
echo "  echo 'deb [signed-by=/etc/apt/keyrings/1b1t.gpg] https://raw.githubusercontent.com/$REPO/gh-pages/ stable main' | sudo tee /etc/apt/sources.list.d/1b1t.list"
echo "  sudo apt update && sudo apt install 1b1t-open-server"
