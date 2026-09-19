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
if [ -f "$ROOT/dist/1b1t-linux" ] && [ -f "$ROOT/dist/1b1t-gui" ]; then
    # 图形版 deb: 编译好的二进制 (无需 python3), 桌面入口, 终端 1b1t 可用
    mkdir -p "$WORK/deb/usr/share/applications"
    install -m755 "$ROOT/dist/1b1t-linux" "$WORK/deb/usr/local/bin/1b1t"
    install -m755 "$ROOT/dist/1b1t-gui" "$WORK/deb/usr/local/bin/1b1t-gui"
    ln -s 1b1t "$WORK/deb/usr/local/bin/1b1t-open-server"
    cat > "$WORK/deb/usr/share/applications/1b1t.desktop" <<'EOF'
[Desktop Entry]
Name=1b1t 开服工具
Name[en]=1b1t Server Tool
Comment=Minecraft 一键开服工具 (图形+命令行)
Exec=/usr/local/bin/1b1t-gui
Icon=1b1t
StartupWMClass=1b1t-gui
Terminal=false
Type=Application
Categories=Game;Utility;
EOF
    # 桌面图标 (软件封面, 云盘 logo)
    if [ -f "$ROOT/assets/1b1t.png" ]; then
        mkdir -p "$WORK/deb/usr/share/icons/hicolor/128x128/apps"
        install -m644 "$ROOT/assets/1b1t.png" \
            "$WORK/deb/usr/share/icons/hicolor/128x128/apps/1b1t.png"
    fi
    cat > "$WORK/deb/DEBIAN/control" <<EOF
Package: 1b1t-open-server
Version: $VER
Section: utils
Priority: optional
Architecture: amd64
Maintainer: 1b1t <3835689650@users.noreply.github.com>
Homepage: https://www.1b1t.cn/
Description: Minecraft 一键开服工具 (1b1t) 图形版
 苹果风液态玻璃图形界面: 服务器列表/开服向导/启动停止/实时日志;
 终端输 1b1t 可用命令行版; 修改服务器名字/副标题/端口/人数/内存;
 自动下载服务端核心、自动匹配 Java、doctor 自主排查。
EOF
    DEB_OUT="$WORK/1b1t-open-server_${VER}_amd64.deb"
else
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
    DEB_OUT="$WORK/1b1t-open-server_${VER}_all.deb"
fi
dpkg-deb --root-owner-group -b "$WORK/deb" "$DEB_OUT"

# Windows / macOS 版 (有预生成的 msi/dmg 则直接使用: 编译好的 exe 无需 Python)
if [ -f "$ROOT/1b1t-open-server_${VER}_windows.msi" ]; then
    cp "$ROOT/1b1t-open-server_${VER}_windows.msi" "$WORK/"
else
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
fi   # 结束 msi 存在分支

if [ -f "$ROOT/1b1t-open-server_${VER}_macos.dmg" ]; then
    cp "$ROOT/1b1t-open-server_${VER}_macos.dmg" "$WORK/"
fi

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

# arm64 独立二进制 (qemu 交叉打包, 需要 /opt/arm64-root 环境)
if [ -x /opt/arm64-root/bin/bash ]; then
    sudo cp /usr/bin/qemu-aarch64-static /opt/arm64-root/usr/bin/ 2>/dev/null || true
    sudo cp "$ROOT/1b1t" /opt/arm64-root/tmp/1b1t
    sudo chroot /opt/arm64-root /bin/bash -c \
        "cd /tmp && rm -rf dist build && python3 -m PyInstaller --onefile --name 1b1t 1b1t" \
        >/dev/null 2>&1
    mkdir -p "$WORK/arm64/1b1t-open-server"
    sudo cp /opt/arm64-root/tmp/dist/1b1t "$WORK/arm64/1b1t-open-server/1b1t"
    sudo chown "$(id -u):$(id -g)" "$WORK/arm64/1b1t-open-server/1b1t"
    cat > "$WORK/arm64/1b1t-open-server/install.sh" <<'EOF'
