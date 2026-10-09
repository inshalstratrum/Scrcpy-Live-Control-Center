#!/usr/bin/env python3
"""
Scrcpy Live Control Center v4.1 (Universal Hero Edition)
Built according to GitHub Spec Kit (Spec-Driven Development) Standards.
- Constitution: .speckit/constitution.md
- Specification: .speckit/specs/001-scrcpy-live-control-center/spec.md
- Plan: .speckit/specs/001-scrcpy-live-control-center/plan.md

Features:
- The Hero: Live Mobile Screen Mirror (Hardware Accelerated Direct3D11)
- Zero-Orphan Process Supervisor (Aggressive cleanup of stale scrcpy sessions)
- Hardware UHID Emulation (Full mouse clicking, wheel scrolling & typing on Xiaomi/POCO)
- Physical Screen Power: Instant ⚡ Screen OFF (Battery Saver) & 💡 Screen ON
- Dual-Pipeline Wake & Unlock (Wakes from sleep & dismisses lock without permissions)
- Instant Single-Screen Mode Shifter (Full Control, Screen-Off Saver, View-Only, Webcam, AI Stream)
- Layout Management: In-App Embedded, Side-by-Side Docked, or Floating Pop-Out
- 1-Click Smart Wi-Fi Pairing (Unplug USB cable and stay wireless)
- Day ☀️ & Night 🌙 Eye-Care Themes with Dynamic UI Font Zooming (Ctrl + Mouse Wheel)
"""

import sys
import os

# Preserve script directory before changing working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import shutil

def find_binary(name):
    """Dynamically locate binaries in script dir, bin subdir, or system PATH."""
    local_path = os.path.join(SCRIPT_DIR, name)
    if os.path.isfile(local_path):
        return local_path
    bin_path = os.path.join(SCRIPT_DIR, "bin", name)
    if os.path.isfile(bin_path):
        return bin_path
    which_path = shutil.which(name)
    if which_path:
        return which_path
    return local_path

SCRCPY_EXE = find_binary("scrcpy.exe" if sys.platform == "win32" else "scrcpy")
ADB_EXE = find_binary("adb.exe" if sys.platform == "win32" else "adb")
RECORDINGS_DIR = os.path.join(SCRIPT_DIR, "recordings")
PRESETS_DIR = os.path.join(SCRIPT_DIR, "presets")

# Prevent Windows DLL search order collisions with scrcpy directory DLLs (libusb, avcodec, SDL, etc.)
# Crucial for pythonw.exe on Windows 11 so _ctypes and PyQt6 import cleanly
_safe_cwd = os.environ.get("TEMP", os.environ.get("USERPROFILE", "C:\\"))
try:
    os.chdir(_safe_cwd)
except Exception:
    pass

import re
import time
import subprocess
import atexit
import traceback
from datetime import datetime

import ctypes
from ctypes import wintypes

# Ensure UTF-8 output if console exists
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Diagnostic logging for headless / pythonw launches
LOG_FILE = os.path.join(SCRIPT_DIR, "control_center.log")

def log_debug(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def handle_exception(exc_type, exc_value, exc_traceback):
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_debug(f"UNHANDLED EXCEPTION:\n{err}")
    if sys.__excepthook__:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception
log_debug("Control Center initializing...")

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QCheckBox,
    QTabWidget, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
    QScrollArea, QFrame, QMenu, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QFont, QIcon, QDragEnterEvent, QDropEvent

# Windows Win32 API functions
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)

# Win32 Constants
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040

VK_MENU = 0x12       # Alt key
VK_SHIFT = 0x10      # Shift key
VK_O = 0x4F          # 'O' key
VK_P = 0x50          # 'P' key
VK_H = 0x48          # 'H' key
VK_B = 0x42          # 'B' key
VK_S = 0x53          # 'S' key
VK_N = 0x4E          # 'N' key
VK_UP = 0x26         # Up Arrow
VK_DOWN = 0x28       # Down Arrow
KEYEVENTF_KEYUP = 0x0002


# ----------------- Process Supervisor & ADB Layer -----------------

def kill_orphaned_scrcpy():
    """Aggressively terminates any orphaned scrcpy.exe processes to free ADB ports."""
    try:
        if os.name == 'nt':
            cmd = ["taskkill", "/F", "/IM", "scrcpy.exe"]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, capture_output=True, startupinfo=startupinfo)
    except Exception:
        pass

def run_adb(args, timeout=6):
    """Run adb command and return combined stdout + stderr string."""
    try:
        if not os.path.isfile(ADB_EXE) and not shutil.which(ADB_EXE):
            return "Error: adb executable not found. Please install Android Platform Tools or run setup_scrcpy.ps1."
        cmd = [ADB_EXE] + args
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=timeout)
        out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        return out.strip()
    except Exception as e:
        return f"Error: {e}"

def get_connected_devices():
    """Returns list of connected adb devices with details."""
    out = run_adb(["devices", "-l"])
    devices = []
    lines = out.splitlines()
    for line in lines[1:]:
        line = line.strip()
        if not line or "offline" in line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serial = parts[0]
            is_wifi = ":" in serial
            model = "Android Device"
            for p in parts[2:]:
                if p.startswith("model:"):
                    model = p.split(":", 1)[1]
            devices.append({
                "serial": serial,
                "model": model,
                "is_wifi": is_wifi,
                "line": line
            })
    return devices

def get_device_hardware_info(serial=None):
    """Queries battery percentage, charging state, resolution, and Android version."""
    battery_level = "--"
    is_charging = False
    screen_res = "Unknown"
    android_ver = "Android"
    prefix = ["-s", serial] if serial else []

    try:
        b_out = run_adb(prefix + ["shell", "dumpsys", "battery"])
        m_level = re.search(r"level:\s*(\d+)", b_out)
        if m_level:
            battery_level = f"{m_level.group(1)}%"
        if "USB powered: true" in b_out or "AC powered: true" in b_out:
            is_charging = True
    except Exception:
        pass

    try:
        s_out = run_adb(prefix + ["shell", "wm", "size"])
        m_size = re.search(r"Physical size:\s*(\d+x\d+)", s_out)
        if m_size:
            screen_res = m_size.group(1)
    except Exception:
        pass

    try:
        v_out = run_adb(prefix + ["shell", "getprop", "ro.build.version.release"])
        if v_out:
            android_ver = f"Android {v_out.strip()}"
    except Exception:
        pass

    return {
        "battery": battery_level,
        "charging": is_charging,
        "resolution": screen_res,
        "android": android_ver
    }

def get_device_wlan_ip(serial=None):
    """Detects Wi-Fi IP address of the device."""
    prefix = ["-s", serial] if serial else []
    out = run_adb(prefix + ["shell", "ip -f inet addr show wlan0"])
    m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out)
    if m:
        return m.group(1)
    out_route = run_adb(prefix + ["shell", "ip route"])
    m2 = re.search(r"src\s+(\d+\.\d+\.\d+\.\d+)", out_route)
    if m2:
        return m2.group(1)
    return ""


# ----------------- Eye-Care Lighting Themes -----------------

THEMES = {
    "night": {
        "name": "🌙 Night Mode (Eye-Care Warm Midnight)",
        "bg_main": "#080d1a",
        "bg_card": "#101827",
        "bg_card_inner": "#162238",
        "bg_hover": "#1d2e4d",
        "text_main": "#f8fafc",
        "text_muted": "#94a3b8",
        "border": "#22324f",
        "accent": "#38bdf8",
        "accent_glow": "#0284c7",
        "sun_moon_btn": "☀️ Switch to Day Mode"
    },
    "day": {
        "name": "☀️ Day Mode (Soft Natural Sunlight)",
        "bg_main": "#f1f5f9",
        "bg_card": "#ffffff",
        "bg_card_inner": "#e2e8f0",
        "bg_hover": "#cbd5e1",
        "text_main": "#0f172a",
        "text_muted": "#475569",
        "border": "#cbd5e1",
        "accent": "#0284c7",
        "accent_glow": "#0369a1",
        "sun_moon_btn": "🌙 Switch to Night Mode"
    }
}

def generate_theme_stylesheet(theme_key="night", font_size=14):
    t = THEMES[theme_key]
    return f"""
    QMainWindow {{
        background-color: {t['bg_main']};
    }}
    QWidget {{
        color: {t['text_main']};
        font-family: 'Segoe UI', -apple-system, Roboto, sans-serif;
        font-size: {font_size}px;
    }}
    QTabWidget::pane {{
        border: 1px solid {t['border']};
        background: {t['bg_main']};
        border-radius: 10px;
    }}
    QTabBar::tab {{
        background: {t['bg_card']};
        color: {t['text_muted']};
        padding: 9px 15px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 700;
        font-size: {font_size}px;
        border: 1px solid {t['border']};
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background: {t['accent']};
        color: #ffffff;
        border-color: {t['accent']};
    }}
    QTabBar::tab:hover:!selected {{
        background: {t['bg_hover']};
        color: {t['text_main']};
    }}
    QGroupBox {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 10px;
        margin-top: 16px;
        padding-top: 14px;
        font-weight: 700;
        color: {t['accent']};
        font-size: {font_size}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
    }}
    QPushButton {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        color: {t['text_main']};
        padding: 8px 14px;
        font-weight: 700;
        font-size: {font_size}px;
    }}
    QPushButton:hover {{
        background-color: {t['bg_hover']};
        border-color: {t['accent']};
    }}
    QPushButton:pressed {{
        background-color: {t['accent']};
        color: #ffffff;
    }}
    QComboBox, QSpinBox {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 6px 10px;
        color: {t['text_main']};
        font-size: {font_size}px;
    }}
    QComboBox:hover, QSpinBox:hover {{
        border-color: {t['accent']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        color: {t['text_main']};
        selection-background-color: {t['accent']};
        selection-color: #ffffff;
    }}
    QCheckBox {{
        spacing: 8px;
        color: {t['text_main']};
        font-size: {font_size}px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {t['border']};
        background: {t['bg_card']};
    }}
    QCheckBox::indicator:checked {{
        background: {t['accent']};
        border-color: {t['accent']};
    }}
    QTextEdit {{
        background-color: {t['bg_main']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        color: {t['text_main']};
        font-family: 'Consolas', monospace;
        font-size: {font_size - 1}px;
    }}
    """


