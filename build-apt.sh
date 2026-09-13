#!/bin/bash
# 构建 deb + APT 仓库 + 更新官网更新日志, 推送到 GitHub (main + gh-pages)
# 用法: ./build-apt.sh [版本号]   默认 1.0.0
# 发布前先编辑 CHANGELOG.md, 在顶部加 "## vX.Y.Z - 日期" 条目(### 新增/### 修复)
set -euo pipefail

VER="${1:-1.0.0}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
SITE_SRC="${SITE_SRC:-$ROOT/../openmc-pan-build/1b1t/index.html}"
SITE_DST="/www/wwwroot/www.1b1t.cn/index.html"
DOCS_SRC="${DOCS_SRC:-$ROOT/../openmc-pan-build/1b1t/docs.html}"
MIRROR_PANEL_SRC="${MIRROR_PANEL_SRC:-$ROOT/../openmc-pan-build/mirror/index.php}"
APT_DST="/www/wwwroot/www.1b1t.cn/1b1t-apt"
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
Homepage: https://www.1b1t.cn/
Description: Minecraft 一键开服工具 (1b1t)
 向导式开服: 选择版本/目录/端口/常见配置, 高级选项可编辑
 server.properties 全部项; 自动下载服务端核心、自动匹配 Java、
 doctor 自主排查问题; 支持 start/stop/restart/status/console。
EOF
dpkg-deb --root-owner-group -b "$WORK/deb" "$WORK/1b1t-open-server_${VER}_all.deb"

# Windows / macOS 版 (脚本 + 一键安装: 装完终端直接输 1b1t)
mkdir -p "$WORK/win/1b1t-open-server" "$WORK/mac"
cp "$ROOT/1b1t" "$WORK/win/1b1t-open-server/1b1t.py"
cp "$ROOT/1b1t" "$WORK/mac/1b1t"
chmod +x "$WORK/mac/1b1t"
# Windows: 安装.bat 装到 Python Scripts 目录(在 PATH), 之后终端输入 1b1t 启动
cat > "$WORK/win/1b1t-open-server/安装.bat" <<'EOF'
@echo off
chcp 65001 >nul
echo ===== 1b1t 一键安装 =====
for /f "delims=" %%i in ('python -c "import sys,os;print(os.path.dirname(sys.executable))"') do set PYDIR=%%i
if not exist "%PYDIR%\Scripts" mkdir "%PYDIR%\Scripts"
copy /y "%~dp01b1t.py" "%PYDIR%\Scripts\1b1t.py" >nul
> "%PYDIR%\Scripts\1b1t.bat" echo @echo off
>> "%PYDIR%\Scripts\1b1t.bat" echo python "%PYDIR%\Scripts\1b1t.py" %%*
echo.
echo 安装完成! 重新打开终端, 输入 1b1t 即可启动
echo (如果提示找不到命令, 请确认 Python 安装时勾选了 Add to PATH)
pause
EOF
cat > "$WORK/win/1b1t-open-server/安装说明.txt" <<'EOF'
1b1t-open-server Windows 版

1. 安装 Python 3.8+: https://www.python.org/downloads/
   (安装时勾选 "Add Python to PATH")
2. 双击 "安装.bat" 一键安装
3. 重新打开终端(CMD/PowerShell), 输入 1b1t 启动
4. 完整说明: https://www.1b1t.cn/
EOF
# macOS: install.sh 装到 /usr/local/bin, 之后终端输入 1b1t 启动
cat > "$WORK/mac/install.sh" <<'EOF'
#!/bin/bash
# 1b1t 一键安装 (macOS)
set -e
D=/usr/local/bin
if [ ! -w "$D" ]; then sudo mkdir -p "$D"; sudo cp 1b1t "$D/1b1t"; sudo chmod +x "$D/1b1t"
else cp 1b1t "$D/1b1t"; chmod +x "$D/1b1t"; fi
echo "安装完成! 重新打开终端, 输入 1b1t 即可启动"
EOF
chmod +x "$WORK/mac/install.sh"
cat > "$WORK/mac/安装说明.txt" <<'EOF'
1b1t-open-server macOS 版

1. 安装 Python 3: brew install python3
2. 终端运行: ./install.sh 一键安装
3. 重新打开终端, 输入 1b1t 启动
4. 完整说明: https://www.1b1t.cn/
EOF
(cd "$WORK/win" && zip -qr "$WORK/1b1t-open-server_${VER}_windows.zip" 1b1t-open-server)
(cd "$WORK/mac" && tar czf "$WORK/1b1t-open-server_${VER}_macos.tar.gz" 1b1t install.sh 安装说明.txt)

# amd64 独立二进制 (免 Python, 单文件直接跑)
mkdir -p "$WORK/amd64/1b1t-open-server"
python3 -m PyInstaller --onefile --name 1b1t --distpath "$WORK/dist" \
    --workpath "$WORK/pyi" "$ROOT/1b1t" >/dev/null 2>&1 \
    || { pip3 install --break-system-packages pyinstaller >/dev/null 2>&1; \
         python3 -m PyInstaller --onefile --name 1b1t --distpath "$WORK/dist" \
             --workpath "$WORK/pyi" "$ROOT/1b1t" >/dev/null 2>&1; }
