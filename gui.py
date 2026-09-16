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
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox,
                               QPlainTextEdit, QPushButton, QRadioButton,
                               QComboBox, QVBoxLayout, QWidget, QGridLayout,
                               QButtonGroup)

ANSI = re.compile(r"\x1b\[[0-9;]*m")

# ---------- 液态玻璃主题 (苹果风) ----------
ACCENT = "#0A84FF"      # iOS 蓝
GREEN = "#30D158"
RED = "#FF453A"
YELLOW = "#FFD60A"
TEXT = "#F5F5F7"
DIM = "#98989D"

QSS = f"""
* {{ font-family: "SF Pro Display", "SF Pro Text", "PingFang SC",
     "Segoe UI", "Microsoft YaHei", sans-serif; color: {TEXT}; }}
#Root {{ background: transparent; }}
#Glass {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(36,36,42,238), stop:0.5 rgba(28,28,32,238),
        stop:1 rgba(24,24,28,238));
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,28);
}}
#Sidebar {{ background: rgba(0,0,0,72); border-radius: 18px 0 0 18px;
            border-right: 1px solid rgba(255,255,255,16); }}
#Logo {{ font-size: 26px; font-weight: 700; letter-spacing: 1px; }}
#Tagline {{ color: {DIM}; font-size: 11px; }}
QPushButton {{
    background: rgba(255,255,255,22); border: 1px solid rgba(255,255,255,30);
    border-radius: 12px; padding: 9px 18px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{ background: rgba(255,255,255,38); }}
QPushButton:pressed {{ background: rgba(255,255,255,52); }}
QPushButton#Primary {{ background: {ACCENT}; border: none; color: white;
                       font-weight: 600; }}
QPushButton#Primary:hover {{ background: #2A93FF; }}
QPushButton#Danger {{ background: rgba(255,69,58,44); border: 1px solid
                     rgba(255,69,58,90); color: {RED}; }}
QPushButton#Danger:hover {{ background: rgba(255,69,58,70); }}
QPushButton#Ghost {{ background: transparent; border: none; color: {DIM}; }}
QLineEdit, QComboBox {{
    background: rgba(255,255,255,16); border: 1px solid rgba(255,255,255,28);
    border-radius: 10px; padding: 8px 12px; font-size: 13px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: #2C2C32; border: 1px solid rgba(255,255,255,30);
    border-radius: 10px; selection-background-color: {ACCENT};
}}
QListWidget {{ background: transparent; border: none; outline: 0; }}
QListWidget::item {{ border-radius: 12px; padding: 10px 12px; margin: 2px 4px; }}
QListWidget::item:hover {{ background: rgba(255,255,255,16); }}
QListWidget::item:selected {{ background: rgba(10,132,255,50);
                              border: 1px solid rgba(10,132,255,120); }}
#ServerName {{ font-size: 30px; font-weight: 700; }}
#ServerSub {{ color: {DIM}; font-size: 14px; }}
#InfoChip {{ background: rgba(255,255,255,16);
             border: 1px solid rgba(255,255,255,26); border-radius: 10px;
             padding: 8px 14px; font-size: 12px; color: #D8D8DD; }}
#InfoChip b {{ color: {TEXT}; font-weight: 600; }}
#CardTitle {{ font-size: 13px; font-weight: 600; color: #C8C8CE;
              letter-spacing: 0.5px; }}
#LogBox {{
    background: rgba(0,0,0,80); border: 1px solid rgba(255,255,255,22);
    border-radius: 14px; padding: 10px; font-family: "SF Mono", Consolas,
    monospace; font-size: 12px; color: #C8E6C8;
}}
#Dot {{ color: {GREEN}; font-size: 14px; }}
#DotStop {{ color: {DIM}; font-size: 14px; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: rgba(255,255,255,40);
    border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QMessageBox, QDialog {{ background: #242428; }}
QDialog QLabel {{ font-size: 13px; }}
QRadioButton {{ font-size: 13px; spacing: 6px; }}
QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 8px;
    border: 1px solid rgba(255,255,255,60); background: transparent; }}
QRadioButton::indicator:checked {{ background: {ACCENT}; border: none; }}
"""


def glass_effect(win):
    """Windows 11: DWM 圆角 + Mica 背景; 其他平台: 半透明"""
    if sys.platform != "win32":
        return
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
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(ctypes.c_int(DWMSBT_MAINWINDOW)), 4)
    except Exception:
        pass


class StartThread(QThread):
    log = Signal(str)
    done = Signal(bool)

    def __init__(self, server_dir, cfg):
        super().__init__()
        self.server_dir, self.cfg = server_dir, cfg

    def run(self):
        ok = core.api_start(self.server_dir, self.cfg, self.log.emit)
        self.done.emit(ok)


class StopThread(QThread):
    log = Signal(str)
    done = Signal()

    def __init__(self, server_dir):
        super().__init__()
        self.server_dir = server_dir

    def run(self):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            core.do_stop(self.server_dir)
        for line in buf.getvalue().splitlines():
            if line.strip():
                self.log.emit(line)
        self.done.emit()


