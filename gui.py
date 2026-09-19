#!/usr/bin/env python3
"""1b1t GUI 版 — 苹果风液态玻璃界面 (PySide6)
功能: 服务器列表/开服向导/启动停止/修改设置(名字·副标题·端口·人数·内存)/实时日志
打包: pyinstaller 三平台 (Windows MSI / macOS 安装包 / Linux deb)"""
import os
import re
import sys
import time

# 复用 1b1t 核心逻辑 (打包时 1b1t 复制为 core1b1t.py)
try:
    import core1b1t as core
except ImportError:
    import importlib.util
    import importlib.machinery
    _path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "1b1t")
    _spec = importlib.util.spec_from_file_location(
        "core1b1t", _path,
        loader=importlib.machinery.SourceFileLoader("core1b1t", _path))
    core = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(core)

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QFrame,
                               QGraphicsBlurEffect, QGraphicsPixmapItem,
                               QGraphicsScene, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QPlainTextEdit, QPushButton,
                               QRadioButton, QComboBox, QVBoxLayout, QWidget,
                               QGridLayout, QButtonGroup, QStackedWidget,
                               QScrollArea)

ANSI = re.compile(r"\x1b\[[0-9;]*m")

# ---------- 液态玻璃主题 (苹果风) ----------
ACCENT = "#0A84FF"      # iOS 蓝
GREEN = "#30D158"
RED = "#FF453A"
YELLOW = "#FFD60A"
TEXT = "#F5F5F7"
DIM = "#98989D"

QSS = f"""
* {{ font-family: "SF Pro Text", "PingFang SC", "Segoe UI",
     "Microsoft YaHei", sans-serif; color: {TEXT}; }}
#Root {{ background: #18181C; }}
#Glass {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(36,36,42,255), stop:0.5 rgba(28,28,32,255),
        stop:1 rgba(24,24,28,255));
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,28);
    border-top: 1px solid rgba(255,255,255,64);
}}
#Sidebar {{ background: rgba(255,255,255,14); border-radius: 18px 0 0 18px;
            border-right: 1px solid rgba(255,255,255,18); }}
#Logo {{ font-size: 24px; font-weight: 700; }}
#Tagline {{ color: {DIM}; font-size: 12px; }}
QPushButton {{
    background: rgba(255,255,255,20); border: 1px solid rgba(255,255,255,30);
    border-radius: 12px; padding: 9px 18px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{ background: rgba(255,255,255,36); }}
QPushButton:pressed {{ background: rgba(255,255,255,50); }}
QPushButton:focus {{ border: 1px solid rgba(10,132,255,180); }}
QPushButton:disabled {{ background: rgba(255,255,255,8);
    color: rgba(245,245,247,80); border-color: rgba(255,255,255,12); }}
QPushButton#Primary {{ background: {ACCENT}; border: none; color: white;
                       font-weight: 600; }}
QPushButton#Primary:hover {{ background: #2A93FF; }}
QPushButton#Primary:disabled {{ background: rgba(10,132,255,80);
    color: rgba(255,255,255,140); }}
QPushButton#Danger {{ background: {RED}; border: none; color: white;
                      font-weight: 600; }}
QPushButton#Danger:hover {{ background: #FF6A61; }}
QPushButton#Danger:disabled {{ background: rgba(255,69,58,80);
    color: rgba(255,255,255,140); }}
QPushButton#WinBtn {{ background: transparent; border: none; border-radius: 8px;
    padding: 0; font-size: 13px; font-weight: 700; }}
QPushButton#WinBtn:hover {{ background: rgba(255,255,255,24); }}
QPushButton#NavBtn {{ background: transparent; border: none; border-radius: 10px;
    padding: 10px 14px; font-size: 13px; font-weight: 500; text-align: left; }}
QPushButton#NavBtn:hover {{ background: rgba(255,255,255,16); }}
QPushButton#NavBtn:checked {{ background: rgba(10,132,255,40);
    color: white; font-weight: 600; }}
QLineEdit, QComboBox {{
    background: rgba(255,255,255,14); border: 1px solid rgba(255,255,255,28);
    border-radius: 10px; padding: 8px 12px; font-size: 13px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: rgba(44,44,48,235); border: 1px solid rgba(255,255,255,30);
    border-radius: 12px; selection-background-color: {ACCENT};
}}
QListWidget {{ background: transparent; border: none; outline: 0; }}
QListWidget::item {{ border-radius: 12px; padding: 10px 12px; margin: 2px 4px; }}
QListWidget::item:hover {{ background: rgba(255,255,255,16); }}
QListWidget::item:selected {{ background: rgba(10,132,255,50);
                              border: 1px solid rgba(10,132,255,120); }}
#ServerName {{ font-size: 24px; font-weight: 700;
               font-family: "SF Pro Display", "PingFang SC", "Segoe UI",
               sans-serif; }}
#ServerSub {{ color: {DIM}; font-size: 13px; }}
#InfoChip {{ background: rgba(255,255,255,14);
             border: 1px solid rgba(255,255,255,26); border-radius: 10px;
             padding: 7px 14px; font-size: 12px; color: #D8D8DD; }}
#InfoChip b {{ color: {TEXT}; font-weight: 600; }}
#CardTitle {{ font-size: 13px; font-weight: 600; color: #C8C8CE; }}
#LogBox {{
    background: rgba(0,0,0,72); border: 1px solid rgba(255,255,255,20);
    border-radius: 14px; padding: 10px; font-family: "SF Mono", Consolas,
    monospace; font-size: 12px;
}}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent;
    border: none; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: rgba(255,255,255,40);
    border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QMessageBox, QDialog {{ background: rgba(36,36,40,238); }}
QDialog QLabel {{ font-size: 13px; }}
QRadioButton {{ font-size: 13px; spacing: 6px; }}
QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 8px;
    border: 1px solid rgba(255,255,255,60); background: transparent; }}
QRadioButton::indicator:checked {{ background: {ACCENT}; border: none; }}
QPushButton#SegBtn {{ background: rgba(255,255,255,12); border: none;
    border-radius: 10px; padding: 5px 14px; color: {DIM}; font-size: 12px; }}
QPushButton#SegBtn:checked {{ background: rgba(10,132,255,60);
    color: {TEXT}; }}
QPlainTextEdit {{ background: rgba(0,0,0,72);
    border: 1px solid rgba(255,255,255,20); border-radius: 10px;
    padding: 8px; font-family: "SF Mono", Consolas, monospace;
    font-size: 12px; }}
"""


def glass_effect(win):
    """Windows 11: DWM 圆角 + Mica 背景
    返回 Mica 是否设置成功 (Win10/失败时调用方回退不透明玻璃)"""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        hwnd = int(win.winId())
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWMWCP_ROUND = 2
        DWMSBT_MAINWINDOW = 2
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 4)
        ok = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(ctypes.c_int(DWMSBT_MAINWINDOW)), 4)
        return ok == 0  # S_OK 才算 Mica 生效
    except Exception:
        return False


class StartThread(QThread):
    log = Signal(str)
    done = Signal(bool, str)  # (成功?, 失败原因)

    def __init__(self, server_dir, cfg):
        super().__init__()
        self.server_dir, self.cfg = server_dir, cfg

    def run(self):
        try:
            ok, detail = core.api_start(self.server_dir, self.cfg,
                                        self.log.emit)
            if not ok and not detail:
                # 启动进程失败: 取日志尾部关键报错行提示用户
                detail = core._tail_error(self.server_dir) or \
                    "服务器进程启动失败, 请展开日志查看详情"
            self.done.emit(ok, detail or "")
        except BaseException as e:
            # 任何异常(缺 Java 的 SystemExit/网络失败等)都要发 done,
            # 否则启动按钮永久禁用 → "启动不了"
            self.done.emit(False, f"启动过程出错: {e}")