#!/bin/bash
# 1b1t 一键安装 (arm64 独立版, 免 Python)
set -e
D=/usr/local/bin
if [ ! -w "$D" ]; then sudo mkdir -p "$D"; sudo cp 1b1t "$D/1b1t"; sudo chmod +x "$D/1b1t"
else cp 1b1t "$D/1b1t"; chmod +x "$D/1b1t"; fi
echo "安装完成! 重新打开终端, 输入 1b1t 即可启动"
EOF
    chmod +x "$WORK/arm64/1b1t-open-server/install.sh"
    cat > "$WORK/arm64/1b1t-open-server/安装说明.txt" <<'EOF'
1b1t-open-server arm64 独立版 (免安装 Python)

1. 解压后运行: ./install.sh 一键安装
2. 重新打开终端, 输入 1b1t 即可启动
3. 完整说明: https://www.1b1t.cn/
EOF
    (cd "$WORK/arm64" && tar czf "$WORK/1b1t-open-server_${VER}_arm64.tar.gz" 1b1t-open-server)
fi

# 平台包汇总到 download/ 目录
mkdir -p "$ROOT/download"
for f in windows.zip windows.msi macos.tar.gz macos.dmg amd64.tar.gz arm64.tar.gz; do
    [ -f "$WORK/1b1t-open-server_${VER}_$f" ] \
        && cp "$WORK/1b1t-open-server_${VER}_$f" "$ROOT/download/"
done
cp "$DEB_OUT" "$ROOT/download/"

echo "==> 2/5 生成 APT 仓库索引 (保留所有历史版本 deb)"
rm -rf "$ROOT/apt/dists"   # 索引重建, pool 里的历史版本 deb 全部保留
mkdir -p "$ROOT/apt/pool/main/1b1t-open-server" \
         "$ROOT/apt/dists/stable/main/binary-all" \
         "$ROOT/apt/dists/stable/main/binary-amd64"
cp "$DEB_OUT" "$ROOT/apt/pool/main/1b1t-open-server/"
(cd "$ROOT/apt" && dpkg-scanpackages --arch all pool/ \
    > dists/stable/main/binary-all/Packages)
gzip -9kf "$ROOT/apt/dists/stable/main/binary-all/Packages"
if [ "${DEB_OUT##*.}" = "deb" ] && [ "$(dpkg-deb -f "$DEB_OUT" Architecture)" = "amd64" ]; then
    (cd "$ROOT/apt" && dpkg-scanpackages --arch amd64 pool/ \
        > dists/stable/main/binary-amd64/Packages)
    gzip -9kf "$ROOT/apt/dists/stable/main/binary-amd64/Packages"
fi

echo "==> 3/5 签名 Release"
cd "$ROOT/apt/dists/stable"
{
    echo "Origin: 1b1t"
    echo "Label: 1b1t apt repo"
    echo "Suite: stable"
    echo "Codename: stable"
    echo "Architectures: all amd64"
    echo "Components: main"
    echo "Date: $(date -R -u)"
    echo "Valid-Until: $(date -R -u -d '+1 year')"
    for algo in sha256sum sha512sum; do
        echo "${algo%sum}:"
        for d in main/binary-all main/binary-amd64; do
            [ -d "$d" ] || continue
            for f in "$d"/Packages "$d"/Packages.gz; do
                read h _ <<< "$($algo "$f")"
                echo " $h $(stat -c%s "$f") $f"
            done
        done
    done
} > Release
gpg --batch --yes --digest-algo SHA512 --personal-digest-preferences SHA512 \
    --clearsign -o InRelease Release
cd "$ROOT"

