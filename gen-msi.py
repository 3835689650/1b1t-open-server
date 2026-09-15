#!/usr/bin/env python3
"""生成 Windows MSI 安装包 (用 msitools 的 msibuild 组装, 无需 Windows 环境)

安装内容:
  %LOCALAPPDATA%\\1b1t\\1b1t.py  主程序
  %LOCALAPPDATA%\\1b1t\\1b1t.bat 启动器 (python "%~dp01b1t.py" %*)
  用户 PATH 追加 %LOCALAPPDATA%\\1b1t  -> 终端输入 1b1t 可用 (命令行)
  开始菜单 + 桌面快捷方式 "1b1t 开服工具" -> 双击打开终端进主菜单 (图形)

用法: python3 gen-msi.py <1b1t源文件> <版本号> <输出.msi>
"""
import os
import re
import subprocess
import sys
import tempfile
import uuid

SRC, VER, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

if not re.match(r"^\d+\.\d+\.\d+$", VER):
    sys.exit("版本号必须是 X.Y.Z 三段数字 (MSI 要求): " + VER)

bat = ('@echo off\r\n'
       'python "%~dp01b1t.py" %*\r\n'
       'if errorlevel 9009 echo [错误] 未找到 python, 请先安装 Python 并勾选 Add to PATH\r\n'
       'if errorlevel 9009 pause\r\n')

G = {k: str(uuid.uuid4()) for k in
     ("PRODUCT", "UPGRADE", "PY", "BAT", "ENV", "START", "DESK")}

tmp = tempfile.mkdtemp()


def idt(name, cols, rows):
    """写 .idt 表文件 (行1=列名, 行2=类型, 行3=主键列名, 之后=数据)"""
    types = {"Property": ["S255", "S255"],
             "Directory": ["S255", "S255", "S255"],
             "Component": ["S255", "S255", "S255", "i2", "S255", "S255"],
             "Feature": ["S255", "S255", "S255", "S255", "i2", "i2",
                         "S255", "i2"],
             "FeatureComponents": ["S255", "S255"],
             "File": ["S255", "S255", "S255", "i4", "S255", "S255", "i2",
                      "i2"],
             "Media": ["i2", "i2", "S255", "S255", "S255", "S255"],
             "Shortcut": ["S255", "S255", "S255", "S255", "S255", "S255",
                          "S255", "i2", "S255", "i2", "i2", "S255"],
             "Environment": ["S255", "S255", "S255", "S255"],
             "_ForceCodepage": ["i2", "S255"]}
    keys = {"Property": ["Property"], "Directory": ["Directory"],
            "Component": ["Component"], "Feature": ["Feature"],
            "FeatureComponents": ["Feature_", "Component_"],
            "File": ["File"], "Media": ["DiskId"], "Shortcut": ["Shortcut"],
            "Environment": ["Environment"], "_ForceCodepage": ["_ForceCodepage"]}
    with open(os.path.join(tmp, name + ".idt"), "w", encoding="utf-8",
              newline="\r\n") as f:
        f.write("\t".join(cols) + "\r\n")
        f.write("\t".join(types[name]) + "\r\n")
        f.write("\t".join(keys[name]) + "\r\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\r\n")