class BackupThread(QThread):
    """后台打包存档 (大世界打包耗时不卡 UI)"""
    log = Signal(str)
    done = Signal(bool)

    def __init__(self, server_dir):
        super().__init__()
        self.server_dir = server_dir
        self.auto = False  # 自动备份失败只记日志不弹窗

    def run(self):
        ok = core.backup_world(self.server_dir, self.log.emit) is not None
        self.done.emit(ok)


class _EmitIO:
    """把 print 输出实时转发到 GUI 日志 (停止过程不再无反馈)"""

    def __init__(self, emit):
        self.emit = emit

    def write(self, s):
        for line in str(s).splitlines():
            if line.strip():
                self.emit(line)

    def flush(self):
        pass


class StopThread(QThread):
    log = Signal(str)
    done = Signal()

    def __init__(self, server_dir):
        super().__init__()
        self.server_dir = server_dir

    def run(self):
        import contextlib
        try:
            with contextlib.redirect_stdout(_EmitIO(self.log.emit)):
                core.do_stop(self.server_dir)
        except BaseException as e:
            self.log.emit(f"[错误] 停止过程出错: {e}")
        self.done.emit()  # 保证 done 一定发出, 停止按钮不卡死


class ModVersThread(QThread):
    """后台拉取 mod 加载器版本列表"""
    done = Signal(str, list)

    def __init__(self, mc_ver, stype):
        super().__init__()
        self.mc_ver, self.stype = mc_ver, stype

    def run(self):
        self.done.emit(self.stype, core.list_mod_versions(self.mc_ver,
                                                          self.stype))


class SettingsDialog(QDialog):
    """软件设置: 版本号 / 自定义背景 / 定时备份 / 默认配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        self.setWindowTitle("设置")
        self.setFixedWidth(440)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        # 版本号
        ver = QLabel(f"1b1t-open-server   v{core.APP_VERSION}")
        ver.setStyleSheet(f"font-size:16px;font-weight:700;color:{TEXT}")
        lay.addWidget(ver)

        # 自定义背景
        lay.addWidget(QLabel("自定义背景"))
        bg_row = QHBoxLayout()
        self.bg_name = QLabel("(无, 深色背景)")
        self.bg_name.setStyleSheet(f"color:{DIM};font-size:12px")
        bg_row.addWidget(self.bg_name, 1)
        pick = QPushButton("选择图片")
        pick.clicked.connect(self.pick_bg)
        clear = QPushButton("清除")
        clear.clicked.connect(self.clear_bg)
        bg_row.addWidget(pick)
        bg_row.addWidget(clear)
        lay.addLayout(bg_row)

        # 定时备份
        lay.addWidget(QLabel("定时备份"))
        bak_row = QHBoxLayout()
        self.bak_plan = QComboBox()
        self.bak_plan.addItems(["关", "每 30 分钟", "每 1 小时",
                                "每 2 小时", "每 6 小时", "每 12 小时",
                                "每 24 小时"])
        bak_row.addWidget(self.bak_plan, 1)
        bak_row.addWidget(QLabel("保留份数"))
        self.bak_keep = QLineEdit()
        self.bak_keep.setFixedWidth(64)
        bak_row.addWidget(self.bak_keep)
        lay.addLayout(bak_row)

        # 默认配置 (简单模式新服使用)
        lay.addWidget(QLabel("新服务器默认配置"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(QLabel("正版验证"), 0, 0)
        self.online = QComboBox()
        self.online.addItems(["开", "关"])
        grid.addWidget(self.online, 0, 1)
        grid.addWidget(QLabel("难度"), 0, 2)
        self.diff = QComboBox()
        self.diff.addItems(["peaceful", "easy", "normal", "hard"])
        grid.addWidget(self.diff, 0, 3)
        grid.addWidget(QLabel("默认 MOTD"), 1, 0)
        self.motd = QLineEdit()
        grid.addWidget(self.motd, 1, 1, 1, 3)
        grid.addWidget(QLabel("死亡不掉落"), 2, 0)
        self.keep = QComboBox()
        self.keep.addItems(["开", "关"])
        grid.addWidget(self.keep, 2, 1)
        lay.addLayout(grid)

        save = QPushButton("保存设置")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_all)
        lay.addWidget(save)
        self.reload_vals()

    def reload_vals(self):
        st = core.load_settings()
        bg = st.get("bg_image", "")
        self.bg_name.setText(os.path.basename(bg) if bg else "(无, 深色背景)")
        try:
            mins = int(st.get("backup_interval_min", "0") or 0)
        except (ValueError, TypeError):
            mins = 0
        plan = {0: 0, 30: 1, 60: 2, 120: 3, 360: 4, 720: 5, 1440: 6}
        self.bak_plan.setCurrentIndex(plan.get(mins, 0))
        self.bak_keep.setText(str(st.get("backup_keep", "10")))
        self.online.setCurrentIndex(0 if st["online_mode"] == "true" else 1)
        self.diff.setCurrentText(st["difficulty"])
        self.motd.setText(st["motd"])
        self.keep.setCurrentIndex(
            0 if st["keep_inventory"] == "true" else 1)

    def pick_bg(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "",
            "图片 (*.png *.jpg *.jpeg *.bmp *.webp)")
        if f:
            st = core.load_settings()
            st["bg_image"] = f
            core.save_settings(st)
            self.reload_vals()
            if self.parent_win:
                self.parent_win.apply_background()

    def clear_bg(self):
        st = core.load_settings()
        st.pop("bg_image", None)
        core.save_settings(st)
        self.reload_vals()
        if self.parent_win:
            self.parent_win.apply_background()

    def save_all(self):
        st = core.load_settings()
        plan = {0: "0", 1: "30", 2: "60", 3: "120", 4: "360", 5: "720",
                6: "1440"}
        st["backup_interval_min"] = plan[self.bak_plan.currentIndex()]
        keep = self.bak_keep.text().strip()
        if keep.isdigit() and int(keep) >= 1:
            st["backup_keep"] = str(int(keep))
        st["online_mode"] = "true" if self.online.currentIndex() == 0 \
            else "false"
        st["difficulty"] = self.diff.currentText()
        st["motd"] = self.motd.text().strip() or "1b1t Server"
        st["keep_inventory"] = "true" if self.keep.currentIndex() == 0 \
            else "false"
        core.save_settings(st)
        if self.parent_win:
            self.parent_win.load_backup_plan()
        QMessageBox.information(self, "设置", "已保存")
        self.accept()


class LogWindow(QDialog):
    """独立日志窗口 (玻璃样式, 跟随主窗口日志实时滚动)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("1b1t 服务器日志")
        self.resize(720, 480)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        self.logbox = QPlainTextEdit()
        self.logbox.setObjectName("LogBox")
        self.logbox.setReadOnly(True)
        self.logbox.setMaximumBlockCount(5000)
        lay.addWidget(self.logbox)