echo "==> 4/5 推送 GitHub (git push 失败时自动走 API)"
# API 上传单文件 (github.com 被墙时的替代)
# 小文件走 Contents API; 大文件(>1MB)上传到 GitHub Release 资产(永久保留)
api_put() { # 本地文件 仓库路径 分支
    if [ "$(stat -c%s "$1")" -gt 1048576 ]; then
        gh release view "v$VER" --repo "$REPO" >/dev/null 2>&1 || \
            gh release create "v$VER" --repo "$REPO" --title "v$VER" \
                --notes "1b1t-open-server v$VER 安装包(Windows MSI / macOS dmg / Linux deb)" \
                >/dev/null 2>&1
        gh release upload "v$VER" "$1" --repo "$REPO" --clobber >/dev/null 2>&1
        echo "  Release: $(basename "$1")"
    else
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
    fi
}
# main 分支全量文件 (脚本/文档/apt 目录/三平台包)
# 注意: find 输出不带目录前缀, 必须手动加回 apt/ download/ 前缀,
# 否则后面 case download/* 的版本过滤永远不生效, 且存在检测会误检根目录
MAIN_FILES=()
for f in 1b1t gui.py assets/logo.jpeg assets/1b1t.png README.md LICENSE \
         CHANGELOG.md build-apt.sh 1b1t-apt-key.gpg; do
    [ -f "$ROOT/$f" ] && MAIN_FILES+=("$f")
done
for f in $(cd apt && find . -type f | sed 's|^\./||'); do
    [ -f "$ROOT/apt/$f" ] && MAIN_FILES+=("apt/$f")
done
for f in $(cd download 2>/dev/null && find . -type f | sed 's|^\./||'); do
    [ -f "$ROOT/download/$f" ] && MAIN_FILES+=("download/$f")
done
# github.com 被墙: git push 会挂几分钟, timeout 快速失败走 API
if git add -A && git commit -m "release $VER" --quiet 2>/dev/null \
   && timeout 25 git push origin main --quiet 2>/dev/null; then
    echo "  main: git push 成功"
else
    echo "  main: git push 失败, 走 API"
    for f in "${MAIN_FILES[@]}"; do
        # 历史版本安装包(大文件)已在各自 Release 资产里, 不重复传
        case "$f" in
            download/*)
                [[ "$f" == *"_${VER}_"* ]] || continue ;;
        esac
        api_put "$ROOT/$f" "$f" main || true
    done
fi
# gh-pages 只放 apt/ 目录内容
git worktree prune
if git worktree add -B gh-pages "$WORK/pages" --quiet 2>/dev/null; then
    find "$WORK/pages" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
    cp -r "$ROOT"/apt/. "$WORK/pages/"
    if git -C "$WORK/pages" add -A && git -C "$WORK/pages" commit -m "apt $VER" --quiet \
       && timeout 25 git -C "$WORK/pages" push -f origin gh-pages \
            --quiet 2>/dev/null; then
        echo "  gh-pages: git push 成功"
    else
        echo "  gh-pages: git push 失败, 走 API"
        for f in $(cd apt && find . -type f | sed 's|^\./||'); do
            api_put "$ROOT/apt/$f" "$f" gh-pages || true
        done
    fi
    git worktree remove "$WORK/pages" --force
else
    echo "  gh-pages: git push 失败, 走 API"
    for f in $(cd apt && find . -type f | sed 's|^\./||'); do
        api_put "$ROOT/apt/$f" "$f" gh-pages || true
    done
fi

echo "==> 5/5 更新官网更新日志并部署"
if [ -f "$SITE_SRC" ]; then
    python3 - "$ROOT" "$SITE_SRC" "$VER" <<'PY'
import re, sys
root, site, ver = sys.argv[1], sys.argv[2], sys.argv[3]
cl = open(root + "/CHANGELOG.md").read()
entries = re.findall(r"^## (v[\d.]+) - (\d{4}-\d{2}-\d{2})\n(.*?)(?=^## |\Z)", cl, re.S | re.M)
def render(ver, date, body):
    # 每个版本一个可展开的卡片, 点击查看详细变更
    html = ['<details class="ver-card">',
            f'<summary><b>{ver}</b> <span class="vdate">{date}</span></summary>']
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
# 顶部版本徽章同步为实际最新版本号 (整合版 changelog 条目名 ≠ 实际版本)
if entries:
    page = re.sub(r'(badge">)v+[\d.]+', r"\1v" + ver, page)
open(site, "w").write(page)
print(f"  已注入全部 {len(entries)} 个版本条目, 徽章更新为 v{ver}")
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