cp "$WORK/dist/1b1t" "$WORK/amd64/1b1t-open-server/1b1t"
cat > "$WORK/amd64/1b1t-open-server/install.sh" <<'EOF'
#!/bin/bash
# 1b1t 一键安装 (amd64 独立版, 免 Python)
set -e
D=/usr/local/bin
if [ ! -w "$D" ]; then sudo mkdir -p "$D"; sudo cp 1b1t "$D/1b1t"; sudo chmod +x "$D/1b1t"
else cp 1b1t "$D/1b1t"; chmod +x "$D/1b1t"; fi
echo "安装完成! 重新打开终端, 输入 1b1t 即可启动"
EOF
chmod +x "$WORK/amd64/1b1t-open-server/install.sh"
cat > "$WORK/amd64/1b1t-open-server/安装说明.txt" <<'EOF'
1b1t-open-server amd64 独立版 (免安装 Python)

1. 解压后运行: ./install.sh 一键安装
2. 重新打开终端, 输入 1b1t 即可启动 (arm64 机器请用 deb 包)
3. 完整说明: https://www.1b1t.cn/
EOF
(cd "$WORK/amd64" && tar czf "$WORK/1b1t-open-server_${VER}_amd64.tar.gz" 1b1t-open-server)

# 平台包汇总到 download/ 目录 (deb 为 all 架构, 支持 amd64/arm64)
mkdir -p "$ROOT/download"
cp "$WORK/1b1t-open-server_${VER}_windows.zip" "$ROOT/download/"
cp "$WORK/1b1t-open-server_${VER}_macos.tar.gz" "$ROOT/download/"
cp "$WORK/1b1t-open-server_${VER}_amd64.tar.gz" "$ROOT/download/"
cp "$WORK/1b1t-open-server_${VER}_all.deb" "$ROOT/download/"

echo "==> 2/5 生成 APT 仓库索引 (保留所有历史版本 deb)"
rm -rf "$ROOT/apt/dists"   # 索引重建, pool 里的历史版本 deb 全部保留
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
# main 分支全量文件 (脚本/文档/apt 目录/三平台包)
MAIN_FILES=()
for f in 1b1t README.md LICENSE CHANGELOG.md build-apt.sh 1b1t-apt-key.gpg \
         $(cd apt && find . -type f | sed 's|^\./||') \
         $(cd download 2>/dev/null && find . -type f | sed 's|^\./||'); do
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
    # 每个版本一个可展开的卡片, 点击查看详细变更
    html = ['<details class="ver-card">',
            f'<summary><b>{ver}</b><span class="vdate">{date}</span></summary>']
    for m in re.finditer(r"^### (\S+)\n((?:- .*\n?)+)", body, re.M):
        items = "".join(f"<li>{i[2:]}</li>" for i in m.group(2).strip().splitlines())
        html.append(f'<div class="tag">{m.group(1)}</div><ul>{items}</ul>')
    html.append('</details>')
    return "\n".join(html)
rendered = "\n".join(render(*e) for e in entries)
page = open(site).read()
pat = r"<!-- CHANGELOG_START -->.*?<!-- CHANGELOG_END -->"
assert re.search(pat, page, re.S), "官网缺少 CHANGELOG_START/END 标记"
page = re.sub(
    pat, "<!-- CHANGELOG_START -->\n" + rendered + "\n  <!-- CHANGELOG_END -->",
    page, flags=re.S)
# 顶部版本徽章同步为最新版本 (entries[0][0] 已含 v 前缀)
if entries:
    page = re.sub(r'(badge">)v+[\d.]+', rf"\1{entries[0][0]}", page)
open(site, "w").write(page)
print(f"  已注入全部 {len(entries)} 个版本条目, 徽章更新为 {entries[0][0]}")
PY
    sudo cp "$SITE_SRC" "$SITE_DST" && sudo chown www:www "$SITE_DST"
    [ -f "$DOCS_SRC" ] && sudo mkdir -p "$(dirname "$SITE_DST")/docs" \
        && sudo cp "$DOCS_SRC" "$(dirname "$SITE_DST")/docs/index.html" \
        && sudo chown www:www "$(dirname "$SITE_DST")/docs/index.html"
    echo "  官网已部署: https://www.1b1t.cn/ (含 /docs/ 教程)"
else
    echo "  未找到官网源码, 跳过 ($SITE_SRC)"
fi

echo "==> 6/6 同步 apt 仓库 + 三平台包 + 镜像面板到官网"
if [ -d "$(dirname "$APT_DST")" ]; then
    sudo mkdir -p "$APT_DST" "$(dirname "$APT_DST")/mirror" "$(dirname "$APT_DST")/download"
    sudo cp -r "$ROOT"/apt/. "$APT_DST"/
    [ -f "$MIRROR_PANEL_SRC" ] && sudo cp "$MIRROR_PANEL_SRC" "$(dirname "$APT_DST")/mirror/"
    sudo cp "$ROOT"/download/* "$(dirname "$APT_DST")/download/"
    sudo chown -R www:www "$APT_DST" "$(dirname "$APT_DST")/mirror" "$(dirname "$APT_DST")/download"
    echo "  已同步: https://www.1b1t.cn/1b1t-apt/ + /download/ (win/mac/linux)"
else
    echo "  未找到站点目录, 跳过"
fi

echo "完成! 安装方法:"
echo "  curl -fsSL https://www.1b1t.cn/1b1t-apt-key.gpg | sudo tee /etc/apt/keyrings/1b1t.gpg >/dev/null"
echo "  echo 'deb [signed-by=/etc/apt/keyrings/1b1t.gpg] https://www.1b1t.cn/1b1t-apt/ stable main' | sudo tee /etc/apt/sources.list.d/1b1t.list"
echo "  sudo apt update && sudo apt install 1b1t-open-server"