class NewServerDialog(QDialog):
    """开服向导: 版本/类型/目录/端口 (简单模式零多余询问)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建服务器")
        self.setFixedWidth(460)
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

        lay.addWidget(QLabel("服务器类型"))
        row = QHBoxLayout()
        self.type_grp = QButtonGroup(self)
        self.type_radio = {}
        for key, name in (("vanilla", "Vanilla"), ("fabric", "Fabric"),
                          ("neoforge", "NeoForge"), ("forge", "Forge")):
            rb = QRadioButton(name)
            if key == "vanilla":
                rb.setChecked(True)
            self.type_grp.addButton(rb)
            self.type_radio[key] = rb
            row.addWidget(rb)
        lay.addLayout(row)

        lay.addWidget(QLabel("服务器位置 (目录)"))
        drow = QHBoxLayout()
        self.ddir = QLineEdit()
        self.ddir.setPlaceholderText("~/1b1t-server")
        drow.addWidget(self.ddir, 1)
        browse = QPushButton("浏览…")
        browse.setFixedWidth(72)
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

    def pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择服务器目录",
                                             os.path.expanduser("~"))
        if d:
            self.ddir.setText(d)

    def values(self):
        ver = self.ver.currentData()
        stype = next(k for k, rb in self.type_radio.items() if rb.isChecked())
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
        return ver, stype, server_dir, port


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("1b1t 开服工具")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(980, 640)
        self.drag_pos = None
        self.current = None  # 当前选中服务器目录
        self.log_offset = 0
        self.start_thread = None
        self.stop_thread = None

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        glass = QFrame()
        glass.setObjectName("Glass")
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
        logo = QLabel("1b1t")
        logo.setObjectName("Logo")
        sv.addWidget(logo)
        tag = QLabel("Minecraft 一键开服")
        tag.setObjectName("Tagline")
        sv.addWidget(tag)
        new_btn = QPushButton("＋ 新建服务器")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self.new_server)
        sv.addWidget(new_btn)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.on_select)
        sv.addWidget(self.list, 1)
        grid.addWidget(side, 0, 0)

        # ---- 右栏 ----
        main = QWidget()
        mv = QVBoxLayout(main)
        mv.setContentsMargins(26, 24, 26, 20)
        mv.setSpacing(12)

        # 头部: 名字 + 副标题 + 状态灯
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
        self.dot.setObjectName("DotStop")
        self.dot.setStyleSheet("font-size:16px")
        head.addWidget(self.dot)
        self.state_lab = QLabel("未选择")
        self.state_lab.setStyleSheet(f"color:{DIM};font-size:13px")
        head.addWidget(self.state_lab)
        mv.addLayout(head)

        # 信息条
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chips = []
        for _ in range(5):
            chip = QLabel("")
            chip.setObjectName("InfoChip")
            chips.addWidget(chip)
            self.chips.append(chip)
        chips.addStretch(1)
        mv.addLayout(chips)

        # 操作按钮
        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.start_btn = QPushButton("启动")
        self.start_btn.setObjectName("Primary")
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.on_stop)
        self.restart_btn = QPushButton("重启")
        self.restart_btn.clicked.connect(self.on_restart)
        self.del_btn = QPushButton("删除")
        self.del_btn.setObjectName("Danger")
        self.del_btn.clicked.connect(self.on_delete)
        for b in (self.start_btn, self.stop_btn, self.restart_btn,
                  self.del_btn):
            btns.addWidget(b)
        btns.addStretch(1)
        mv.addLayout(btns)

        # 设置卡片
        set_title = QLabel("服务器设置")
        set_title.setObjectName("CardTitle")
        mv.addWidget(set_title)
        form = QGridLayout()
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
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        form.addWidget(save_btn, 2, 3)
        mv.addLayout(form)

        # 日志
        log_title = QLabel("服务器日志")
        log_title.setObjectName("CardTitle")
        mv.addWidget(log_title)
        self.logbox = QPlainTextEdit()
        self.logbox.setObjectName("LogBox")
        self.logbox.setReadOnly(True)
        mv.addWidget(self.logbox, 1)
        grid.addWidget(main, 0, 1)

        # 日志轮询
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_log)
        self.timer.start(1000)

        self.refresh_list()
        glass_effect(self)

    # ---------- 拖动窗口 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if self.drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

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

    def on_select(self, item, prev):
        if item is None:
            return
        d = item.data(Qt.UserRole)
        self.current = d
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
        self.ed_name.setText(name)
        self.ed_sub.setText(sub)
        self.ed_port.setText(str(cfg.get("port") or
                                 props.get("server-port", "25565")))
        self.ed_players.setText(props.get("max-players", "20"))
        self.cb_ram.setEditText(cfg.get("ram", "2G"))
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
        else:
            self.dot.setStyleSheet(f"color:{DIM};font-size:16px")
            self.state_lab.setText("已停止")
            self.state_lab.setStyleSheet(f"color:{DIM};font-size:13px")
            self.start_btn.setEnabled(self.current is not None)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)

    # ---------- 日志 ----------
    def append_log(self, text):
        for line in text.splitlines():
            self.logbox.appendPlainText(line)
        sb = self.logbox.verticalScrollBar()
        sb.setValue(sb.maximum())

    def poll_log(self):
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
            ver, stype, server_dir, port = dlg.values()
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
               "port": int(port), "ram": core.default_ram(),
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
            return
        self.append_log("========== 启动 ==========")
        self.start_btn.setEnabled(False)
        self.start_thread = StartThread(self.current, cfg)
        self.start_thread.log.connect(self.append_log)
        self.start_thread.done.connect(self.on_start_done)
        self.start_thread.start()

    def on_start_done(self, ok):
        self.start_btn.setEnabled(True)
        self.update_state()
        if not ok:
            QMessageBox.warning(self, "启动失败",
                                "服务器启动失败, 请看日志排查")

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

    # ---------- 保存设置 ----------
    def save_settings(self):
        if not self.current:
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
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