class NewServerDialog(QDialog):
    """开服向导: 版本/类型(mod加载器+版本)/目录/端口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建服务器")
        self.setFixedWidth(460)
        self.mod_thread = None
        lay = QVBoxLayout(self)
        lay.setSpacing(14)

        t = QLabel("新建服务器")
        t.setStyleSheet(f"font-size:20px;font-weight:700;color:{TEXT}")
        lay.addWidget(t)

        lay.addWidget(QLabel("Minecraft 版本"))
        self.ver = QComboBox()
        try:
            vers = core.load_manifest()
            releases = [v["id"] for v in vers
                        if v.get("type") == "release"]
            snapshots = [v["id"] for v in vers
                         if v.get("type") == "snapshot"]
            for v in releases[:25]:
                self.ver.addItem(f"正式版  {v}", v)
            for v in snapshots[:10]:
                self.ver.addItem(f"快照    {v}", v)
            if self.ver.count() == 0:
                for v in core.FALLBACK_VERSIONS:
                    self.ver.addItem(v, v)
        except Exception:
            for v in ("1.21.1", "1.20.4", "1.19.4", "1.18.2", "1.16.5"):
                self.ver.addItem(v, v)
        lay.addWidget(self.ver)

        lay.addWidget(QLabel("服务器类型 (mod 加载器)"))
        row = QHBoxLayout()
        self.type_grp = QButtonGroup(self)
        self.type_radio = {}
        for key, name in (("vanilla", "Vanilla"), ("fabric", "Fabric"),
                          ("neoforge", "NeoForge"), ("forge", "Forge")):
            rb = QRadioButton(name)
            if key == "vanilla":
                rb.setChecked(True)
            # 只在选中时刷新, 并直接传类型 (避免同组切换时序问题)
            rb.toggled.connect(
                lambda checked, k=key: checked and self.reload_mod_versions(k))
            self.type_grp.addButton(rb)
            self.type_radio[key] = rb
            row.addWidget(rb)
        lay.addLayout(row)

        # mod 加载器版本 (选 Fabric/NeoForge/Forge 时显示)
        self.mod_lab = QLabel("加载器版本")
        self.mod_ver = QComboBox()
        self.mod_ver.setEditable(False)  # 纯下拉选择, 不用输入
        self.mod_ver.setPlaceholderText("自动使用最新版")
        self.mod_lab.hide()
        self.mod_ver.hide()
        lay.addWidget(self.mod_lab)
        lay.addWidget(self.mod_ver)
        self.ver.currentIndexChanged.connect(self.reload_mod_versions)

        lay.addWidget(QLabel("服务器位置 (目录)"))
        drow = QHBoxLayout()
        self.ddir = QLineEdit()
        self.ddir.setPlaceholderText("~/1b1t-server")
        drow.addWidget(self.ddir, 1)
        browse = QPushButton("浏览…")
        browse.setMinimumWidth(72)
        browse.clicked.connect(self.pick_dir)
        drow.addWidget(browse)
        lay.addLayout(drow)

        lay.addWidget(QLabel("端口"))
        self.port = QLineEdit("25565")
        lay.addWidget(self.port)

        ok = QPushButton("开服")
        ok.setObjectName("Primary")
        ok.clicked.connect(self.accept)
        lay.addWidget(ok)

    def _stop_mod_thread(self):
        if self.mod_thread:
            if self.mod_thread.isRunning():
                self.mod_thread.terminate()
                self.mod_thread.wait(1000)
            self.mod_thread = None

    def closeEvent(self, e):
        """关闭时回收后台线程, 防止 QThread destroyed while running"""
        self._stop_mod_thread()
        super().closeEvent(e)

    def reload_mod_versions(self, stype=None):
        if stype is None:
            stype = next(k for k, rb in self.type_radio.items()
                         if rb.isChecked())
        if stype == "vanilla":
            self.mod_lab.hide()
            self.mod_ver.hide()
            return
        self.mod_lab.show()
        self.mod_ver.show()
        self._stop_mod_thread()
        self.mod_thread = ModVersThread(self.ver.currentData() or
                                       self.ver.currentText(), stype)
        self.mod_thread.done.connect(self.fill_mod_versions)
        self.mod_thread.start()

    def fill_mod_versions(self, stype, vers):
        if stype != next(k for k, rb in self.type_radio.items()
                         if rb.isChecked()):
            return
        cur = self.mod_ver.currentText()
        self.mod_ver.clear()
        if not vers:
            # 该 MC 版本没有此加载器 (如 NeoForge 不支持 1.20.1)
            self.mod_ver.addItem(f"(该版本无 {stype} 可用, 将自动用最新)",
                                 None)
            self.mod_ver.setCurrentIndex(0)
            return
        for v in vers[:15]:
            self.mod_ver.addItem(v, v)
        if cur:
            i = self.mod_ver.findText(cur)
            if i >= 0:
                self.mod_ver.setCurrentIndex(i)
        # editable combobox 清空后可能不自动选中第一项, 显式选中
        if self.mod_ver.count() and self.mod_ver.currentIndex() < 0:
            self.mod_ver.setCurrentIndex(0)

    def pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择服务器目录",
                                             os.path.expanduser("~"))
        if d:
            self.ddir.setText(d)

    def values(self):
        ver = self.ver.currentData()
        stype = next(k for k, rb in self.type_radio.items() if rb.isChecked())
        mod_version = None
        if stype != "vanilla" and self.mod_ver.count() > 0:
            mod_version = self.mod_ver.currentData() or \
                self.mod_ver.currentText().strip() or None
        server_dir = self.ddir.text().strip() or os.path.join(
            os.path.expanduser("~"),
            f"1b1t-server-{ver}")
        server_dir = os.path.abspath(os.path.expanduser(server_dir))
        port = self.port.text().strip() or "25565"
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("端口无效, 请输入 1-65535")
        # 端口占用检测: 被占自动换空闲端口
        import socket
        s = socket.socket()
        try:
            s.bind(("0.0.0.0", int(port)))
            s.close()
        except OSError:
            free = core.free_port()
            QMessageBox.information(
                self, "端口", f"端口 {port} 已被占用, 自动改用空闲端口 {free}")
            port = str(free)
        return ver, stype, server_dir, port, mod_version


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("1b1t 开服工具")
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 固定窗口尺寸: 防止详情页内容把窗口撑高(侧边栏底部按钮被挤出)
        self.setFixedSize(980, 640)
        self.drag_pos = None
        self.current = None  # 当前选中服务器目录
        self.log_offset = 0
        self.start_thread = None
        self.stop_thread = None
        self.bak_thread = None
        self.log_win = None  # 独立日志窗口

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        # 自定义背景图层 (全平台背景完全不透明; 液态玻璃质感只在按钮/卡片)
        self.is_linux = sys.platform.startswith("linux")
        self.bg_label = QLabel(root)
        self.bg_label.lower()
        glass = QFrame()
        glass.setObjectName("Glass")
        # 窗口阴影 (无边框窗口必需, 否则玻璃感出不来)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(glass)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 170))
        shadow.setOffset(0, 12)
        glass.setGraphicsEffect(shadow)
        outer.addWidget(glass)
        grid = QGridLayout(glass)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        # ---- 左栏: logo + 服务器列表 ----
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(238)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(18, 22, 18, 16)
        sv.setSpacing(12)
        # logo 行: 窗口控制按钮(红=关闭 黄=最小化) + 1b1t 标题
        logo_row = QHBoxLayout()
        logo_row.setSpacing(8)
        self.win_close = self._win_btn("✕", "#FF5F57", "#FF3B30")
        self.win_close.clicked.connect(self.close)
        self.win_min = self._win_btn("−", "#FEBC2E", "#FF9F0A")
        self.win_min.clicked.connect(self.showMinimized)
        self.win_close.setToolTip("关闭")
        self.win_min.setToolTip("最小化")
        for b in (self.win_close, self.win_min):
            logo_row.addWidget(b)
        logo = QLabel("1b1t")
        logo.setObjectName("Logo")
        logo_row.addWidget(logo)
        logo_row.addStretch(1)
        sv.addLayout(logo_row)
        tag = QLabel("Minecraft 一键开服")
        tag.setObjectName("Tagline")
        sv.addWidget(tag)
        # ---- 侧边栏: 主页入口 + 服务器列表直接放 + 设置固定在底部 ----
        self.nav_btns = {}
        home_btn = QPushButton("🏠 主页")
        home_btn.setObjectName("NavBtn")
        home_btn.setCheckable(True)
        home_btn.setChecked(True)
        home_btn.clicked.connect(lambda _c: self.nav_to("home"))
        sv.addWidget(home_btn)
        self.nav_btns["home"] = home_btn
        # 新建 + 服务器列表 (直接放在侧边栏)
        new_btn = QPushButton("＋ 新建服务器")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self.new_server)
        sv.addWidget(new_btn)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.on_select)
        sv.addWidget(self.list, 1)
        # 侧边栏底部: 设置 + 版本号
        set_btn = QPushButton("⚙ 设置")
        set_btn.setObjectName("NavBtn")
        set_btn.clicked.connect(self.open_settings)
        sv.addWidget(set_btn)
        ver_lab = QLabel(f"v{core.APP_VERSION}")
        ver_lab.setStyleSheet(f"color:{DIM};font-size:11px")
        sv.addWidget(ver_lab)
        grid.addWidget(side, 0, 0)

        # ---- 主页 ----
        self.home_page = QWidget()
        hv = QVBoxLayout(self.home_page)
        hv.setContentsMargins(26, 40, 26, 20)
        hv.setSpacing(14)
        home_title = QLabel("1b1t 开服工具")
        home_title.setStyleSheet(
            f"font-size:28px;font-weight:700;color:{TEXT};"
            "font-family:\"SF Pro Display\",\"PingFang SC\",sans-serif;")
        hv.addWidget(home_title)
        home_sub = QLabel("Minecraft 一键开服 · 图形 + 命令行")
        home_sub.setStyleSheet(f"color:{DIM};font-size:14px")
        hv.addWidget(home_sub)
        self.home_stats = QLabel("")
        self.home_stats.setStyleSheet(
            f"color:{DIM};font-size:13px;margin-top:4px")
        hv.addWidget(self.home_stats)
        hv.addSpacing(10)
        # 快捷入口卡片 (设置入口只在侧边栏导航)
        for text, icon, handler in (
                ("新建服务器", "＋", self.new_server),
                ("打开服务器目录", "📁", self.open_servers_dir),
                ("手动开服教程", "📖", self.open_docs)):
            card = QPushButton(f"{icon}  {text}")
            card.setFixedHeight(44)
            card.clicked.connect(handler)
            hv.addWidget(card)
        hv.addStretch(1)

        # ---- 右栏 ----
        main = QWidget()
        self.main_page = main
        mv = QVBoxLayout(main)
        mv.setContentsMargins(26, 24, 26, 20)
        mv.setSpacing(12)

        # 头部: 名字 + 副标题 + 状态灯 (红绿灯已移到侧边栏)
        head = QHBoxLayout()
        headv = QVBoxLayout()
        headv.setSpacing(2)
        self.name_lab = QLabel("选择或新建服务器")
        self.name_lab.setObjectName("ServerName")
        headv.addWidget(self.name_lab)
        self.sub_lab = QLabel("在左侧选择服务器开始管理")
        self.sub_lab.setObjectName("ServerSub")
        headv.addWidget(self.sub_lab)
        head.addLayout(headv, 1)
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color:{DIM};font-size:16px")
        head.addWidget(self.dot)
        self.state_lab = QLabel("未选择")
        self.state_lab.setStyleSheet(f"color:{DIM};font-size:13px")
        head.addWidget(self.state_lab)
        mv.addLayout(head)

        # 信息条
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chips = []
        self.chips_widget = QWidget()
        self.chips_layout = chips
        for _ in range(5):
            chip = QLabel("")
            chip.setObjectName("InfoChip")
            chips.addWidget(chip)
            self.chips.append(chip)
        chips.addStretch(1)
        self.chips_widget.setLayout(chips)
        self.chips_widget.hide()  # 未选择服务器时隐藏空药丸
        mv.addWidget(self.chips_widget)

        # 操作按钮
        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.start_btn = QPushButton("▶ 启动")
        self.start_btn.setObjectName("Primary")
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn = QPushButton("■ 停止")
        self.stop_btn.clicked.connect(self.on_stop)
        self.restart_btn = QPushButton("↻ 重启")
        self.restart_btn.clicked.connect(self.on_restart)
        self.del_btn = QPushButton("🗑 删除")
        self.del_btn.setObjectName("Danger")
        self.del_btn.clicked.connect(self.on_delete)
        for b in (self.start_btn, self.stop_btn, self.restart_btn,
                  self.del_btn):
            btns.addWidget(b)
        btns.addStretch(1)
        mv.addLayout(btns)

        # 设置卡片: 简单(快捷项) / 高级(server.properties 全部项)
        set_head = QHBoxLayout()
        set_title = QLabel("服务器设置")
        set_title.setObjectName("CardTitle")
        set_head.addWidget(set_title)
        set_head.addStretch(1)
        self.set_simple_btn = QPushButton("简单")
        self.set_adv_btn = QPushButton("高级")
        for b in (self.set_simple_btn, self.set_adv_btn):
            b.setCheckable(True)
            b.setObjectName("SegBtn")
            set_head.addWidget(b)
        self.set_simple_btn.setChecked(True)
        self.set_simple_btn.clicked.connect(lambda: self.switch_set_mode(0))
        self.set_adv_btn.clicked.connect(lambda: self.switch_set_mode(1))
        self.run_hint = QLabel("⚠ 运行中: 请先停止服务器再修改设置")
        self.run_hint.setStyleSheet(f"color:{YELLOW};font-size:12px")
        self.run_hint.hide()
        set_head.addWidget(self.run_hint)
        mv.addLayout(set_head)

        # 简单模式: 快捷配置表单
        self.set_stack = QStackedWidget()
        simple_w = QWidget()
        form = QGridLayout(simple_w)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.addWidget(QLabel("服务器名字"), 0, 0)
        self.ed_name = QLineEdit()
        self.ed_name.setPlaceholderText("游戏界面看到的名字")
        form.addWidget(self.ed_name, 0, 1)
        form.addWidget(QLabel("副标题"), 0, 2)
        self.ed_sub = QLineEdit()
        self.ed_sub.setPlaceholderText("名字下面的一行小字(可留空)")
        form.addWidget(self.ed_sub, 0, 3)
        form.addWidget(QLabel("端口"), 1, 0)
        self.ed_port = QLineEdit()
        form.addWidget(self.ed_port, 1, 1)
        form.addWidget(QLabel("最大人数"), 1, 2)
        self.ed_players = QLineEdit()
        form.addWidget(self.ed_players, 1, 3)
        form.addWidget(QLabel("内存上限"), 2, 0)
        self.cb_ram = QComboBox()
        self.cb_ram.addItems(["2G", "4G", "8G", "16G", "32G"])
        self.cb_ram.setEditable(True)
        form.addWidget(self.cb_ram, 2, 1)
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_settings)
        form.addWidget(self.save_btn, 2, 3)
        self.set_stack.addWidget(simple_w)

        # 高级模式: 编辑 server.properties 全部项 (key=value)
        adv_w = QWidget()
        av = QVBoxLayout(adv_w)
        av.setContentsMargins(0, 0, 0, 0)
        av.setSpacing(8)
        adv_tip = QLabel("编辑 server.properties 全部配置项"
                         " (key=value, # 开头的注释行会被忽略)")
        adv_tip.setStyleSheet(f"color:{DIM};font-size:12px")
        av.addWidget(adv_tip)
        self.ed_props = QPlainTextEdit()
        self.ed_props.setMinimumHeight(240)
        av.addWidget(self.ed_props)
        adv_save_row = QHBoxLayout()
        adv_save_row.addStretch(1)
        self.adv_save_btn = QPushButton("保存高级配置")
        self.adv_save_btn.clicked.connect(self.save_settings_advanced)
        adv_save_row.addWidget(self.adv_save_btn)
        av.addLayout(adv_save_row)
        self.set_stack.addWidget(adv_w)
        mv.addWidget(self.set_stack)

        # 存档备份
        self.backup_card = QWidget()
        bv = QVBoxLayout(self.backup_card)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(8)
        bak_title = QLabel("存档备份")
        bak_title.setObjectName("CardTitle")
        bv.addWidget(bak_title)
        bak_row = QHBoxLayout()
        bak_now = QPushButton("立即备份")
        bak_now.setObjectName("Primary")
        bak_now.clicked.connect(self.do_backup_now)
        self.bak_list = QListWidget()
        self.bak_list.setFixedHeight(80)
        self.bak_restore = QPushButton("恢复选中")
        self.bak_restore.clicked.connect(self.restore_backup)
        self.bak_del = QPushButton("删除")
        self.bak_del.setObjectName("Danger")
        self.bak_del.clicked.connect(self.del_backup)
        # 定时备份开关 + 间隔 (分钟)
        self.bak_auto = QComboBox()
        self.bak_auto.addItems(["定时备份: 关", "每 30 分钟", "每 1 小时",
                                "每 2 小时", "每 6 小时", "每 12 小时",
                                "每 24 小时"])
        self.bak_auto.currentIndexChanged.connect(self.save_backup_plan)
        bak_row.addWidget(bak_now)
        bak_row.addWidget(self.bak_restore)
        bak_row.addWidget(self.bak_del)
        bak_row.addWidget(self.bak_auto, 1)
        bv.addLayout(bak_row)
        bv.addWidget(self.bak_list)
        self.backup_card.hide()  # 选中服务器后才显示
        mv.addWidget(self.backup_card)

        # Mod 管理 (mod 服务器才有)
        self.mod_card = QWidget()
        mod_v = QVBoxLayout(self.mod_card)
        mod_v.setContentsMargins(0, 0, 0, 0)
        mod_v.setSpacing(8)
        mod_title = QLabel("Mod 管理 (mods 目录)")
        mod_title.setObjectName("CardTitle")
        mod_v.addWidget(mod_title)
        mod_row = QHBoxLayout()
        self.mod_list = QListWidget()
        self.mod_list.setFixedHeight(110)
        mod_v.addWidget(self.mod_list)
        add_mod = QPushButton("＋ 添加 mod")
        add_mod.clicked.connect(self.add_mod)
        del_mod = QPushButton("删除")
        del_mod.setObjectName("Danger")
        del_mod.clicked.connect(self.del_mod)
        open_dir = QPushButton("打开文件夹")
        open_dir.clicked.connect(self.open_mods_dir)
        mod_row.addWidget(add_mod)
        mod_row.addWidget(del_mod)
        mod_row.addWidget(open_dir)
        mod_row.addStretch(1)
        mod_v.addLayout(mod_row)
        self.mod_card.hide()
        mv.addWidget(self.mod_card)

        # 日志
        log_head = QHBoxLayout()
        log_title = QLabel("服务器日志")
        log_title.setObjectName("CardTitle")
        log_head.addWidget(log_title)
        log_head.addStretch(1)
        self.log_pop_btn = QPushButton("⧉ 弹出日志窗口")
        self.log_pop_btn.clicked.connect(self.pop_log_window)
        log_head.addWidget(self.log_pop_btn)
        mv.addLayout(log_head)
        self.logbox = QPlainTextEdit()
        self.logbox.setObjectName("LogBox")
        self.logbox.setReadOnly(True)
        self.logbox.setMaximumBlockCount(5000)  # 防内存无限增长
        self.logbox.setMinimumHeight(140)  # 滚动布局下日志区保持可用高度
        mv.addWidget(self.logbox, 1)
        # 控制台命令输入 (发到服务器控制台)
        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(8)
        self.cmd_in = QLineEdit()
        self.cmd_in.setPlaceholderText("输入服务器命令, 回车发送 (如 say 你好 / list / stop)")
        self.cmd_in.returnPressed.connect(self.send_cmd)
        cmd_row.addWidget(self.cmd_in, 1)
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.send_cmd)
        cmd_row.addWidget(send_btn)
        mv.addLayout(cmd_row)
        # 右侧用 QStackedWidget 切换主页/详情 (可靠, 无 z-order 问题)
        # 详情页包进滚动区: 固定窗口下设置表单不被挤压成 6px
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(main)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)  # index 0
        self.stack.addWidget(scroll)          # index 1
        self.main_page = scroll
        grid.addWidget(self.stack, 0, 1)

        # 日志轮询
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_log)
        self.timer.start(1000)

        self.refresh_list()
        self.load_backup_plan()
        self.apply_background()
        # 初始显示主页
        self.stack.setCurrentIndex(0)
        self.refresh_home_stats()

    def open_settings(self):
        """软件设置对话框 (版本号/背景/备份计划/默认配置)"""
        dlg = SettingsDialog(self)
        dlg.exec()

    def open_servers_dir(self):
        """文件管理器打开服务器所在目录"""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(
            os.path.expanduser("~")))

    def open_docs(self):
        """浏览器打开手动开服教程"""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl("https://www.1b1t.cn/docs/"))

    def refresh_home_stats(self):
        """主页统计: 服务器总数 / 运行中数量"""
        dirs = core.find_servers()
        running = 0
        for d in dirs:
            old = core.read_pid(d)
            if old and core.is_running(old["pid"]):
                running += 1
        self.home_stats.setText(
            f"共 {len(dirs)} 个服务器 · {running} 个运行中 · "
            f"v{core.APP_VERSION}")

    def toggle_max(self):
        """无边框窗口安全最大化: 记录原位置, 铺满屏幕工作区, 再点还原"""
        if getattr(self, "_maxed", False):
            self.setGeometry(self._normal_geo)
            self._maxed = False
        else:
            self._normal_geo = self.geometry()
            self._maxed = True
            self.setGeometry(QApplication.primaryScreen().availableGeometry())

    def _win_btn(self, glyph, idle, hover):
        """苹果交通灯样式窗口按钮"""
        b = QPushButton(glyph)
        b.setObjectName("WinBtn")
        b.setFixedSize(18, 18)
        b.setStyleSheet(
            f"QPushButton#WinBtn {{ background: {idle}; border: none;"
            f"border-radius: 9px; color: rgba(0,0,0,0); font-size: 10px;"
            f"font-weight: 700; padding: 0; }}"
            f"QPushButton#WinBtn:hover {{ background: {hover};"
            f"color: rgba(0,0,0,140); }}")
        return b

    # ---------- 拖动窗口 (仅空白区域) ----------
    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        w = self.childAt(e.position().toPoint())
        # 只在主玻璃/侧栏空白处拖动, 点击控件不拖
        if w is None or isinstance(w, (QFrame, QListWidget)) \
                or w.objectName() in ("Glass", "Sidebar", "Root"):
            self.drag_pos = e.globalPosition().toPoint() - self.pos()
        else:
            self.drag_pos = None

    def mouseMoveEvent(self, e):
        if self.drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    # ---------- 自定义背景 ----------
    def apply_background(self):
        """设置里保存的背景图片铺满窗口 (无则默认深色玻璃底)"""
        try:
            st = core.load_settings()
            bg = st.get("bg_image", "")
        except Exception:
            bg = ""
        if bg and os.path.isfile(bg):
            pm = QPixmap(bg)
            if not pm.isNull():
                w, h = self.width(), self.height()
                self.bg_label.setPixmap(pm.scaled(
                    max(1, w), max(1, h),
                    Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
                self.bg_label.setGeometry(0, 0, w, h)
                self.bg_label.show()
                # 背景图上方叠深色玻璃层(图透出, 按钮保持液态玻璃)
                self.centralWidget().setStyleSheet(
                    "#Root { background: transparent; }"
                    "#Glass { background: rgba(22,22,26,225);"
                    " border-radius: 20px;"
                    " border: 1px solid rgba(255,255,255,30);"
                    " border-top: 1px solid rgba(255,255,255,60); }")
                if hasattr(self, "bg_name"):
                    self.bg_name.setText(os.path.basename(bg))
                return
        self.bg_label.hide()
        self.centralWidget().setStyleSheet("")  # 恢复默认不透明深色
        if hasattr(self, "bg_name"):
            self.bg_name.setText("(无, 深色背景)")

    def pick_background(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "",
            "图片 (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not f:
            return
        st = core.load_settings()
        st["bg_image"] = f
        core.save_settings(st)
        self.apply_background()
        self.append_log(f"已设置自定义背景: {os.path.basename(f)}")

    def clear_background(self):
        st = core.load_settings()
        st.pop("bg_image", None)
        core.save_settings(st)
        self.apply_background()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "bg_label"):
            self.apply_background()

    # ---------- 服务器列表 ----------
    def refresh_list(self, select=None):
        self.list.blockSignals(True)
        self.list.clear()
        for d in core.find_servers():
            cfg = core.load_cfg(d)
            name = (cfg or {}).get("props", {}).get("motd", "").split("\n")[0] \
                or os.path.basename(d)
            item = QListWidgetItem(f"{name}\n{os.path.basename(d)}")
            item.setData(Qt.UserRole, d)
            self.list.addItem(item)
            if select == d:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        # 信号被屏蔽时 setCurrentItem 不触发 on_select,
        # 显式补一次 (否则新建后点侧边栏该服务器进不了详情页)
        if select:
            self.on_select(self.list.currentItem(), None)

    def nav_to(self, key):
        """侧边栏主页入口: 切回主页视图 (保留服务器选择)"""
        if key != "home":
            return
        self.list.blockSignals(True)
        self.list.clearSelection()
        # 必须同时清 currentItem: clearSelection 只清高亮不清内部
        # currentItem, 否则再点同一个服务器不触发 currentItemChanged
        # → 进不了详情页
        self.list.setCurrentItem(None)
        self.list.blockSignals(False)
        self.stack.setCurrentIndex(0)
        self.nav_btns["home"].setChecked(True)
        self.refresh_home_stats()
        self.update_state()

    def on_select(self, item, prev):
        if item is None:
            # 取消选择 → 回主页
            self.current = None
            self.stack.setCurrentIndex(0)
            self.nav_btns["home"].setChecked(True)
            self.refresh_home_stats()
            self.backup_card.hide()
            self.update_state()
            return
        d = item.data(Qt.UserRole)
        self.current = d
        self.stack.setCurrentIndex(1)
        self.nav_btns["home"].setChecked(False)
        self.log_offset = 0
        self.logbox.clear()
        cfg = core.load_cfg(d)
        if not cfg:
            return
        props = cfg.get("props", {})
        motd = props.get("motd", "").split("\n") if props.get("motd") else []
        name = motd[0] if motd else os.path.basename(d)
        sub = motd[1] if len(motd) > 1 else ""
        self.name_lab.setText(name)
        self.sub_lab.setText(sub or os.path.basename(d))
        chips = [f"<b>版本</b> {cfg.get('version', '-')}",
                 f"<b>类型</b> {cfg.get('server_type', 'vanilla')}",
                 f"<b>端口</b> {cfg.get('port', '-')}",
                 f"<b>内存</b> {cfg.get('ram', '-')}",
                 f"<b>人数</b> {props.get('max-players', '20')}"]
        for chip, txt in zip(self.chips, chips):
            chip.setText(txt)
        self.chips_widget.show()
        self.ed_name.setText(name)
        self.ed_sub.setText(sub)
        self.ed_port.setText(str(cfg.get("port") or
                                 props.get("server-port", "25565")))
        self.ed_players.setText(props.get("max-players", "20"))
        self.cb_ram.setEditText(cfg.get("ram", "2G"))
        self.refresh_mods()
        self.refresh_backups()
        self.load_backup_plan()
        self.update_state()

    def update_state(self):
        running = False
        if self.current:
            old = core.read_pid(self.current)
            running = bool(old and core.is_running(old["pid"]))
        self.dot.setText("●")
        if running:
            self.dot.setStyleSheet(f"color:{GREEN};font-size:16px")
            self.state_lab.setText("运行中")
            self.state_lab.setStyleSheet(
                f"color:{GREEN};font-size:13px")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)
            # 运行中禁止改配置: 提示 + 保存按钮禁用 (停服后可改)
            self.run_hint.show()
            self.save_btn.setEnabled(False)
            self.adv_save_btn.setEnabled(False)
        else:
            self.dot.setStyleSheet(f"color:{DIM};font-size:16px")
            self.state_lab.setText("已停止")
            self.state_lab.setStyleSheet(f"color:{DIM};font-size:13px")
            self.start_btn.setEnabled(self.current is not None)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
            self.run_hint.hide()
            self.save_btn.setEnabled(self.current is not None)
            self.adv_save_btn.setEnabled(self.current is not None)

    # ---------- 日志 ----------
    def append_log(self, text):
        """按关键词着色: 错误红/警告黄/普通白 (苹果风终端配色)
        同时写入独立日志窗口 (若已弹出)"""
        for line in text.splitlines():
            low = line.lower()
            if re.search(r"error|exception|fail|错误|失败", low):
                html = f'<span style="color:#FF6A61">{self._esc(line)}</span>'
            elif re.search(r"warn|警告", low):
                html = f'<span style="color:#FFD60A">{self._esc(line)}</span>'
            else:
                html = None
            if html:
                self.logbox.appendHtml(html)
                if self.log_win:
                    self.log_win.logbox.appendHtml(html)
            else:
                self.logbox.appendPlainText(line)
                if self.log_win:
                    self.log_win.logbox.appendPlainText(line)
        for box in (self.logbox,) + ((self.log_win.logbox,)
                                     if self.log_win else ()):
            sb = box.verticalScrollBar()
            sb.setValue(sb.maximum())

    def pop_log_window(self):
        """日志独立弹窗 (可以拖到副屏/单独看)"""
        if self.log_win is None:
            self.log_win = LogWindow(self)
        self.log_win.show()
        self.log_win.raise_()

    def send_cmd(self):
        """把输入的命令发到服务器控制台 (如 say/list/stop)"""
        if not self.current:
            return
        line = self.cmd_in.text().strip()
        if not line:
            return
        old = core.read_pid(self.current)
        if not old or not core.is_running(old["pid"]):
            QMessageBox.warning(self, "发送命令", "服务器未在运行")
            return
        if core.send_console(self.current, line):
            self.append_log(f"> {line}")
            self.cmd_in.clear()
        else:
            QMessageBox.warning(self, "发送命令", "命令发送失败")

    @staticmethod
    def _esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;"))

    def poll_log(self):
        # 定时备份检查 (last_backup 时间戳防重复)
        self.check_auto_backup()
        if not self.current:
            return
        path = os.path.join(core.runtime_dir(self.current), "console.log")
        try:
            with open(path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                if size < self.log_offset:
                    self.log_offset = 0
                    self.logbox.clear()
                if size == self.log_offset:
                    return
                f.seek(self.log_offset)
                data = f.read(size - self.log_offset)
                self.log_offset = size
            text = ANSI.sub("", data.decode("utf-8", errors="replace"))
            if text.strip():
                self.append_log(text)
        except OSError:
            pass

    # ---------- 新建 ----------
    def new_server(self):
        dlg = NewServerDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        try:
            ver, stype, server_dir, port, mod_version = dlg.values()
        except ValueError as e:
            QMessageBox.warning(self, "参数错误", str(e))
            return
        cfg = core.load_cfg(server_dir)
        if cfg:
            QMessageBox.information(self, "已存在",
                                    "该目录已有服务器, 直接启动即可")
            self.refresh_list(select=server_dir)
            return
        os.makedirs(server_dir, exist_ok=True)
        st = core.load_settings()
        props = {"server-port": port,
                 "online-mode": st["online_mode"],
                 "motd": f"{st['motd']}\n{st['motd']} 服务器",
                 "difficulty": st["difficulty"],
                 "max-players": "20"}
        cfg = {"dir": server_dir, "version": ver, "server_type": stype,
               "mod_version": mod_version, "port": int(port),
               "ram": core.default_ram(),
               "props": props, "gamerules": {}}
        if st["keep_inventory"] == "true":
            cfg["gamerules"]["keepInventory"] = "true"
        core.save_cfg(server_dir, cfg)
        self.refresh_list(select=server_dir)
        self.append_log(f"已创建服务器: MC {ver} ({stype}) 端口 {port}")
        self.on_start()

    # ---------- 启动/停止/重启/删除 ----------
    def on_start(self):
        if not self.current:
            return
        cfg = core.load_cfg(self.current)
        if not cfg:
            QMessageBox.warning(self, "启动失败",
                                "服务器配置不存在或损坏, 无法启动\n\n"
                                "可删除后重新创建该服务器")
            return
        self.append_log("========== 启动 ==========")
        self.start_btn.setEnabled(False)
        self.start_thread = StartThread(self.current, cfg)
        self.start_thread.log.connect(self.append_log)
        self.start_thread.done.connect(self.on_start_done)
        self.start_thread.start()

    def on_start_done(self, ok, detail):
        self.start_btn.setEnabled(True)
        self.update_state()
        if not ok:
            # 明确失败原因弹窗 (含日志尾部关键报错行)
            QMessageBox.warning(
                self, "启动失败",
                f"服务器启动失败\n\n{detail}\n\n"
                "完整日志见下方日志区 (可用 doctor 排查)")

    def on_stop(self):
        if not self.current:
            return
        self.append_log("========== 停止 ==========")
        self.stop_btn.setEnabled(False)
        self.stop_thread = StopThread(self.current)
        self.stop_thread.log.connect(self.append_log)
        self.stop_thread.done.connect(self.on_stop_done)
        self.stop_thread.start()

    def on_stop_done(self):
        self.update_state()

    def on_restart(self):
        if not self.current:
            return
        old = core.read_pid(self.current)
        if old and core.is_running(old["pid"]):
            self.stop_thread = StopThread(self.current)
            self.stop_thread.log.connect(self.append_log)
            self.stop_thread.done.connect(self.on_start)
            self.stop_thread.start()
        else:
            self.on_start()

    def on_delete(self):
        if not self.current:
            return
        old = core.read_pid(self.current)
        if old and core.is_running(old["pid"]):
            QMessageBox.warning(self, "服务器运行中",
                                "请先停止服务器再删除")
            return
        d = self.current
        if QMessageBox.question(
                self, "删除服务器",
                f"确定删除 {os.path.basename(d)} ? 存档会丢失, 不可恢复!") \
                != QMessageBox.Yes:
            return
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        self.append_log(f"已删除: {d}")
        self.current = None
        self.refresh_list()
        self.nav_to("home")  # 删除后返回主页

    # ---------- 存档备份 ----------
    BAK_PLAN = {0: 0, 1: 30, 2: 60, 3: 120, 4: 360, 5: 720, 6: 1440}

    def bak_dir(self):
        return os.path.join(self.current or "", "backups")

    def save_backup_plan(self, idx):
        """定时备份开关/间隔 → settings (GUI 开着时按间隔自动备份)"""
        st = core.load_settings()
        st["backup_interval_min"] = str(self.BAK_PLAN.get(idx, 0))
        core.save_settings(st)

    def load_backup_plan(self):
        st = core.load_settings()
        try:
            mins = int(st.get("backup_interval_min", "0") or 0)
        except (ValueError, TypeError):
            mins = 0
        # 找最近的档位 (找不到就用 0=关)
        idx = 0
        for i, m in self.BAK_PLAN.items():
            if m == mins:
                idx = i
        self.bak_auto.blockSignals(True)
        self.bak_auto.setCurrentIndex(idx)
        self.bak_auto.blockSignals(False)

    def refresh_backups(self):
        if not self.current:
            self.backup_card.hide()
            return
        self.backup_card.show()
        self.bak_list.clear()
        d = self.bak_dir()
        if not os.path.isdir(d):
            return
        for f in sorted(os.listdir(d), reverse=True):
            if not f.endswith(".tar.gz"):
                continue
            p = os.path.join(d, f)
            size = os.path.getsize(p) // 1024 // 1024
            item = QListWidgetItem(
                f"{f}   ({size} MB, {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p)))})")
            item.setData(Qt.UserRole, p)
            self.bak_list.addItem(item)

    def check_auto_backup(self):
        """定时备份检查 (每秒调用; last_backup 防重复,
        last_backup_attempt 防失败后每 1 秒疯狂重试)"""
        if not self.current:
            return
        st = core.load_settings()
        try:
            mins = int(st.get("backup_interval_min", "0") or 0)
        except (ValueError, TypeError):
            return
        if mins <= 0:
            return
        cfg = core.load_cfg(self.current)
        last = (cfg or {}).get("last_backup", 0)
        attempt = (cfg or {}).get("last_backup_attempt", 0)
        # 失败后至少 10 分钟再试 (备份是重活, 不能每秒重试)
        if time.time() - last >= mins * 60 and time.time() - attempt >= 600:
            cfg["last_backup_attempt"] = int(time.time())
            core.save_cfg(self.current, cfg)
            self.do_backup_now(auto=True)

    def do_backup_now(self, auto=False):
        if not self.current:
            return
        if not auto:
            self.append_log("========== 备份存档 ==========")
        if self.bak_thread and self.bak_thread.isRunning():
            return  # 备份进行中, 防重复
        self.bak_thread = BackupThread(self.current)
        self.bak_thread.auto = auto
        self.bak_thread.log.connect(self.append_log)
        self.bak_thread.done.connect(self.on_backup_done)
        self.bak_thread.start()

    def on_backup_done(self, ok):
        self.refresh_backups()
        if not ok:
            # 自动备份失败只记日志(不弹窗骚扰), 手动备份失败才弹窗
            if getattr(self.bak_thread, "auto", False):
                self.append_log("[备份] 自动备份失败, 10 分钟后自动重试")
                return
            QMessageBox.warning(self, "备份失败", "存档备份失败, 请看日志")

    def closeEvent(self, e):
        """关闭软件时回收全部后台线程 (防 QThread 崩溃/关不掉)"""
        for t in (self.bak_thread, self.start_thread, self.stop_thread):
            if t and t.isRunning():
                t.terminate()
                t.wait(2000)
        super().closeEvent(e)

    def restore_backup(self):
        item = self.bak_list.currentItem()
        if not item:
            QMessageBox.warning(self, "恢复备份", "请先选择要恢复的备份")
            return
        p = item.data(Qt.UserRole)
        if QMessageBox.question(
                self, "恢复备份",
                f"恢复 {os.path.basename(p)} ?\n当前存档会被覆盖, "
                "恢复前会自动备份当前存档") != QMessageBox.Yes:
            return
        # 先备份当前 (防误操作丢档)
        self.append_log("恢复前先备份当前存档...")
        core.backup_world(self.current, self.append_log)
        # 服务器需停止才能安全恢复
        old = core.read_pid(self.current)
        if old and core.is_running(old["pid"]):
            QMessageBox.warning(self, "恢复备份",
                                "服务器正在运行, 请先停止再恢复")
            self.refresh_backups()
            return
        try:
            import tarfile
            with tarfile.open(p, "r:gz") as tf:
                tf.extractall(self.current)
            self.append_log(f"已恢复备份: {os.path.basename(p)}")
            self.refresh_backups()
        except Exception as e:
            QMessageBox.warning(self, "恢复失败", str(e))

    def del_backup(self):
        item = self.bak_list.currentItem()
        if not item:
            QMessageBox.warning(self, "删除备份", "请先选择要删除的备份")
            return
        p = item.data(Qt.UserRole)
        if QMessageBox.question(self, "删除备份",
                                f"确定删除 {os.path.basename(p)} ?") \
                != QMessageBox.Yes:
            return
        try:
            os.remove(p)
            self.refresh_backups()
        except OSError as e:
            QMessageBox.warning(self, "删除失败", str(e))

    # ---------- Mod 管理 ----------
    def mods_dir(self):
        return os.path.join(self.current or "", "mods")

    def refresh_mods(self):
        stype = ""
        if self.current:
            cfg = core.load_cfg(self.current)
            stype = (cfg or {}).get("server_type", "vanilla")
        if stype not in ("fabric", "neoforge", "forge"):
            self.mod_card.hide()
            return
        self.mod_card.show()
        self.mod_list.clear()
        d = self.mods_dir()
        os.makedirs(d, exist_ok=True)
        for name in sorted(os.listdir(d)):
            if name.endswith(".jar"):
                self.mod_list.addItem(name)

    def add_mod(self):
        if not self.current:
            return
        d = self.mods_dir()
        os.makedirs(d, exist_ok=True)
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择 mod 文件 (jar)", "", "Mod 文件 (*.jar)")
        if not files:
            return
        import shutil
        for f in files:
            dest = os.path.join(d, os.path.basename(f))
            if os.path.abspath(f) == os.path.abspath(dest):
                continue
            shutil.copy(f, dest)
            self.append_log(f"已添加 mod: {os.path.basename(f)}")
        self.refresh_mods()
        QMessageBox.information(self, "Mod 管理",
                                f"已添加 {len(files)} 个 mod, 重启服务器后生效")

    def del_mod(self):
        item = self.mod_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Mod 管理", "请先选择要删除的 mod")
            return
        name = item.text()
        if QMessageBox.question(self, "删除 mod",
                                f"确定删除 {name} ?") != QMessageBox.Yes:
            return
        try:
            os.remove(os.path.join(self.mods_dir(), name))
            self.append_log(f"已删除 mod: {name}")
            self.refresh_mods()
        except OSError as e:
            QMessageBox.warning(self, "删除失败", str(e))

    def open_mods_dir(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        d = self.mods_dir()
        os.makedirs(d, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    # ---------- 保存设置 ----------
    def _is_running(self):
        """当前服务器是否在运行 (停服后才能改配置)"""
        if not self.current:
            return False
        old = core.read_pid(self.current)
        return bool(old and core.is_running(old["pid"]))

    def _need_stop_warn(self):
        """运行中修改配置 → 提示先停服, 返回 True 表示要拦截"""
        if self._is_running():
            QMessageBox.warning(
                self, "服务器运行中",
                "请先停止服务器再修改设置\n\n"
                "配置在服务器下次启动时生效")
            return True
        return False

    def switch_set_mode(self, idx):
        """设置卡片 简单/高级 切换; 切到高级时载入全部配置项"""
        self.set_simple_btn.setChecked(idx == 0)
        self.set_adv_btn.setChecked(idx == 1)
        self.set_stack.setCurrentIndex(idx)
        if idx == 1 and self.current:
            cfg = core.load_cfg(self.current) or {}
            self.ed_props.setPlainText(core.render_properties(
                cfg.get("props", {})))

    def save_settings_advanced(self):
        """高级模式保存: 解析 key=value 全部项写回 server.properties"""
        if not self.current:
            return
        if self._need_stop_warn():
            return
        props = {}
        for line in self.ed_props.toPlainText().splitlines():
            line = line.split("#")[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
        if not props:
            QMessageBox.warning(self, "参数错误",
                                "没有解析到任何配置项 (格式: key=value)")
            return
        cfg = core.load_cfg(self.current) or {}
        cfg["props"] = props
        if props.get("server-port", "").isdigit():
            cfg["port"] = int(props["server-port"])
        core.save_cfg(self.current, cfg)
        with open(os.path.join(self.current, "server.properties"),
                  "w") as f:
            f.write(core.render_properties(props))
        self.append_log("已保存高级配置 (重启后生效)")
        self.on_select(self.list.currentItem(), None)

    def save_settings(self):
        if not self.current:
            return
        if self._need_stop_warn():
            return
        cfg = core.load_cfg(self.current)
        if not cfg:
            return
        props = dict(cfg.get("props", {}))
        name = self.ed_name.text().strip() or "1b1t Server"
        sub = self.ed_sub.text().strip()
        props["motd"] = name + ("\n" + sub if sub else "")
        port = self.ed_port.text().strip()
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            QMessageBox.warning(self, "参数错误", "端口无效, 请输入 1-65535")
            return
        import socket
        s = socket.socket()
        try:
            s.bind(("0.0.0.0", int(port)))
            s.close()
        except OSError:
            free = core.free_port()
            QMessageBox.information(
                self, "端口", f"端口 {port} 已被占用, 自动改用空闲端口 {free}")
            port = str(free)
        players = self.ed_players.text().strip()
        if not players.isdigit() or not 1 <= int(players) <= 100000:
            QMessageBox.warning(self, "参数错误", "人数无效, 请输入正整数")
            return
        props["max-players"] = players
        props["server-port"] = port
        cfg["port"] = int(port)
        ram = self.cb_ram.currentText().strip().upper()
        if not re.match(r"^\d+[GM]?$", ram):
            QMessageBox.warning(self, "参数错误", "内存无效, 如 4G/512M")
            return
        if not re.search(r"[GM]", ram):
            ram += "G"
        cfg["ram"] = ram
        cfg["props"] = props
        core.save_cfg(self.current, cfg)
        with open(os.path.join(self.current, "server.properties"), "w") as f:
            f.write(core.render_properties(props))
        self.append_log("已保存服务器设置 (运行中重启后生效)")
        self.on_select(self.list.currentItem(), None)


def main():
    if len(sys.argv) > 3 and sys.argv[1] == "__sub":
        # 内部子进程入口 (服务器 keeper/收尾进程):
        # 冻结后 "二进制 -c 代码" 跑不起来, 统一走 __sub
        if sys.argv[2] == "keeper":
            core.run_keeper(sys.argv[3])
        elif sys.argv[2] == "cleanup":
            core.run_cleanup(sys.argv[3])
        return
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