try:
    idt("_ForceCodepage", ["", "_ForceCodepage"], [(0, "936")])  # GBK 存中文
    idt("Property", ["Property", "Value"], [
        ("ProductCode", "{" + G["PRODUCT"] + "}"),
        ("UpgradeCode", "{" + G["UPGRADE"] + "}"),
        ("ProductVersion", VER),
        ("ProductName", "1b1t-open-server"),
        ("Manufacturer", "1b1t"),
        ("ALLUSERS", "2"), ("MSIINSTALLPERUSER", "1"),
    ])
    idt("Directory", ["Directory", "Directory_Parent", "DefaultDir"], [
        ("TARGETDIR", "", "SourceDir"),
        ("INSTALLDIR", "TARGETDIR", "[LocalAppDataFolder]1b1t"),
        ("PROGDIR", "TARGETDIR", "[ProgramMenuFolder]1b1t"),
        ("DESKTOPDIR", "TARGETDIR", "[DesktopFolder]"),
    ])
    idt("Component", ["Component", "ComponentId", "Directory_", "Attributes",
                      "Condition", "KeyPath"], [
        ("pycomp", "{" + G["PY"] + "}", "INSTALLDIR", 0, "", "1b1t.py"),
        ("batcomp", "{" + G["BAT"] + "}", "INSTALLDIR", 0, "", "1b1t.bat"),
        ("envcomp", "{" + G["ENV"] + "}", "INSTALLDIR", 0, "", "ENV_1b1t"),
        ("startcomp", "{" + G["START"] + "}", "PROGDIR", 0, "", "SC_1b1t"),
        ("deskcomp", "{" + G["DESK"] + "}", "DESKTOPDIR", 0, "", "SC_1b1t_D"),
    ])
    idt("Feature", ["Feature", "Feature_Parent", "Title", "Description",
                    "Display", "Level", "Directory_", "Attributes"], [
        ("Main", "", "1b1t 一键开服", "Minecraft 一键开服工具", 1, 1,
         "INSTALLDIR", 0),
    ])
    idt("FeatureComponents", ["Feature_", "Component_"], [
        ("Main", c) for c in
        ("pycomp", "batcomp", "envcomp", "startcomp", "deskcomp")
    ])
    idt("File", ["File", "Component_", "FileName", "FileSize", "Version",
                 "Language", "Attributes", "Sequence"], [
        ("1b1t.py", "pycomp", "1b1t.py", os.path.getsize(SRC), "", "", 0, 1),
        ("1b1t.bat", "batcomp", "1b1t.bat", len(bat.encode()), "", "", 0, 2),
    ])
    idt("Media", ["DiskId", "LastSequence", "DiskPrompt", "Cabinet",
                  "VolumeLabel", "Source"], [
        (1, 2, "", "", "", ""),  # Cabinet 空 = 文件以独立 stream 存储(未压缩)
    ])
    idt("Shortcut", ["Shortcut", "Directory_", "Name", "Component_", "Target",
                     "Arguments", "Description", "Hotkey", "Icon_",
                     "IconIndex", "ShowCmd", "WkDir"], [
        ("SC_1b1t", "PROGDIR", "1b1t 开服工具", "startcomp",
         "[INSTALLDIR]1b1t.bat", "", "Minecraft 一键开服工具", 0, "", 0, 1,
         "INSTALLDIR"),
        ("SC_1b1t_D", "DESKTOPDIR", "1b1t 开服工具", "deskcomp",
         "[INSTALLDIR]1b1t.bat", "", "Minecraft 一键开服工具", 0, "", 0, 1,
         "INSTALLDIR"),
    ])
    idt("Environment", ["Environment", "Name", "Value", "Component_"], [
        # '=' 前缀 = 追加到 PATH 尾部
        ("ENV_1b1t", "=PATH", "[INSTALLDIR]", "envcomp"),
    ])
    with open(os.path.join(tmp, "1b1t.bat"), "w", encoding="utf-8",
              newline="\r\n") as f:
        f.write(bat)

    if os.path.exists(OUT):
        os.unlink(OUT)
    run = subprocess.run(["msibuild", OUT, "-s", "1b1t-open-server", "1b1t",
                          "Installation Database", "{" + G["PRODUCT"] + "}"],
                         capture_output=True, text=True)
    if run.returncode:
        sys.exit("msibuild -s 失败: " + run.stderr)
    for t in ("_ForceCodepage", "Property", "Directory", "Component",
              "Feature", "FeatureComponents", "File", "Media", "Shortcut",
              "Environment"):
        run = subprocess.run(["msibuild", OUT, "-i",
                              os.path.join(tmp, t + ".idt")],
                             capture_output=True, text=True)
        if run.returncode:
            sys.exit(f"msibuild 导入 {t} 失败: " + run.stderr)
    for stream, path in (("1b1t.py", SRC),
                         ("1b1t.bat", os.path.join(tmp, "1b1t.bat"))):
        run = subprocess.run(["msibuild", OUT, "-a", stream, path],
                             capture_output=True, text=True)
        if run.returncode:
            sys.exit(f"msibuild 加 stream {stream} 失败: " + run.stderr)
finally:
    for f in os.listdir(tmp):
        os.unlink(os.path.join(tmp, f))
    os.rmdir(tmp)

print(f"已生成: {OUT} (v{VER}, {os.path.getsize(OUT)} 字节)")