# ----------------- Mode Shifter Button -----------------

class ModeShiftButton(QPushButton):
    """Distinctive, high-contrast action button for instant mode shifting."""
    def __init__(self, title, icon, accent_color, tag="", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setText(f"{icon}  {title}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #111a2c;
                border: 2px solid #22324f;
                border-radius: 10px;
                color: #f1f5f9;
                font-weight: 700;
                padding: 12px 14px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {accent_color};
                background-color: #17243c;
            }}
        """)


# ----------------- Main Unified Live Control Center -----------------

class ScrcpyUnifiedControlCenter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrcpy Live Control Center v4.1 (Universal Hero Edition)")
        self.resize(1300, 860)
        self.setMinimumSize(1020, 700)
        self.setAcceptDrops(True)

        self.current_theme = "night"
        self.base_font_size = 14
        self.selected_serial = ""
        self.current_mode = "full"
        self.is_screen_physically_off = False
        self.device_aspect_ratio = 0.45

        # Process management
        self.scrcpy_proc = None
        self.scrcpy_hwnd = None
        self.scrcpy_title = "Scrcpy_Live_Hero_Window"
        self.layout_mode = "embedded"  # 'embedded', 'docked', or 'floating'
        
        self.active_streamer_proc = None
        self.is_streaming_pc = False

        # Register exit hook to guarantee zero orphaned processes
        atexit.register(self.cleanup_all_processes)

        self.apply_theme()
        self.setup_ui()
        self.refresh_devices()

        # Timers
        self.embed_timer = QTimer(self)
        self.embed_timer.timeout.connect(self._poll_and_manage_window)

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.refresh_devices)
        self.poll_timer.start(3500)

        # Initial device discovery and start
        QTimer.singleShot(300, self.initial_startup)

    def apply_theme(self):
        stylesheet = generate_theme_stylesheet(self.current_theme, self.base_font_size)
        self.setStyleSheet(stylesheet)

    def toggle_day_night(self):
        self.current_theme = "day" if self.current_theme == "night" else "night"
        self.apply_theme()
        t = THEMES[self.current_theme]
        self.btn_day_night.setText(t["sun_moon_btn"])
        self.lbl_status.setText(f"Switched to {t['name']}")

    # ----------------- UI Construction -----------------

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(4)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: #1e293b;
            }
            QSplitter::handle:hover {
                background: #38bdf8;
            }
        """)

        # LEFT SIDE: Full-height, edge-to-edge phone frame
        # "The screen of the phone must be on the left side, the complete left side, from top to bottom.
        #  No border, no option on top and bottom or left. The complete screen of the live mobile screen
        #  must be on the full left side of this app, and all control on the right."
        left_screen = self.create_hero_screen_area()
        self.splitter.addWidget(left_screen)

        # RIGHT SIDE: All controls in a modern scrollable dashboard
        right_dashboard = self.create_right_dashboard()
        self.splitter.addWidget(right_dashboard)

        # Splitter sizing
        init_h = max(700, self.height())
        phone_w = max(340, int(init_h * self.device_aspect_ratio))
        right_w = max(600, self.width() - phone_w)
        self.splitter.setSizes([phone_w, right_w])
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.splitterMoved.connect(lambda pos, idx: self.resize_embedded_window())

        main_layout.addWidget(self.splitter)

    def create_right_dashboard(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0b0f19;
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 4px;
            }
        """)

        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setSpacing(10)
        v_layout.setContentsMargins(12, 10, 12, 10)

        # 1. Top Cockpit Header Card (Title, Badges, Device Selector, Wi-Fi, Day/Night, Zoom)
        header = self.create_top_cockpit()
        v_layout.addWidget(header)

        # 2. Hero Screen & Power Dock Card (Screen OFF, Screen ON, Wake, Re-sync, Nav buttons)
        screen_dock = self.create_phone_screen_dock()
        v_layout.addWidget(screen_dock)

        # 3. Control Rail Tabs (Mode Shift, Stream Quality, Connectivity, Guide)
        rail = self.create_control_rail()
        v_layout.addWidget(rail, stretch=1)

        # 4. Command Preview & Status Footer
        footer = self.create_footer()
        v_layout.addWidget(footer)

        scroll.setWidget(container)
        return scroll

    def create_top_cockpit(self):
        card = QFrame()
        card.setStyleSheet("background-color: #101827; border: 1px solid #22324f; border-radius: 10px; padding: 6px;")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)

        # Row 1: App Title, Badges, Day/Night, Snapping, Zoom
        r1 = QHBoxLayout()
        title_box = QHBoxLayout()
        icon_main = QLabel("📱")
        icon_main.setFont(QFont("Segoe UI Emoji", 22))
        title_box.addWidget(icon_main)

        title_txt = QVBoxLayout()
        title_lbl = QLabel("SCRCPY LIVE CONTROL CENTER v4.1")
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #38bdf8; letter-spacing: 0.5px;")
        title_txt.addWidget(title_lbl)

        sub_lbl = QLabel("Hero Live Mirror • Hardware UHID Input Active • Zero-Orphan Supervisor • Spec Kit Built")
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        title_txt.addWidget(sub_lbl)
        title_box.addLayout(title_txt)
        r1.addLayout(title_box)

        r1.addStretch()

        # Day / Night Toggle Button
        self.btn_day_night = QPushButton("☀️ Switch to Day Mode")
        self.btn_day_night.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: #0b0f19;
                font-weight: 800;
                border: 1px solid #fbbf24;
                border-radius: 8px;
                padding: 6px 14px;
            }
            QPushButton:hover { background: #d97706; color: white; }
        """)
        self.btn_day_night.clicked.connect(self.toggle_day_night)
        r1.addWidget(self.btn_day_night)

        # Monitor Snapping Menu
        btn_snap_menu = QPushButton("📐 Snap Layout ▼")
        btn_snap_menu.setStyleSheet("background: #1e293b; color: #f8fafc; font-weight: 700; border-radius: 8px; padding: 6px 12px;")
        snap_menu = QMenu(self)
        snap_menu.addAction("◧ Snap Left (50% Monitor)", lambda: self.snap_window("left"))
        snap_menu.addAction("◨ Snap Right (50% Monitor)", lambda: self.snap_window("right"))
        snap_menu.addAction("🗔 Compact Side-Dock (460px width)", lambda: self.snap_window("dock"))
        snap_menu.addAction("🗖 Center Floating (75% Monitor)", lambda: self.snap_window("center"))
        snap_menu.addAction("⛶ Maximize / Restore", lambda: self.snap_window("max"))
        btn_snap_menu.setMenu(snap_menu)
        r1.addWidget(btn_snap_menu)

        # UI Font Zoom Controls
        btn_zoom_out = QPushButton("A-")
        btn_zoom_out.setToolTip("Decrease UI Font Size (Ctrl + Wheel Down)")
        btn_zoom_out.setFixedWidth(34)
        btn_zoom_out.clicked.connect(lambda: self.change_font_size(-1))
        r1.addWidget(btn_zoom_out)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold;")
        r1.addWidget(self.lbl_zoom)

        btn_zoom_in = QPushButton("A+")
        btn_zoom_in.setToolTip("Increase UI Font Size (Ctrl + Wheel Up)")
        btn_zoom_in.setFixedWidth(34)
        btn_zoom_in.clicked.connect(lambda: self.change_font_size(1))
        r1.addWidget(btn_zoom_in)

        layout.addLayout(r1)

        # Row 2: Live Device Telemetry, Device Combo Selector & Wi-Fi Connect
        r2 = QHBoxLayout()
        self.led_status = QLabel("🟢 CHECKING DEVICE")
        self.led_status.setStyleSheet("""
            background: #064e3b;
            color: #34d399;
            border: 1px solid #059669;
            border-radius: 6px;
            padding: 4px 10px;
            font-weight: 800;
            font-size: 12px;
        """)
        r2.addWidget(self.led_status)

        self.lbl_dev_specs = QLabel("📱 Checking...")
        self.lbl_dev_specs.setStyleSheet("background: #1e293b; color: #f1f5f9; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 12px;")
        r2.addWidget(self.lbl_dev_specs)

        self.lbl_battery = QLabel("🔋 Battery: --")
        self.lbl_battery.setStyleSheet("background: #1e293b; color: #f1f5f9; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 12px;")
        r2.addWidget(self.lbl_battery)

        self.lbl_wifi_ip = QLabel("📶 Wi-Fi: --")
        self.lbl_wifi_ip.setStyleSheet("background: #1e293b; color: #f1f5f9; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 12px;")
        r2.addWidget(self.lbl_wifi_ip)

        r2.addStretch()

        # Device Combo Selector
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(220)
        self.device_combo.currentIndexChanged.connect(self.on_device_selection_changed)
        r2.addWidget(self.device_combo)

        # 1-Click Wi-Fi Connect Button
        self.btn_wifi_connect = QPushButton("📶 Connect Wi-Fi")
        self.btn_wifi_connect.setToolTip("Enable Wireless TCP/IP mode and connect over Wi-Fi")
        self.btn_wifi_connect.setStyleSheet("background: #0d9488; color: white; font-weight: bold; border-radius: 6px; padding: 4px 12px;")
        self.btn_wifi_connect.clicked.connect(self.connect_wireless_smart)
        r2.addWidget(self.btn_wifi_connect)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Refresh Device Metrics & Screen")
        btn_refresh.clicked.connect(self.refresh_devices)
        r2.addWidget(btn_refresh)

        layout.addLayout(r2)
        return card

    # ----------------- Hero Screen Area (Complete Left Side) -----------------

    def create_hero_screen_area(self):
        """Creates the full-height, edge-to-edge phone frame on the complete left side.
        Zero borders, zero options on top/bottom/left, spanning from top pin point to bottom pin point."""
        self.phone_frame = QFrame()
        self.phone_frame.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.phone_frame.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: none;
                border-radius: 0px;
                margin: 0px;
                padding: 0px;
            }
        """)
        self.phone_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.phone_frame.setMinimumWidth(260)

        frame_layout = QVBoxLayout(self.phone_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Standby / Connecting placeholder shown only when no live mirror is attached
        self.placeholder_widget = QWidget()
        self.placeholder_widget.setStyleSheet("background-color: #030712; margin: 0; padding: 0;")
        ph_layout = QVBoxLayout(self.placeholder_widget)
        ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.setSpacing(14)
        ph_layout.setContentsMargins(12, 12, 12, 12)

        self.ph_icon = QLabel("📱")
        self.ph_icon.setFont(QFont("Segoe UI Emoji", 56))
        self.ph_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.addWidget(self.ph_icon)

        self.ph_text = QLabel("Live Mobile Screen\n(Direct3D11 Hardware Native)")
        self.ph_text.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.ph_text.setStyleSheet("color: #94a3b8;")
        self.ph_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.addWidget(self.ph_text)

        self.btn_start_mirror = QPushButton("▶ Launch Live Mirror")
        self.btn_start_mirror.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 800;
                font-size: 14px;
                padding: 10px 24px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_start_mirror.clicked.connect(self.start_live_mirror)
        ph_layout.addWidget(self.btn_start_mirror, alignment=Qt.AlignmentFlag.AlignCenter)

        frame_layout.addWidget(self.placeholder_widget)
        return self.phone_frame

    def create_phone_screen_dock(self):
        """Card on the right panel holding screen power toggles, mirror status, and navigation."""
        card = QFrame()
        card.setStyleSheet("background-color: #101827; border: 1px solid #22324f; border-radius: 10px; padding: 6px;")
        v = QVBoxLayout(card)
        v.setSpacing(8)
        v.setContentsMargins(10, 8, 10, 8)

        # Row 1: Badges & Layout Controls
        r1 = QHBoxLayout()
        self.lbl_hero_badge = QLabel("🎮 LIVE MOBILE MIRROR")
        self.lbl_hero_badge.setStyleSheet("color: #38bdf8; font-weight: 800; font-size: 12px;")
        r1.addWidget(self.lbl_hero_badge)

        self.lbl_screen_power = QLabel("💡 Phone Display: ON")
        self.lbl_screen_power.setStyleSheet("""
            background: #1e293b;
            color: #38bdf8;
            border: 1px solid #38bdf855;
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 700;
        """)
        r1.addWidget(self.lbl_screen_power)

        r1.addStretch()

        btn_resync = QPushButton("🔄 Re-sync")
        btn_resync.setToolTip("Re-syncs or restarts the live mirror session")
        btn_resync.setStyleSheet("background: #1e293b; color: #cbd5e1; font-size: 11px; padding: 3px 8px;")
        btn_resync.clicked.connect(self.restart_live_mirror)
        r1.addWidget(btn_resync)

        self.combo_layout = QComboBox()
        self.combo_layout.addItems(["🗔 In-App Full-Height Left", "🗖 Docked Side-by-Side", "🗗 Floating Pop-Out"])
        self.combo_layout.setToolTip("Choose window layout: Full left in app, docked beside app, or floating window")
        self.combo_layout.setStyleSheet("background: #334155; color: white; font-weight: 700; font-size: 11px; padding: 2px 6px;")
        self.combo_layout.currentIndexChanged.connect(self.on_layout_mode_changed)
        r1.addWidget(self.combo_layout)

        v.addLayout(r1)

        # Row 2: Physical Screen Power Toggles & Wake
        r2 = QHBoxLayout()
        self.btn_toggle_screen_off = QPushButton("⚡ Screen OFF (Saver)")
        self.btn_toggle_screen_off.setToolTip("Turn physical phone screen OFF while mirror stays live and mouse/keys stay active! Saves battery & prevents heat.")
        self.btn_toggle_screen_off.setStyleSheet("""
            QPushButton {
                background-color: #065f46;
                color: #34d399;
                border: 1px solid #059669;
                font-weight: 800;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #047857; color: white; }
        """)
        self.btn_toggle_screen_off.clicked.connect(self.turn_physical_screen_off)
        r2.addWidget(self.btn_toggle_screen_off)

        btn_screen_on = QPushButton("💡 Screen ON")
        btn_screen_on.setToolTip("Turn physical phone screen display back ON")
        btn_screen_on.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #475569;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #334155; color: white; }
        """)
        btn_screen_on.clicked.connect(self.turn_physical_screen_on)
        r2.addWidget(btn_screen_on)

        btn_wake = QPushButton("🔓 Wake & Unlock")
        btn_wake.setToolTip("Wakes phone from sleep, turns display on and dismisses lockscreen")
        btn_wake.setStyleSheet("""
            QPushButton {
                background-color: #6d28d9;
                color: white;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #5b21b6; }
        """)
        btn_wake.clicked.connect(self.wake_and_unlock_action)
        r2.addWidget(btn_wake)

        v.addLayout(r2)

        # Row 3: Android Navigation Buttons
        r3 = QHBoxLayout()
        btn_back = QPushButton("🔙 Back")
        btn_back.setToolTip("Send Back key (Right-click in mirror also sends Back)")
        btn_back.clicked.connect(lambda: self.send_phone_nav_key("back"))
        r3.addWidget(btn_back)

        btn_home = QPushButton("🏠 Home")
        btn_home.setToolTip("Send Home key (Middle-click in mirror also sends Home)")
        btn_home.clicked.connect(lambda: self.send_phone_nav_key("home"))
        r3.addWidget(btn_home)

        btn_recents = QPushButton("🔲 Recents")
        btn_recents.setToolTip("Open App Switcher / Recent Apps")
        btn_recents.clicked.connect(lambda: self.send_phone_nav_key("recents"))
        r3.addWidget(btn_recents)

        btn_notif = QPushButton("🔔 Notifs")
        btn_notif.setToolTip("Pull down notification shade")
        btn_notif.clicked.connect(lambda: self.send_phone_nav_key("notif"))
        r3.addWidget(btn_notif)

        btn_voldown = QPushButton("🔉")
        btn_voldown.setToolTip("Volume Down")
        btn_voldown.setFixedWidth(32)
        btn_voldown.clicked.connect(lambda: self.send_phone_nav_key("voldown"))
        r3.addWidget(btn_voldown)

        btn_volup = QPushButton("🔊")
        btn_volup.setToolTip("Volume Up")
        btn_volup.setFixedWidth(32)
        btn_volup.clicked.connect(lambda: self.send_phone_nav_key("volup"))
        r3.addWidget(btn_volup)

        btn_shot = QPushButton("📸 Snap HD")
        btn_shot.setToolTip("Take high-definition screenshot and save to recordings folder")
        btn_shot.setStyleSheet("background-color: #0369a1; color: white; font-weight: bold; border-radius: 6px; padding: 5px 10px;")
        btn_shot.clicked.connect(self.capture_phone_screenshot)
        r3.addWidget(btn_shot)

        v.addLayout(r3)
        return card

    # ----------------- Control Rail (Right Side) -----------------

    def create_control_rail(self):
        rail = QWidget()
        layout = QVBoxLayout(rail)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        tabs = QTabWidget()
        tabs.addTab(self.create_modes_tab(), "🎮 Shift Mode")
        tabs.addTab(self.create_settings_tab(), "⚙️ Stream Quality")
        tabs.addTab(self.create_connectivity_tab(), "📶 Connectivity")
        tabs.addTab(self.create_guide_tab(), "📖 Xiaomi & Keys")
        layout.addWidget(tabs)

        return rail

    def create_modes_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        v = QVBoxLayout(container)
        v.setSpacing(10)
        v.setContentsMargins(6, 8, 6, 8)

        lbl_desc = QLabel("💡 <b>One-Click Mode Shifting:</b> Switch operational modes on the fly on your live screen without opening separate windows!")
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lbl_desc.setWordWrap(True)
        v.addWidget(lbl_desc)

        # 1. Full Control
        m1 = ModeShiftButton("Full Control (Hardware UHID)", "🎮", "#0284c7")
        m1.setToolTip("Full screen mirroring with mouse & keyboard. Hardware UHID active - works on Xiaomi & Poco phones!")
        m1.clicked.connect(lambda: self.shift_to_mode("full"))
        v.addWidget(m1)

        # 2. Screen-Off Saver
        m2 = ModeShiftButton("Screen-Off Battery Saver", "🔋", "#10b981")
        m2.setToolTip("Turns physical phone display completely OFF to save battery & stop heating, while PC mirror stays live and fully interactive!")
        m2.clicked.connect(lambda: self.shift_to_mode("screen_off"))
        v.addWidget(m2)

        # 3. View-Only Monitor
        m3 = ModeShiftButton("View-Only Monitor", "👁️", "#64748b")
        m3.setToolTip("High-definition mirror with mouse and keyboard inputs disabled. Ideal for presentations or monitoring.")
        m3.clicked.connect(lambda: self.shift_to_mode("view_only"))
        v.addWidget(m3)

        # 4. Mobile Webcam 30 FPS
        m4 = ModeShiftButton("Mobile Webcam (Smooth 30 FPS)", "📷", "#ec4899")
        m4.setToolTip("Streams phone camera at smooth 30 FPS with true-to-life colors. Toggle Front/Rear sensor in Stream Quality tab.")
        m4.clicked.connect(lambda: self.shift_to_mode("camera"))
        v.addWidget(m4)

        # 5. PC Screen to Phone (for Google Assistant)
        self.btn_mode_pc_share = ModeShiftButton("PC Screen to Phone (Assistant AI)", "🤖", "#6366f1")
        self.btn_mode_pc_share.setToolTip("Streams PC desktop to phone with zoom & high-contrast sharpening. Mobile Google Assistant reads text and converses voice-to-voice!")
        self.btn_mode_pc_share.clicked.connect(self.toggle_pc_to_phone_stream)
        v.addWidget(self.btn_mode_pc_share)

        # 6. Screen Recording to MP4
        m6 = ModeShiftButton("Record to MP4 (HD Capture)", "🔴", "#ef4444")
        m6.setToolTip("Mirrors device and records high-definition MP4 video directly to the 'recordings' folder.")
        m6.clicked.connect(lambda: self.shift_to_mode("record"))
        v.addWidget(m6)

        # 7. Audio-Only Stream
        m7 = ModeShiftButton("Audio-Only Stream", "🔊", "#f59e0b")
        m7.setToolTip("Streams phone music, podcasts, or calls to your PC speakers with zero video lag.")
        m7.clicked.connect(lambda: self.shift_to_mode("audio_only"))
        v.addWidget(m7)

        v.addStretch()
        scroll.setWidget(container)
        return scroll

    def create_settings_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(6, 8, 6, 8)

        # Video Quality Settings
        grp_video = QGroupBox("📺 Display & Video Settings")
        g_layout = QGridLayout(grp_video)
        g_layout.setSpacing(8)

        g_layout.addWidget(QLabel("Max Resolution:"), 0, 0)
        self.combo_res = QComboBox()
        self.combo_res.addItems(["Native (Full Quality)", "2560 (2K QHD)", "1920 (1080p FHD)", "1280 (720p HD)", "854 (480p Fast)"])
        self.combo_res.setCurrentIndex(0)
        self.combo_res.currentIndexChanged.connect(self.on_setting_changed)
        g_layout.addWidget(self.combo_res, 0, 1)

        g_layout.addWidget(QLabel("Video Bitrate:"), 1, 0)
        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems(["4 Mbps (Fast / Low Bandwidth)", "8 Mbps (Default Balanced)", "12 Mbps (High Definition)", "16 Mbps (Ultra Clear)", "24 Mbps (Maximum Fidelity)"])
        self.combo_bitrate.setCurrentIndex(1)
        self.combo_bitrate.currentIndexChanged.connect(self.on_setting_changed)
        g_layout.addWidget(self.combo_bitrate, 1, 1)

        g_layout.addWidget(QLabel("Max Frame Rate:"), 2, 0)
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["60 FPS (Ultra Smooth)", "30 FPS (Battery Friendly)", "120 FPS (High Refresh Rate)"])
        self.combo_fps.setCurrentIndex(0)
        self.combo_fps.currentIndexChanged.connect(self.on_setting_changed)
        g_layout.addWidget(self.combo_fps, 2, 1)

        g_layout.addWidget(QLabel("Video Codec:"), 3, 0)
        self.combo_codec = QComboBox()
        self.combo_codec.addItems(["H.264 (Universal / Hardware Accelerated)", "H.265 (High Efficiency HEVC)", "AV1 (Next-Gen)", "VP9", "VP8"])
        self.combo_codec.setCurrentIndex(0)
        self.combo_codec.currentIndexChanged.connect(self.on_setting_changed)
        g_layout.addWidget(self.combo_codec, 3, 1)

        layout.addWidget(grp_video)

        # Camera Webcam Configuration (30 FPS Native True Color)
        grp_camera = QGroupBox("📷 Camera Webcam Configuration")
        c_layout = QGridLayout(grp_camera)
        c_layout.setSpacing(8)

        c_layout.addWidget(QLabel("Camera Sensor:"), 0, 0)
        self.combo_cam_id = QComboBox()
        self.combo_cam_id.addItems([
            "Rear Main 4K Camera (Camera ID 0 - Best Colors)",
            "Front Selfie Camera (Camera ID 1)",
            "Secondary Wide / Macro Camera (Camera ID 2)"
        ])
        self.combo_cam_id.setCurrentIndex(0)
        self.combo_cam_id.currentIndexChanged.connect(self.on_setting_changed)
        c_layout.addWidget(self.combo_cam_id, 0, 1)

        c_layout.addWidget(QLabel("Camera FPS:"), 1, 0)
        self.combo_cam_fps = QComboBox()
        self.combo_cam_fps.addItems(["30 FPS (Hardware Native - Perfect Color & Exposure)", "24 FPS (Cinematic)", "15 FPS (Low Light)"])
        self.combo_cam_fps.setCurrentIndex(0)
        self.combo_cam_fps.currentIndexChanged.connect(self.on_setting_changed)
        c_layout.addWidget(self.combo_cam_fps, 1, 1)

        c_layout.addWidget(QLabel("Camera Size:"), 2, 0)
        self.combo_cam_res = QComboBox()
        self.combo_cam_res.addItems(["1920x1080 (Full HD 1080p)", "1280x720 (HD 720p)", "4080x3072 (Full Sensor 12MP)"])
        self.combo_cam_res.setCurrentIndex(0)
        self.combo_cam_res.currentIndexChanged.connect(self.on_setting_changed)
        c_layout.addWidget(self.combo_cam_res, 2, 1)

        self.chk_camera_torch = QCheckBox("Flashlight / Torch ON during webcam")
        self.chk_camera_torch.toggled.connect(self.on_setting_changed)
        c_layout.addWidget(self.chk_camera_torch, 3, 0, 1, 2)

        layout.addWidget(grp_camera)

        # Stream Flags
        grp_flags = QGroupBox("🛡️ Stream Audio & Touch Options")
        f_layout = QVBoxLayout(grp_flags)
        f_layout.setSpacing(6)

        self.chk_forward_audio = QCheckBox("Forward Phone Audio to PC Speakers")
        self.chk_forward_audio.setChecked(True)
        self.chk_forward_audio.toggled.connect(self.on_setting_changed)
        f_layout.addWidget(self.chk_forward_audio)

        self.chk_show_touches = QCheckBox("Show Physical Finger Touches on Screen (-t)")
        self.chk_show_touches.toggled.connect(self.on_setting_changed)
        f_layout.addWidget(self.chk_show_touches)

        layout.addWidget(grp_flags)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def create_connectivity_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(6, 8, 6, 8)

        # Wi-Fi Pairing
        grp_wifi = QGroupBox("📶 Wi-Fi Wireless Connection")
        w_layout = QVBoxLayout(grp_wifi)
        w_layout.setSpacing(8)

        lbl_wifi_desc = QLabel("Connect your phone wirelessly over local Wi-Fi. Once paired, you can unplug your USB cable completely and use Scrcpy from anywhere!")
        lbl_wifi_desc.setWordWrap(True)
        lbl_wifi_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        w_layout.addWidget(lbl_wifi_desc)

        btn_pair_wifi = QPushButton("🚀 1-Click Connect Wi-Fi & Unplug USB")
        btn_pair_wifi.setStyleSheet("background-color: #0d9488; color: white; font-weight: 800; padding: 10px; border-radius: 8px;")
        btn_pair_wifi.clicked.connect(self.connect_wireless_smart)
        w_layout.addWidget(btn_pair_wifi)

        btn_disconnect_wifi = QPushButton("🔌 Disconnect Wireless Sessions")
        btn_disconnect_wifi.clicked.connect(self.disconnect_wireless_action)
        w_layout.addWidget(btn_disconnect_wifi)

        layout.addWidget(grp_wifi)

        # File Drop & APK Install
        grp_files = QGroupBox("📥 Drag & Drop Files / APKs")
        file_layout = QVBoxLayout(grp_files)
        file_layout.setSpacing(8)

        lbl_drop = QLabel("• <b>Drop an APK</b> anywhere on this window to install it on your phone.\n• <b>Drop photos, videos, or files</b> to push them to /sdcard/Download/.")
        lbl_drop.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lbl_drop.setWordWrap(True)
        file_layout.addWidget(lbl_drop)

        btn_install_apk = QPushButton("📦 Select & Install APK File...")
        btn_install_apk.clicked.connect(self.install_apk_dialog)
        file_layout.addWidget(btn_install_apk)

        layout.addWidget(grp_files)

        # Maintenance Tools
        grp_maint = QGroupBox("🔧 Android Maintenance")
        m_layout = QHBoxLayout(grp_maint)
        m_layout.setSpacing(8)

        btn_reboot = QPushButton("🔄 Reboot Phone")
        btn_reboot.clicked.connect(self.prompt_reboot)
        m_layout.addWidget(btn_reboot)

        btn_restart_adb = QPushButton("🔁 Restart ADB Server")
        btn_restart_adb.clicked.connect(self.restart_adb_server)
        m_layout.addWidget(btn_restart_adb)

        layout.addWidget(grp_maint)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def create_guide_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(6, 8, 6, 8)

        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setHtml("""
        <h3 style="color:#38bdf8;">🛡️ Lock Screen Pattern & Black Screen:</h3>
        <p><b>Why does the screen turn black on pattern/PIN?</b><br>
        Android enforces a security shield (<code>FLAG_SECURE</code>) specifically while entering passwords, PINs, or pattern locks to prevent background screen recording. Once unlocked, the screen immediately reappears!</p>
        <p><b>👉 How to prevent the screen from ever locking while connected:</b><br>
        Open phone <b>Settings -> Additional settings -> Developer options</b> and turn <b>ON</b>: <code>Stay awake (Screen will never sleep while charging)</code>.<br>
        Your phone will stay on the home screen whenever plugged into PC!</p>

        <h3 style="color:#38bdf8;">🖱️ Mouse & Keyboard on Xiaomi / POCO:</h3>
        <p>This Control Center uses <b>Hardware UHID Emulation</b> (<code>--keyboard=uhid --mouse=uhid</code>). UHID simulates a physical USB mouse and keyboard directly at the Android Linux kernel level, bypassing Xiaomi's <code>INJECT_EVENTS</code> permission block completely!</p>
        <ul>
            <li><b>Left-Alt</b>: Releases the mouse pointer from the phone mirror back to your Windows desktop.</li>
            <li><b>Right-Click</b>: Sends Back button (or turns phone screen ON if asleep!).</li>
            <li><b>Middle-Click</b>: Sends Home button.</li>
            <li><b>Mouse Wheel</b>: Scrolls vertically inside phone apps.</li>
        </ul>

        <h3 style="color:#38bdf8;">⌨️ Keyboard Shortcuts (Left-Alt Modifier):</h3>
        <ul>
            <li><b>Alt + O</b>: Turn physical screen OFF (keep PC mirror active)</li>
            <li><b>Alt + Shift + O</b>: Turn physical screen back ON</li>
            <li><b>Alt + P</b>: Power key</li>
            <li><b>Alt + H</b>: Home key</li>
            <li><b>Alt + B</b>: Back key</li>
            <li><b>Alt + S</b>: Recent apps</li>
            <li><b>Alt + N</b>: Pull down notification shade</li>
            <li><b>Alt + F</b>: Fullscreen mirror</li>
            <li><b>Alt + C / Alt + V</b>: Copy / Paste between PC and Phone</li>
        </ul>
        """)
        layout.addWidget(guide_text)

        btn_open_presets = QPushButton("📂 Open Presets Folder in Windows Explorer")
        btn_open_presets.clicked.connect(lambda: os.startfile(PRESETS_DIR))
        layout.addWidget(btn_open_presets)

        scroll.setWidget(container)
        return scroll

    def create_footer(self):
        card = QFrame()
        card.setStyleSheet("background-color: #101827; border: 1px solid #22324f; border-radius: 8px; padding: 6px;")
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 6, 10, 6)

        cmd_row = QHBoxLayout()
        cmd_lbl = QLabel("💻 Live Command:")
        cmd_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        cmd_row.addWidget(cmd_lbl)

        self.txt_cmd_preview = QLabel("scrcpy")
        self.txt_cmd_preview.setStyleSheet("color: #cbd5e1; font-family: 'Consolas', monospace; font-size: 11px; background: #0b111e; padding: 3px 6px; border-radius: 4px;")
        cmd_row.addWidget(self.txt_cmd_preview, stretch=1)

        btn_copy_cmd = QPushButton("📋 Copy")
        btn_copy_cmd.setFixedWidth(64)
        btn_copy_cmd.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        btn_copy_cmd.clicked.connect(self.copy_command_preview)
        cmd_row.addWidget(btn_copy_cmd)
        layout.addLayout(cmd_row)

        bot_row = QHBoxLayout()
        self.lbl_status = QLabel("Ready • Scrcpy v4.1 Active • Hardware UHID Enabled")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        bot_row.addWidget(self.lbl_status)
        bot_row.addStretch()

        self.btn_stop = QPushButton("⏹️ Stop Active Session")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background: #e11d48;
                border: 1px solid #f43f5e;
                color: white;
                font-weight: 700;
                padding: 4px 14px;
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover { background: #be123c; }
        """)
        self.btn_stop.clicked.connect(self.stop_all_sessions)
        self.btn_stop.setEnabled(False)
        bot_row.addWidget(self.btn_stop)

        layout.addLayout(bot_row)
        return card

    # ----------------- Start & Manage Live Mirror -----------------

    def initial_startup(self):
        """Discovers devices and auto-starts live mirror in hero panel."""
        log_debug("Executing initial_startup...")
        self.refresh_devices()
        devices = get_connected_devices()
        log_debug(f"initial_startup detected devices: {devices}")
        if devices:
            self.start_live_mirror()

    def build_scrcpy_command(self, mode):
        cmd = [SCRCPY_EXE]

        serial = self.get_target_serial()
        if serial:
            cmd.extend(["-s", serial])

        # Assign unique window title
        cmd.append(f"--window-title={self.scrcpy_title}")

        # Input engine: UHID by default (bypasses Xiaomi Security block!)
        if mode in ("full", "screen_off", "record"):
            cmd.extend([
                "--keyboard=uhid",
                "--mouse=uhid",
                "--mouse-bind=bhsn:++++",  # Right-click is BACK & powers on screen if off!
                "--shortcut-mod=lalt"
            ])
        elif mode == "view_only":
            cmd.append("--no-control")

        # Mode Specifics
        if mode == "screen_off":
            cmd.append("--turn-screen-off")
            self.is_screen_physically_off = True
        else:
            self.is_screen_physically_off = False

        if mode == "camera":
            cmd.append("--video-source=camera")
            cam_idx = self.combo_cam_id.currentIndex()
            cmd.append(f"--camera-id={cam_idx}")

            fps_map = ["30", "24", "15"]
            cmd.append(f"--camera-fps={fps_map[self.combo_cam_fps.currentIndex()]}")

            res_map = ["1920x1080", "1280x720", "4080x3072"]
            cmd.append(f"--camera-size={res_map[self.combo_cam_res.currentIndex()]}")

            if self.chk_camera_torch.isChecked():
                cmd.append("--camera-torch")
        else:
            # Resolution limit
            res_idx = self.combo_res.currentIndex()
            if res_idx == 1: cmd.extend(["-m", "2560"])
            elif res_idx == 2: cmd.extend(["-m", "1920"])
            elif res_idx == 3: cmd.extend(["-m", "1280"])
            elif res_idx == 4: cmd.extend(["-m", "854"])

            # Bitrate
            b_idx = self.combo_bitrate.currentIndex()
            bitrates = ["4M", "8M", "12M", "16M", "24M"]
            cmd.extend(["-b", bitrates[b_idx]])

            # FPS
            f_idx = self.combo_fps.currentIndex()
            fps_map = ["60", "30", "120"]
            cmd.extend(["--max-fps", fps_map[f_idx]])

            # Codec
            c_idx = self.combo_codec.currentIndex()
            codec_map = ["h264", "h265", "av1", "vp9", "vp8"]
            if c_idx < len(codec_map):
                cmd.extend(["--video-codec", codec_map[c_idx]])

        if not self.chk_forward_audio.isChecked():
            cmd.append("--no-audio")

        if self.chk_show_touches.isChecked():
            cmd.append("-t")

        if mode == "record":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rec_file = os.path.join(RECORDINGS_DIR, f"scrcpy_rec_{timestamp}.mp4")
            cmd.extend([f"--record={rec_file}", "--record-format=mp4"])
            self.lbl_status.setText(f"Recording to: scrcpy_rec_{timestamp}.mp4")

        elif mode == "audio_only":
            cmd.extend(["--no-video", "--audio-codec=opus"])

        # Window geometry and borderless config
        if self.layout_mode == "embedded":
            pt = self.phone_frame.mapToGlobal(QPoint(0, 0))
            frame_w = max(240, self.phone_frame.width())
            frame_h = max(360, self.phone_frame.height())
            cmd.extend([
                "--window-borderless",
                f"--window-x={pt.x()}",
                f"--window-y={pt.y()}",
                f"--window-width={frame_w}",
                f"--window-height={frame_h}"
            ])
        elif self.layout_mode == "docked":
            geo = self.geometry()
            dock_width = max(360, int(geo.height() * 0.46))
            dock_x = max(0, geo.x() - dock_width - 8)
            dock_y = geo.y()
            dock_height = geo.height()
            cmd.extend([
                "--window-borderless",
                f"--window-x={dock_x}",
                f"--window-y={dock_y}",
                f"--window-width={dock_width}",
                f"--window-height={dock_height}"
            ])

        return cmd

    def start_live_mirror(self):
        """Launches scrcpy under the Process Supervisor and initiates window management."""
        self.stop_scrcpy_process()
        kill_orphaned_scrcpy()

        if not os.path.isfile(SCRCPY_EXE) and not shutil.which(SCRCPY_EXE):
            log_debug("scrcpy executable not found.")
            QMessageBox.warning(
                self,
                "Scrcpy Not Found",
                "scrcpy executable was not found.\n\n"
                "Please run 'setup_scrcpy.ps1' to automatically download official scrcpy binaries,\n"
                "or install scrcpy and adb to your system PATH."
            )
            self.lbl_status.setText("Launch failed: scrcpy binary missing.")
            return

        cmd = self.build_scrcpy_command(self.current_mode)
        log_debug(f"start_live_mirror command: {' '.join(cmd)}")
        self.update_command_preview()

        self.lbl_status.setText(f"Starting live mirror ({self.current_mode})...")
        self.placeholder_widget.show()
        self.ph_text.setText("Connecting Live Screen...\n(Direct3D11 Native Pipeline)")

        try:
            self.session_log_file = open(os.path.join(SCRIPT_DIR, "scrcpy_session.log"), "w", encoding="utf-8", errors="replace")
            self.scrcpy_proc = subprocess.Popen(cmd, cwd=SCRIPT_DIR, stdout=self.session_log_file, stderr=subprocess.STDOUT)
            log_debug(f"scrcpy_proc launched with PID: {self.scrcpy_proc.pid}")
            self.btn_stop.setEnabled(True)
            self.embed_attempts = 0
            self.embed_timer.start(100)
            self.update_screen_power_label()
        except Exception as e:
            log_debug(f"Failed to start scrcpy: {e}")
            QMessageBox.critical(self, "Launch Error", f"Failed to start scrcpy:\n{e}")
            self.lbl_status.setText(f"Launch failed: {e}")

    def _poll_and_manage_window(self):
        """Locates the Scrcpy window handle and applies layout management."""
        self.embed_attempts += 1
        hwnd = user32.FindWindowW(None, self.scrcpy_title)
        if hwnd:
            log_debug(f"_poll_and_manage_window found HWND: {hwnd} on attempt {self.embed_attempts}")
            self.embed_timer.stop()
            self.scrcpy_hwnd = hwnd

            if self.layout_mode == "embedded":
                self.resize_embedded_window()
                self.placeholder_widget.hide()
                self.lbl_status.setText("🟢 Live Mobile Screen Active & Embedded (UHID Mouse On)!")
            elif self.layout_mode == "docked":
                self.dock_beside_control_center()
                self.placeholder_widget.show()
                self.ph_text.setText("Live Screen Docked Beside Control Center.")
                self.lbl_status.setText("🟢 Live Mobile Screen Docked Side-by-Side!")
            else:  # floating
                self.placeholder_widget.show()
                self.ph_text.setText("Live Screen Running in Floating Window.")
                self.lbl_status.setText("🟢 Live Mobile Screen Floating!")
        elif self.embed_attempts > 60:
            self.embed_timer.stop()
            self.ph_text.setText("Mirror window started.\nIf not embedded, check taskbar.")

    def resize_embedded_window(self):
        if self.scrcpy_hwnd and self.layout_mode == "embedded":
            pt = self.phone_frame.mapToGlobal(QPoint(0, 0))
            user32.SetWindowPos(
                self.scrcpy_hwnd, 0,
                pt.x(), pt.y(), self.phone_frame.width(), self.phone_frame.height(),
                SWP_NOZORDER | SWP_NOACTIVATE
            )

    def dock_beside_control_center(self):
        """Positions Scrcpy seamlessly on the left of the Control Center."""
        if not self.scrcpy_hwnd:
            return
        geo = self.geometry()
        # Phone aspect ratio ~ 9:20 or ~ 1:2
        dock_width = max(360, int(geo.height() * 0.46))
        dock_x = max(0, geo.x() - dock_width - 8)
        dock_y = geo.y()
        dock_height = geo.height()

        user32.SetWindowPos(
            self.scrcpy_hwnd, 0,
            dock_x, dock_y, dock_width, dock_height,
            SWP_NOZORDER | SWP_NOACTIVATE
        )

    def on_layout_mode_changed(self):
        idx = self.combo_layout.currentIndex()
        if idx == 0:
            self.layout_mode = "embedded"
        elif idx == 1:
            self.layout_mode = "docked"
        else:
            self.layout_mode = "floating"

        if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
            self.start_live_mirror()
        elif not self.scrcpy_proc:
            self.start_live_mirror()

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.scrcpy_hwnd:
            if self.layout_mode == "embedded":
                self.resize_embedded_window()
            elif self.layout_mode == "docked":
                self.dock_beside_control_center()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'splitter') and hasattr(self, 'device_aspect_ratio'):
            target_w = max(260, int(self.height() * self.device_aspect_ratio))
            right_w = max(500, self.width() - target_w)
            self.splitter.setSizes([target_w, right_w])
        if self.scrcpy_hwnd:
            if self.layout_mode == "embedded":
                self.resize_embedded_window()
            elif self.layout_mode == "docked":
                self.dock_beside_control_center()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange and self.scrcpy_hwnd:
            if self.isMinimized():
                user32.ShowWindow(self.scrcpy_hwnd, 0)  # SW_HIDE
            else:
                user32.ShowWindow(self.scrcpy_hwnd, 1)  # SW_SHOWNORMAL
                if self.layout_mode == "embedded":
                    self.resize_embedded_window()
                elif self.layout_mode == "docked":
                    self.dock_beside_control_center()

    def shift_to_mode(self, mode):
        """Instantly shifts mode without opening extra python or terminal windows."""
        if mode == self.current_mode:
            if mode == "screen_off" and not self.is_screen_physically_off:
                self.turn_physical_screen_off()
            return

        self.current_mode = mode
        mode_titles = {
            "full": "🎮 Full Interactive Control",
            "screen_off": "🔋 Screen-Off Battery Saver",
            "view_only": "👁️ View-Only Monitor",
            "camera": "📷 Mobile Webcam 30 FPS",
            "record": "🔴 HD Screen Recording",
            "audio_only": "🔊 Audio-Only Stream"
        }
        self.lbl_hero_badge.setText(mode_titles.get(mode, "Live Screen"))

        # If switching between full and screen_off while running, use instantaneous shortcut
        if mode in ("full", "screen_off") and self.scrcpy_hwnd:
            if mode == "screen_off":
                self.turn_physical_screen_off()
            else:
                self.turn_physical_screen_on()
            self.lbl_status.setText(f"Shifted to {mode_titles[mode]}")
            return

        # Otherwise restart live mirror with new mode parameters
        self.start_live_mirror()

    def restart_live_mirror(self):
        self.start_live_mirror()

    def stop_scrcpy_process(self):
        self.embed_timer.stop()
        if self.scrcpy_proc:
            try:
                self.scrcpy_proc.terminate()
            except Exception:
                pass
            self.scrcpy_proc = None
        self.scrcpy_hwnd = None

    def stop_all_sessions(self):
        self.stop_scrcpy_process()
        kill_orphaned_scrcpy()
        if self.is_streaming_pc:
            self.stop_pc_to_phone_stream()
        self.btn_stop.setEnabled(False)
        self.placeholder_widget.show()
        self.ph_text.setText("Session stopped.\nClick 'Launch Live Mirror' to resume.")
        self.lbl_status.setText("All active sessions terminated.")

    def cleanup_all_processes(self):
        self.stop_all_sessions()

    # ----------------- Screen Power & Navigation -----------------

    def toggle_physical_screen_power(self):
        if self.is_screen_physically_off:
            self.turn_physical_screen_on()
        else:
            self.turn_physical_screen_off()

    def turn_physical_screen_off(self):
        """Sends Alt + O to Scrcpy to turn phone screen OFF while mirror stays live!"""
        self.is_screen_physically_off = True
        self.send_scrcpy_key_shortcut(VK_O, shift=False)
        self.update_screen_power_label()
        self.lbl_status.setText("⚡ Physical phone screen turned OFF. PC mirror active & saving battery!")

    def turn_physical_screen_on(self):
        """Sends Alt + Shift + O to Scrcpy to turn phone screen back ON."""
        self.is_screen_physically_off = False
        self.send_scrcpy_key_shortcut(VK_O, shift=True)
        self.update_screen_power_label()
        self.lbl_status.setText("💡 Physical phone screen turned ON.")

    def update_screen_power_label(self):
        if self.is_screen_physically_off:
            self.lbl_screen_power.setText("🔋 Phone Display: OFF (Saving Battery)")
            self.lbl_screen_power.setStyleSheet("""
                background: #064e3b;
                color: #34d399;
                border: 1px solid #059669;
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
            """)
            self.btn_toggle_screen_off.setText("💡 Screen ON")
            self.btn_toggle_screen_off.setStyleSheet("""
                QPushButton {
                    background-color: #0284c7;
                    color: white;
                    font-weight: 800;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover { background-color: #0369a1; }
            """)
        else:
            self.lbl_screen_power.setText("💡 Phone Display: ON")
            self.lbl_screen_power.setStyleSheet("""
                background: #1e293b;
                color: #38bdf8;
                border: 1px solid #38bdf855;
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
            """)
            self.btn_toggle_screen_off.setText("⚡ Screen OFF")
            self.btn_toggle_screen_off.setStyleSheet("""
                QPushButton {
                    background-color: #065f46;
                    color: #34d399;
                    border: 1px solid #059669;
                    font-weight: 800;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover { background-color: #047857; color: white; }
            """)

    def send_scrcpy_key_shortcut(self, key_code, shift=False):
        """Sends shortcut with Left-Alt modifier directly to Scrcpy window."""
        if not self.scrcpy_hwnd:
            return
        user32.SetForegroundWindow(self.scrcpy_hwnd)
        time.sleep(0.02)
        user32.keybd_event(VK_MENU, 0, 0, 0)
        if shift:
            user32.keybd_event(VK_SHIFT, 0, 0, 0)
        user32.keybd_event(key_code, 0, 0, 0)
        user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)
        if shift:
            user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

    def wake_and_unlock_action(self):
        """Dual-pipeline wakeup: Wakes device screen, dismisses keyguard, brings launcher forward."""
        serial = self.get_target_serial()
        prefix = ["-s", serial] if serial else []

        # 1. Send scrcpy power-on shortcut if running
        self.send_scrcpy_key_shortcut(VK_P, shift=False)

        # 2. Issue ADB commands that wake Xiaomi without requiring INJECT_EVENTS permission
        run_adb(prefix + ["shell", "cmd statusbar expand-notifications; cmd statusbar collapse; wm dismiss-keyguard; am start -a android.intent.action.MAIN -c android.intent.category.HOME"])

        self.is_screen_physically_off = False
        self.update_screen_power_label()
        self.lbl_status.setText("🔓 Wake & Dismiss Lockscreen command executed!")

    def send_phone_nav_key(self, nav_type):
        serial = self.get_target_serial()
        prefix = ["-s", serial] if serial else []

        if nav_type == "back":
            self.send_scrcpy_key_shortcut(VK_B)
        elif nav_type == "home":
            self.send_scrcpy_key_shortcut(VK_H)
            run_adb(prefix + ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME"])
        elif nav_type == "recents":
            self.send_scrcpy_key_shortcut(VK_S)
        elif nav_type == "notif":
            self.send_scrcpy_key_shortcut(VK_N)
            run_adb(prefix + ["shell", "cmd", "statusbar", "expand-notifications"])
        elif nav_type == "volup":
            self.send_scrcpy_key_shortcut(VK_UP)
        elif nav_type == "voldown":
            self.send_scrcpy_key_shortcut(VK_DOWN)

    # ----------------- Wi-Fi Wireless Pairing -----------------

    def connect_wireless_smart(self):
        """Smart Wi-Fi connector with robust detection, feedback, and zero empty dialogs."""
        self.lbl_status.setText("Inspecting Wi-Fi configuration...")
        QApplication.processEvents()

        devices = get_connected_devices()

        # Check if already connected over Wi-Fi
        wifi_dev = next((d for d in devices if d["is_wifi"]), None)
        if wifi_dev:
            self.selected_serial = wifi_dev["serial"]
            idx = self.device_combo.findData(wifi_dev["serial"])
            if idx >= 0:
                self.device_combo.setCurrentIndex(idx)
            QMessageBox.information(
                self,
                "Wi-Fi Connection Active",
                f"✅ Your phone is already connected wirelessly at:\n{wifi_dev['serial']}\n\n"
                "The target has been switched to Wi-Fi. You can now safely unplug your USB cable!"
            )
            self.lbl_status.setText(f"Active device set to Wi-Fi: {wifi_dev['serial']}")
            self.start_live_mirror()
            return

        # Find USB device to get its Wi-Fi IP
        usb_dev = next((d for d in devices if not d["is_wifi"]), None)
        if not usb_dev:
            QMessageBox.warning(
                self,
                "No USB Device Connected",
                "Please connect your phone via USB cable once to initialize Wi-Fi pairing."
            )
            return

        ip = get_device_wlan_ip(usb_dev["serial"])
        if not ip:
            QMessageBox.warning(
                self,
                "Phone Wi-Fi IP Not Detected",
                "Could not detect your phone's Wi-Fi IP address.\n\n"
                "Please verify:\n"
                "1. Is Wi-Fi turned ON on your phone?\n"
                "2. Is your phone connected to the same Wi-Fi router as this PC?"
            )
            return

        self.lbl_status.setText(f"Enabling TCP/IP 5555 on {ip}...")
        QApplication.processEvents()

        run_adb(["-s", usb_dev["serial"], "tcpip", "5555"])
        QTimer.singleShot(1800, lambda: self._finish_smart_connect(ip))

    def _finish_smart_connect(self, ip):
        target = f"{ip}:5555"
        res = run_adb(["connect", target], timeout=8)

        if "connected to" in res.lower() or "already connected" in res.lower():
            QMessageBox.information(
                self,
                "Wireless Connected Successfully!",
                f"🎉 Connected wirelessly to {target}!\n\n"
                "You can now unplug your USB cable and use Scrcpy completely wirelessly anywhere!"
            )
            self.refresh_devices()
            idx = self.device_combo.findData(target)
            if idx >= 0:
                self.device_combo.setCurrentIndex(idx)
                self.selected_serial = target
            self.lbl_status.setText(f"Connected wirelessly to {target}")
            self.start_live_mirror()
        else:
            QMessageBox.warning(
                self,
                "Wi-Fi Connection Status",
                f"Attempted connection to {target}.\n\n"
                f"ADB response:\n{res if res else 'Connection timed out'}\n\n"
                "Troubleshooting:\n"
                "1. Ensure your PC and phone are connected to the same router.\n"
                "2. Check if your router enables 'AP Client Isolation'."
            )
            self.lbl_status.setText("Wi-Fi connection attempt completed.")

    def disconnect_wireless_action(self):
        res = run_adb(["disconnect"])
        self.lbl_status.setText("Disconnected wireless adb sessions.")
        self.refresh_devices()
        QMessageBox.information(self, "Disconnected", f"Wireless sessions disconnected.\n{res}")

    # ----------------- PC Screen to Phone Streamer -----------------

    def toggle_pc_to_phone_stream(self):
        if self.is_streaming_pc:
            self.stop_pc_to_phone_stream()
        else:
            self.start_pc_to_phone_stream()

    def start_pc_to_phone_stream(self):
        streamer_script = os.path.join(SCRIPT_DIR, "pc_to_phone_streamer.py")
        if not os.path.exists(streamer_script):
            QMessageBox.warning(self, "Streamer Missing", "pc_to_phone_streamer.py was not found.")
            return

        self.lbl_status.setText("Starting PC Screen Stream for Google Assistant...")
        try:
            self.active_streamer_proc = subprocess.Popen([sys.executable, streamer_script], cwd=SCRIPT_DIR)
            self.is_streaming_pc = True
            self.btn_mode_pc_share.setText("⏹️  Stop Assistant AI Share")
            self.btn_mode_pc_share.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    font-weight: 800;
                    border: 2px solid #dc2626;
                    border-radius: 10px;
                    padding: 12px 14px;
                    text-align: left;
                }
            """)
            self.lbl_status.setText("PC Screen Stream Active! Phone browser opened. Ask Google Assistant about your screen.")
        except Exception as e:
            QMessageBox.critical(self, "Streamer Error", f"Failed to launch PC streamer:\n{e}")

    def stop_pc_to_phone_stream(self):
        if self.active_streamer_proc:
            try:
                self.active_streamer_proc.terminate()
            except Exception:
                pass
            self.active_streamer_proc = None

        run_adb(["reverse", "--remove", "tcp:8765"])
        self.is_streaming_pc = False
        self.btn_mode_pc_share.setText("🤖  PC Screen to Phone (Assistant AI)")
        self.btn_mode_pc_share.setStyleSheet("""
            QPushButton {
                background-color: #111a2c;
                border: 2px solid #22324f;
                border-radius: 10px;
                color: #f1f5f9;
                font-weight: 700;
                padding: 12px 14px;
                text-align: left;
            }
            QPushButton:hover {
                border-color: #6366f1;
                background-color: #17243c;
            }
        """)
        self.lbl_status.setText("PC Screen Stream stopped.")

    # ----------------- Window Snapping & Zoom -----------------

    def snap_window(self, mode):
        screen = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        if mode == "left":
            self.showNormal()
            self.setGeometry(screen.x(), screen.y(), screen.width() // 2, screen.height())
            self.lbl_status.setText("📐 Snapped to Left Half of screen.")
        elif mode == "right":
            self.showNormal()
            self.setGeometry(screen.x() + screen.width() // 2, screen.y(), screen.width() // 2, screen.height())
            self.lbl_status.setText("📐 Snapped to Right Half of screen.")
        elif mode == "dock":
            self.showNormal()
            dock_w = 460
            self.setGeometry(screen.x() + screen.width() - dock_w, screen.y(), dock_w, screen.height())
            self.lbl_status.setText("📐 Snapped to Compact Side-Dock.")
        elif mode == "center":
            self.showNormal()
            w = int(screen.width() * 0.75)
            h = int(screen.height() * 0.82)
            x = screen.x() + (screen.width() - w) // 2
            y = screen.y() + (screen.height() - h) // 2
            self.setGeometry(x, y, w, h)
            self.lbl_status.setText("📐 Snapped to Center Floating view.")
        elif mode == "max":
            if self.isMaximized():
                self.showNormal()
                self.lbl_status.setText("📐 Restored Normal window size.")
            else:
                self.showMaximized()
                self.lbl_status.setText("⛶ Maximized window.")
        QTimer.singleShot(150, self.resize_embedded_window)

    def wheelEvent(self, event):
        """Ctrl + Mouse Wheel scales entire UI font size."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.change_font_size(1)
            elif delta < 0:
                self.change_font_size(-1)
            event.accept()
        else:
            super().wheelEvent(event)

    def change_font_size(self, delta):
        new_size = max(11, min(22, self.base_font_size + delta))
        if new_size != self.base_font_size:
            self.base_font_size = new_size
            self.apply_theme()
            self.lbl_zoom.setText(f"{int(self.base_font_size / 14 * 100)}%")

    # ----------------- Drag & Drop Files -----------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.lbl_status.setText("📥 Drop file to Push or Install APK on phone...")

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        serial = self.get_target_serial()
        for u in urls:
            local_path = u.toLocalFile()
            if not local_path or not os.path.exists(local_path):
                continue
            if local_path.lower().endswith(".apk"):
                self.install_apk_file(local_path, serial)
            else:
                self.push_file_to_device(local_path, serial)

    def push_file_to_device(self, file_path, serial=None):
        filename = os.path.basename(file_path)
        self.lbl_status.setText(f"Pushing {filename} to /sdcard/Download/...")
        QApplication.processEvents()
        prefix = ["-s", serial] if serial else []
        res = run_adb(prefix + ["push", file_path, f"/sdcard/Download/{filename}"])
        if "pushed" in res.lower() or "1 file pushed" in res.lower():
            QMessageBox.information(self, "File Pushed", f"Successfully pushed:\n{filename}\nSaved to phone's /sdcard/Download/")
            self.lbl_status.setText(f"File pushed: {filename}")
        else:
            QMessageBox.warning(self, "Push Result", f"ADB output:\n{res}")

    def install_apk_file(self, apk_path, serial=None):
        filename = os.path.basename(apk_path)
        self.lbl_status.setText(f"Installing {filename} on phone...")
        QApplication.processEvents()
        prefix = ["-s", serial] if serial else []
        res = run_adb(prefix + ["install", "-r", apk_path], timeout=40)
        if "success" in res.lower():
            QMessageBox.information(self, "APK Installed", f"Successfully installed {filename} on your device!")
            self.lbl_status.setText(f"Installed: {filename}")
        else:
            QMessageBox.warning(self, "Install Failed", f"ADB result:\n{res}\n\nTip: On Xiaomi/Poco, ensure 'Install via USB' is enabled in Developer Options.")

    def install_apk_dialog(self):
        apk_path, _ = QFileDialog.getOpenFileName(self, "Select APK File", "", "Android Package (*.apk)")
        if apk_path:
            self.install_apk_file(apk_path, self.get_target_serial())

    # ----------------- Telemetry & Refresh -----------------

    def check_process_liveness(self):
        if self.scrcpy_proc is not None:
            ret = self.scrcpy_proc.poll()
            if ret is not None:
                log_debug(f"scrcpy_proc terminated with code: {ret}")
                self.scrcpy_proc = None
                self.scrcpy_hwnd = None
                self.placeholder_widget.show()
                self.ph_text.setText("Live mirror stopped.\nClick 'Launch Live Mirror' to reconnect.")
                self.lbl_status.setText(f"Live session ended (exit code {ret}).")
                self.btn_stop.setEnabled(False)

    def refresh_devices(self):
        self.check_process_liveness()
        devices = get_connected_devices()
        target_serial = self.selected_serial

        self.device_combo.blockSignals(True)
        self.device_combo.clear()

        if not devices:
            self.led_status.setText("🔴 NO DEVICE DETECTED")
            self.led_status.setStyleSheet("background: #451a03; color: #f59e0b; border: 1px solid #78350f; border-radius: 6px; padding: 4px 10px; font-weight: 800; font-size: 12px;")
            self.lbl_dev_specs.setText("📱 Not Detected")
            self.lbl_battery.setText("🔋 Battery: --")
            self.lbl_wifi_ip.setText("📶 Wi-Fi: --")
            self.selected_serial = ""
        else:
            first_dev = devices[0]
            self.led_status.setText("🟢 DEVICE READY")
            self.led_status.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 6px; padding: 4px 10px; font-weight: 800; font-size: 12px;")

            active_dev = first_dev
            for dev in devices:
                if dev["serial"] == target_serial:
                    active_dev = dev
                    break

            hw = get_device_hardware_info(active_dev["serial"])
            wlan_ip = get_device_wlan_ip(active_dev["serial"])

            # Detect exact aspect ratio from device resolution
            try:
                res_str = hw.get("resolution", "")
                if "x" in res_str:
                    parts = [int(p) for p in res_str.split("x") if p.isdigit()]
                    if len(parts) == 2 and parts[0] > 0 and parts[1] > 0:
                        self.device_aspect_ratio = min(parts[0], parts[1]) / max(parts[0], parts[1])
            except Exception:
                pass

            charging_icon = "⚡" if hw["charging"] else ""
            self.lbl_dev_specs.setText(f"📱 {active_dev['model']} ({hw['resolution']}, {hw['android']})")
            self.lbl_battery.setText(f"🔋 {hw['battery']} {charging_icon}")
            self.lbl_wifi_ip.setText(f"📶 {wlan_ip if wlan_ip else 'USB'}")

            for dev in devices:
                badge = "[Wi-Fi]" if dev["is_wifi"] else "[USB]"
                label = f"{badge} {dev['model']} ({dev['serial']})"
                self.device_combo.addItem(label, dev["serial"])

            idx = self.device_combo.findData(active_dev["serial"])
            if idx >= 0:
                self.device_combo.setCurrentIndex(idx)
            self.selected_serial = active_dev["serial"]

        self.device_combo.blockSignals(False)
        self.update_command_preview()

    def on_device_selection_changed(self):
        self.selected_serial = self.device_combo.currentData() or ""
        self.update_command_preview()

    def on_setting_changed(self):
        self.update_command_preview()

    def get_target_serial(self):
        data = self.device_combo.currentData()
        if data:
            return data
        if self.selected_serial:
            return self.selected_serial
        devices = get_connected_devices()
        if devices:
            self.selected_serial = devices[0]["serial"]
            return self.selected_serial
        return ""

    def update_command_preview(self):
        cmd = self.build_scrcpy_command(self.current_mode)
        rel_parts = []
        for p in cmd[1:]:
            if " " in p:
                rel_parts.append(f'"{p}"')
            else:
                rel_parts.append(p)
        self.txt_cmd_preview.setText("scrcpy " + " ".join(rel_parts))

    def copy_command_preview(self):
        QApplication.clipboard().setText(self.txt_cmd_preview.text())
        self.lbl_status.setText("📋 Copied scrcpy command to clipboard!")

    def capture_phone_screenshot(self):
        serial = self.get_target_serial()
        prefix = ["-s", serial] if serial else []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        phone_path = f"/sdcard/screenshot_{timestamp}.png"
        pc_path = os.path.join(RECORDINGS_DIR, f"screenshot_{timestamp}.png")

        self.lbl_status.setText("Capturing high-definition screenshot...")
        QApplication.processEvents()

        run_adb(prefix + ["shell", "screencap", "-p", phone_path])
        run_adb(prefix + ["pull", phone_path, pc_path])
        run_adb(prefix + ["shell", "rm", phone_path])

        if os.path.exists(pc_path):
            self.lbl_status.setText(f"Screenshot saved: {os.path.basename(pc_path)}")
            QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved successfully to:\n{pc_path}")
        else:
            self.lbl_status.setText("Screenshot capture failed.")

    def prompt_reboot(self):
        reply = QMessageBox.question(self, "Reboot Phone", "Are you sure you want to reboot the connected phone?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            serial = self.get_target_serial()
            prefix = ["-s", serial] if serial else []
            run_adb(prefix + ["reboot"])
            self.lbl_status.setText("Device reboot command issued.")

    def restart_adb_server(self):
        self.lbl_status.setText("Restarting ADB server...")
        QApplication.processEvents()
        run_adb(["kill-server"])
        time.sleep(1)
        run_adb(["start-server"])
        self.refresh_devices()
        self.lbl_status.setText("ADB server restarted.")

    def closeEvent(self, event):
        self.cleanup_all_processes()
        event.accept()


if __name__ == "__main__":
    log_debug("Starting QApplication...")
    app = QApplication(sys.argv)
    log_debug("Instantiating ScrcpyUnifiedControlCenter...")
    window = ScrcpyUnifiedControlCenter()
    log_debug("Displaying window...")
    window.show()
    # Force window visibility and bring to foreground in case parent process passed SW_HIDE
    try:
        user32.ShowWindow(int(window.winId()), 1)  # SW_SHOWNORMAL
        user32.SetForegroundWindow(int(window.winId()))
    except Exception as e:
        log_debug(f"ShowWindow error: {e}")
    log_debug("Entering Qt event loop...")
    sys.exit(app.exec())
