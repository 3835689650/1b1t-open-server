#!/usr/bin/env python3
"""生成 Windows MSI 安装包 (msitools 组装, 无需 Windows 环境)

安装内容 (都是编译好的 exe, 用户不需要装 Python):
  %LOCALAPPDATA%\\1b1t\\1b1t.exe     命令行版
  %LOCALAPPDATA%\\1b1t\\1b1t-gui.exe 图形版(液态玻璃界面)
  用户 PATH 追加 %LOCALAPPDATA%\\1b1t -> 终端输 1b1t 可用
  开始菜单 + 桌面快捷方式 "1b1t 开服工具" -> 双击打开图形版

用法: python3 gen-msi.py <cli.exe> <gui.exe> <版本号> <输出.msi>
"""
import os
import re
import subprocess
import sys
import tempfile
import uuid

CLI_EXE, GUI_EXE, VER, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

if not re.match(r"^\d+\.\d+\.\d+$", VER):
    sys.exit("版本号必须是 X.Y.Z 三段数字 (MSI 要求): " + VER)

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
             "Environment": ["S255", "S255", "S255", "S255"]}
    keys = {"Property": ["Property"], "Directory": ["Directory"],
            "Component": ["Component"], "Feature": ["Feature"],
            "FeatureComponents": ["Feature_", "Component_"],
            "File": ["File"], "Media": ["DiskId"], "Shortcut": ["Shortcut"],
            "Environment": ["Environment"]}
    with open(os.path.join(tmp, name + ".idt"), "w", encoding="utf-8",
              newline="\r\n") as f:
        f.write("\t".join(cols) + "\r\n")
        f.write("\t".join(types[name]) + "\r\n")
        f.write("\t".join(keys[name]) + "\r\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\r\n")


try:
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
        ("clicomp", "{" + G["PY"] + "}", "INSTALLDIR", 0, "", "1b1t.exe"),
        ("guicomp", "{" + G["BAT"] + "}", "INSTALLDIR", 0, "", "1b1t-gui.exe"),
        ("envcomp", "{" + G["ENV"] + "}", "INSTALLDIR", 0, "", "ENV_1b1t"),
        ("startcomp", "{" + G["START"] + "}", "PROGDIR", 0, "", "SC_1b1t"),
        ("deskcomp", "{" + G["DESK"] + "}", "DESKTOPDIR", 0, "", "SC_1b1t_D"),
    ])
    idt("Feature", ["Feature", "Feature_Parent", "Title", "Description",
                    "Display", "Level", "Directory_", "Attributes"], [
        ("Main", "", "1b1t 一键开服", "Minecraft 一键开服工具 (图形+命令行)", 1,
         1, "INSTALLDIR", 0),
    ])
    idt("FeatureComponents", ["Feature_", "Component_"], [
        ("Main", c) for c in
        ("clicomp", "guicomp", "envcomp", "startcomp", "deskcomp")
    ])
    idt("File", ["File", "Component_", "FileName", "FileSize", "Version",
                 "Language", "Attributes", "Sequence"], [
        ("1b1t.exe", "clicomp", "1b1t.exe", os.path.getsize(CLI_EXE), "", "",
         0, 1),
        ("1b1t-gui.exe", "guicomp", "1b1t-gui.exe",
         os.path.getsize(GUI_EXE), "", "", 0, 2),
    ])
    idt("Media", ["DiskId", "LastSequence", "DiskPrompt", "Cabinet",
                  "VolumeLabel", "Source"], [
        (1, 2, "", "", "", ""),  # Cabinet 空 = 文件以独立 stream 存储(未压缩)
    ])
    idt("Shortcut", ["Shortcut", "Directory_", "Name", "Component_", "Target",
                     "Arguments", "Description", "Hotkey", "Icon_",
                     "IconIndex", "ShowCmd", "WkDir"], [
        ("SC_1b1t", "PROGDIR", "1b1t 开服工具", "startcomp",
         "[INSTALLDIR]1b1t-gui.exe", "", "Minecraft 一键开服工具 (图形版)",
         0, "", 0, 1, "INSTALLDIR"),
        ("SC_1b1t_D", "DESKTOPDIR", "1b1t 开服工具", "deskcomp",
         "[INSTALLDIR]1b1t-gui.exe", "", "Minecraft 一键开服工具 (图形版)",
         0, "", 0, 1, "INSTALLDIR"),
    ])
    idt("Environment", ["Environment", "Name", "Value", "Component_"], [
        # '=' 前缀 = 追加到 PATH 尾部
        ("ENV_1b1t", "=PATH", "[INSTALLDIR]", "envcomp"),
    ])

    # 1. 用 libmsi 建库并设 codepage 936 (GBK 存中文快捷方式名)
    if os.path.exists(OUT):
        os.unlink(OUT)
    code = f"""
import gi
gi.require_version('Libmsi', '1.0')
from gi.repository import Libmsi
db = Libmsi.Database.new({OUT!r}, Libmsi.DbFlags.CREATE)
si = Libmsi.SummaryInfo.new(db, 15)
si.set_int(1, 65001)
si.set_string(2, '1b1t-open-server')
si.set_string(3, '1b1t')
si.set_string(9, '{{{G["PRODUCT"]}}}')
si.persist()
db.commit()
"""
    run = subprocess.run([sys.executable, "-c", code],
                         capture_output=True, text=True)
    if run.returncode:
        sys.exit("建库失败: " + run.stderr)

    # 2. 导入各表
    for t in ("Property", "Directory", "Component", "Feature",
              "FeatureComponents", "File", "Media", "Shortcut",
              "Environment"):
        run = subprocess.run(["msibuild", OUT, "-i",
                              os.path.join(tmp, t + ".idt")],
                             capture_output=True, text=True)
        if run.returncode:
            sys.exit(f"msibuild 导入 {t} 失败: " + run.stderr)

    # 3. 加 exe 文件 stream
    for stream, path in (("1b1t.exe", CLI_EXE),
                         ("1b1t-gui.exe", GUI_EXE)):
        run = subprocess.run(["msibuild", OUT, "-a", stream, path],
                             capture_output=True, text=True)
        if run.returncode:
            sys.exit(f"msibuild 加 stream {stream} 失败: " + run.stderr)
finally:
    for f in os.listdir(tmp):
        os.unlink(os.path.join(tmp, f))
    os.rmdir(tmp)

print(f"已生成: {OUT} (v{VER}, {os.path.getsize(OUT)} 字节)")
