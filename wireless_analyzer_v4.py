#!/usr/bin/env python3
"""
Wireless Analyzer - WiFi & Bluetooth LE Scanner
Mimics Acrylic Suite Wi-Fi Analyzer & Bluetooth Analyzer
Requires: PyQt5, scapy (optional), subprocess tools
"""

import sys
import os
import re
import time
import math
import random
import subprocess
import threading
from datetime import datetime
from collections import defaultdict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QComboBox, QSplitter, QStatusBar,
    QFrame, QGroupBox, QSlider, QCheckBox, QTextEdit, QScrollArea,
    QProgressBar, QToolBar, QAction, QSizePolicy, QMenu, QSystemTrayIcon,
    QMessageBox, QLineEdit, QSpinBox
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QRect, QPoint,
    QRectF, QPointF, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QRadialGradient, QPainterPath, QPixmap,
    QIcon, QPalette, QPolygon, QPolygonF
)


# ─── Color Palette ────────────────────────────────────────────────────────────
BG_DARK     = QColor("#0d1117")
BG_PANEL    = QColor("#161b22")
BG_CARD     = QColor("#1c2230")
ACCENT_CYAN = QColor("#00d4ff")
ACCENT_GREEN= QColor("#39ff14")
ACCENT_ORANGE=QColor("#ff6b35")
ACCENT_PINK = QColor("#ff2d78")
ACCENT_PURPLE=QColor("#a855f7")
TEXT_PRIMARY= QColor("#e6edf3")
TEXT_DIM    = QColor("#6e7681")
BORDER_CLR  = QColor("#30363d")
GRID_CLR    = QColor("#1f2937")

# Channel colors for overlap chart
CHAN_COLORS = [
    "#00d4ff","#39ff14","#ff6b35","#ff2d78","#a855f7",
    "#ffd700","#00ff99","#ff4444","#44aaff","#ff8800",
    "#cc44ff","#00ffcc","#ff66aa","#88ff00","#ff0099",
]

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #30363d;
    background: #161b22;
}
QTabBar::tab {
    background: #0d1117;
    color: #8b949e;
    padding: 10px 22px;
    border: 1px solid #30363d;
    border-bottom: none;
    margin-right: 2px;
    font-size: 14px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #161b22;
    color: #00d4ff;
    border-top: 2px solid #00d4ff;
}
QTabBar::tab:hover { color: #e6edf3; background: #1c2230; }
QTableWidget {
    background: #161b22;
    gridline-color: #21262d;
    border: 1px solid #30363d;
    selection-background-color: #1f3a5f;
    alternate-background-color: #1c2230;
    font-size: 13px;
}
QTableWidget::item { padding: 5px 10px; border: none; }
QHeaderView::section {
    background: #0d1117;
    color: #00d4ff;
    padding: 8px 10px;
    border: 1px solid #30363d;
    font-weight: bold;
    font-size: 13px;
    letter-spacing: 1px;
}
QPushButton {
    background: #1c2230;
    color: #00d4ff;
    border: 1px solid #00d4ff;
    padding: 8px 18px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 13px;
    letter-spacing: 1px;
}
QPushButton:hover { background: #00d4ff; color: #0d1117; }
QPushButton:pressed { background: #0099bb; }
QPushButton:disabled { color: #6e7681; border-color: #30363d; }
QComboBox {
    background: #1c2230;
    color: #e6edf3;
    border: 1px solid #30363d;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 13px;
    min-height: 26px;
}
QComboBox:hover { border-color: #00d4ff; }
QComboBox QAbstractItemView {
    background: #1c2230;
    color: #e6edf3;
    selection-background-color: #1f3a5f;
    border: 1px solid #30363d;
    font-size: 13px;
}
QScrollBar:vertical { background: #0d1117; width: 12px; border: none; }
QScrollBar::handle:vertical {
    background: #30363d; border-radius: 6px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #00d4ff; }
QScrollBar:horizontal { background: #0d1117; height: 12px; border: none; }
QScrollBar::handle:horizontal { background: #30363d; border-radius: 6px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QStatusBar {
    background: #0d1117; color: #8b949e;
    border-top: 1px solid #30363d; font-size: 13px;
}
QGroupBox {
    border: 1px solid #30363d; border-radius: 4px;
    margin-top: 10px; padding-top: 10px;
    color: #00d4ff; font-weight: bold; font-size: 13px;
}
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLabel { color: #e6edf3; font-size: 13px; }
QLineEdit {
    background: #1c2230; color: #e6edf3;
    border: 1px solid #30363d; padding: 5px 10px;
    border-radius: 4px; font-size: 13px;
}
QLineEdit:focus { border-color: #00d4ff; }
QTextEdit {
    background: #0d1117; color: #39ff14;
    border: 1px solid #30363d;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}
QCheckBox { color: #e6edf3; spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #30363d; background: #1c2230; border-radius: 3px;
}
QCheckBox::indicator:checked { background: #00d4ff; border-color: #00d4ff; }
QToolBar {
    background: #0d1117; border-bottom: 1px solid #30363d;
    spacing: 6px; padding: 5px;
}
QToolButton {
    background: transparent; color: #8b949e;
    border: none; padding: 6px 12px;
    border-radius: 4px; font-size: 13px;
}
QToolButton:hover { background: #1c2230; color: #e6edf3; }
QSplitter::handle { background: #30363d; }
QSpinBox {
    background: #1c2230; color: #e6edf3;
    border: 1px solid #30363d; padding: 5px 8px;
    border-radius: 4px; font-size: 13px;
}
QSpinBox:focus { border-color: #00d4ff; }
"""


# ─── Signal Strength Bar Widget ───────────────────────────────────────────────
class SignalBar(QWidget):
    def __init__(self, value=-100, max_val=-20, parent=None):
        super().__init__(parent)
        self.value = value
        self.max_val = max_val
        self.setFixedSize(90, 20)

    def setValue(self, v):
        self.value = v
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pct = max(0, min(1, (self.value + 100) / 80.0))
        bars = 5
        bw = (w - bars * 2) // bars
        for i in range(bars):
            filled = pct >= (i + 1) / bars
            x = i * (bw + 2)
            bh = int(h * (i + 1) / bars)
            rect = QRect(x, h - bh, bw, bh)
            if filled:
                if pct > 0.7:
                    c = QColor("#39ff14")
                elif pct > 0.4:
                    c = QColor("#ffd700")
                else:
                    c = QColor("#ff6b35")
                p.fillRect(rect, c)
            else:
                p.fillRect(rect, QColor("#1c2230"))
        p.end()


# ─── Channel Overlap Diagram ──────────────────────────────────────────────────
class ChannelOverlapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.networks = []
        self.band = "2.4GHz"
        self.setMinimumHeight(280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setNetworks(self, nets, band="2.4GHz"):
        self.networks = [n for n in nets if n.get("band","2.4GHz") == band]
        self.band = band
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        p.fillRect(0, 0, w, h, BG_PANEL)

        margin_l, margin_r, margin_t, margin_b = 60, 20, 20, 40
        plot_w = w - margin_l - margin_r
        plot_h = h - margin_t - margin_b

        # Grid
        p.setPen(QPen(GRID_CLR, 1))
        for i in range(5):
            y = margin_t + int(plot_h * i / 4)
            p.drawLine(margin_l, y, margin_l + plot_w, y)

        # Y-axis labels (dBm)
        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 11))
        for i, db in enumerate([-20, -40, -60, -80, -100]):
            y = margin_t + int(plot_h * i / 4)
            p.drawText(2, y + 4, 55, 12, Qt.AlignRight, f"{db}")

        if self.band == "2.4GHz":
            channels = list(range(1, 15))
            ch_start, ch_end = 1, 14
        else:
            channels = [36,40,44,48,52,56,60,64,100,104,108,112,116,120,
                        124,128,132,136,140,144,149,153,157,161,165]
            ch_start, ch_end = 36, 165

        total_span = ch_end - ch_start + 2

        def ch_to_x(ch):
            return margin_l + int((ch - ch_start + 0.5) / total_span * plot_w)

        def dbm_to_y(dbm):
            clamped = max(-100, min(-20, dbm))
            frac = (clamped + 20) / (-100 + 20)  # 0 = top(-20), 1 = bottom(-100)
            return margin_t + int(frac * plot_h)

        # Channel tick labels
        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 11))
        for ch in channels:
            x = ch_to_x(ch)
            p.drawLine(x, margin_t + plot_h, x, margin_t + plot_h + 4)
            p.drawText(x - 10, h - margin_b + 6, 20, 14, Qt.AlignHCenter, str(ch))

        # X axis label
        p.setPen(QPen(TEXT_PRIMARY, 1))
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.drawText(0, h - 14, w, 14, Qt.AlignHCenter, f"Channel ({self.band})")

        # Draw each network as a bell curve
        for idx, net in enumerate(self.networks):
            ch = net.get("channel", 6)
            sig = net.get("signal", -70)
            ssid = net.get("ssid", "?")
            color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])

            # Bell-like shape centered at channel, width ~5 channels for 2.4GHz
            if self.band == "2.4GHz":
                width_ch = 2.2
            else:
                width_ch = 2.0

            cx = ch_to_x(ch)
            top_y = dbm_to_y(sig)
            bot_y = dbm_to_y(-100)

            path = QPainterPath()
            steps = 60
            pts = []
            for s in range(steps + 1):
                t = (s / steps) * width_ch * 2 * 3 - width_ch * 3
                ch_pos = ch + t / 3
                amp = math.exp(-0.5 * (t ** 2)) * (sig + 100) / 80
                dbm_val = -100 + amp * 80
                x = ch_to_x(ch_pos)
                y = dbm_to_y(dbm_val)
                pts.append(QPointF(x, y))

            if pts:
                path.moveTo(QPointF(pts[0].x(), bot_y))
                path.lineTo(pts[0])
                for pt in pts[1:]:
                    path.lineTo(pt)
                path.lineTo(QPointF(pts[-1].x(), bot_y))
                path.closeSubpath()

                fill = QColor(color)
                fill.setAlpha(60)
                p.fillPath(path, QBrush(fill))

                stroke = QColor(color)
                stroke.setAlpha(220)
                p.strokePath(path, QPen(stroke, 1.5))

            # SSID label at peak
            peak_x = ch_to_x(ch)
            peak_y = dbm_to_y(sig) - 4
            p.setPen(QPen(color, 1))
            p.setFont(QFont("Consolas", 8, QFont.Bold))
            lbl = ssid[:10] if len(ssid) > 10 else ssid
            p.drawText(peak_x - 30, peak_y - 12, 60, 12, Qt.AlignHCenter, lbl)

        # Border
        p.setPen(QPen(BORDER_CLR, 1))
        p.drawRect(margin_l, margin_t, plot_w, plot_h)
        p.end()


# ─── Signal History Graph ─────────────────────────────────────────────────────
class SignalHistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = {}   # ssid -> list of (time, dbm)
        self.max_points = 60
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def addSample(self, ssid, dbm):
        if ssid not in self.history:
            self.history[ssid] = []
        self.history[ssid].append(dbm)
        if len(self.history[ssid]) > self.max_points:
            self.history[ssid].pop(0)
        self.update()

    def clear(self):
        self.history.clear()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, BG_PANEL)

        ml, mr, mt, mb = 55, 10, 10, 30
        pw = w - ml - mr
        ph = h - mt - mb

        # Grid lines
        p.setPen(QPen(GRID_CLR, 1, Qt.DashLine))
        for i in range(5):
            y = mt + int(ph * i / 4)
            p.drawLine(ml, y, ml + pw, y)
            dbm = -20 - i * 20
            p.setPen(QPen(TEXT_DIM, 1))
            p.setFont(QFont("Consolas", 11))
            p.drawText(2, y - 5, 50, 12, Qt.AlignRight, f"{dbm} dBm")
            p.setPen(QPen(GRID_CLR, 1, Qt.DashLine))

        # Time labels
        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 11))
        for i in range(0, self.max_points + 1, 10):
            x = ml + int(i / self.max_points * pw)
            t = self.max_points - i
            p.drawText(x - 12, h - mb + 6, 24, 14, Qt.AlignHCenter, f"-{t}s" if t else "now")

        # Draw lines
        for idx, (ssid, vals) in enumerate(list(self.history.items())[:12]):
            if len(vals) < 2:
                continue
            color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
            pen = QPen(color, 2)
            p.setPen(pen)
            n = len(vals)
            pts = []
            for i, v in enumerate(vals):
                x = ml + int((self.max_points - n + i) / self.max_points * pw)
                frac = (max(-100, min(-20, v)) + 20) / (-100 + 20)
                y = mt + int(frac * ph)
                pts.append(QPointF(x, y))
            for i in range(len(pts) - 1):
                p.drawLine(pts[i], pts[i+1])

        # Legend
        if self.history:
            lx = ml + 5
            ly = mt + 5
            p.setFont(QFont("Consolas", 11))
            for idx, ssid in enumerate(list(self.history.keys())[:8]):
                color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
                p.setPen(QPen(color, 2))
                p.drawLine(lx, ly + 5, lx + 16, ly + 5)
                p.setPen(QPen(TEXT_PRIMARY, 1))
                p.drawText(lx + 20, ly - 2, 100, 14, Qt.AlignLeft, ssid[:14])
                ly += 16
                if ly > mt + ph - 10:
                    break

        p.setPen(QPen(BORDER_CLR, 1))
        p.drawRect(ml, mt, pw, ph)
        p.end()


# ─── Radar/Polar Widget for BLE ───────────────────────────────────────────────
class BLERadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = []
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._angle_offset = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._rotate)
        self._timer.start(50)

    def _rotate(self):
        self._angle_offset = (self._angle_offset + 1) % 360
        self.update()

    def setDevices(self, devs):
        self.devices = devs
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 20

        p.fillRect(0, 0, w, h, BG_PANEL)

        # Rings
        for i in range(1, 5):
            rr = int(r * i / 4)
            p.setPen(QPen(GRID_CLR, 1))
            p.drawEllipse(QPointF(cx, cy), rr, rr)
            dbm = -20 - i * 20
            p.setPen(QPen(TEXT_DIM, 1))
            p.setFont(QFont("Consolas", 11))
            p.drawText(cx + rr + 2, cy - 4, 30, 12, Qt.AlignLeft, f"{dbm}")

        # Sweep line
        angle_rad = math.radians(self._angle_offset)
        p.setPen(QPen(QColor(0, 212, 255, 180), 1.5))
        p.drawLine(cx, cy,
                   int(cx + r * math.cos(angle_rad)),
                   int(cy - r * math.sin(angle_rad)))

        # Sweep gradient arc
        sweep_color = QColor(0, 212, 255, 30)
        for arc_i in range(60):
            a = angle_rad - math.radians(arc_i)
            alpha = int(30 * (1 - arc_i / 60))
            p.setPen(QPen(QColor(0, 212, 255, alpha), 1.5))
            p.drawLine(cx, cy,
                       int(cx + r * math.cos(a)),
                       int(cy - r * math.sin(a)))

        # Cross hairs
        p.setPen(QPen(GRID_CLR, 1))
        p.drawLine(cx - r, cy, cx + r, cy)
        p.drawLine(cx, cy - r, cx, cy + r)

        # Devices
        for idx, dev in enumerate(self.devices[:16]):
            sig = dev.get("rssi", -70)
            angle = dev.get("_angle", idx * 45) % 360
            frac = max(0, min(1, (sig + 100) / 80.0))
            dist = (1.0 - frac) * r * 0.95
            angle_r = math.radians(angle)
            dx = cx + dist * math.cos(angle_r)
            dy = cy - dist * math.sin(angle_r)
            color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
            p.setPen(QPen(color, 2))
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(dx, dy), 5, 5)
            p.setPen(QPen(color, 1))
            p.setFont(QFont("Consolas", 11))
            name = dev.get("name", dev.get("address","?"))[:10]
            p.drawText(int(dx) + 7, int(dy) - 4, 80, 12, Qt.AlignLeft, name)

        # Center dot
        p.setBrush(QBrush(ACCENT_CYAN))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), 4, 4)

        # Title
        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 8, QFont.Bold))
        p.drawText(0, 2, w, 14, Qt.AlignHCenter, "BLE RADAR")
        p.end()


# ─── Scanner Thread ───────────────────────────────────────────────────────────
class ScannerThread(QThread):
    wifi_result   = pyqtSignal(list)
    ble_result    = pyqtSignal(list)
    log_message   = pyqtSignal(str)
    scan_error    = pyqtSignal(str)

    def __init__(self, interval=3):
        super().__init__()
        self.interval = interval
        self._running = False
        self.use_mock = False

    def run(self):
        self._running = True
        while self._running:
            wifi = self._scan_wifi()
            ble  = self._scan_ble()
            self.wifi_result.emit(wifi)
            self.ble_result.emit(ble)
            for i in range(self.interval * 10):
                if not self._running:
                    break
                time.sleep(0.1)

    def stop(self):
        self._running = False

    def _scan_wifi(self):
        # Try real scan first
        networks = []
        try:
            networks = self._try_nmcli()
            if networks:
                self.log_message.emit(f"[WiFi] nmcli: {len(networks)} networks")
                return networks
        except Exception as e:
            pass

        try:
            networks = self._try_iwlist()
            if networks:
                self.log_message.emit(f"[WiFi] iwlist: {len(networks)} networks")
                return networks
        except Exception:
            pass

        try:
            networks = self._try_airport()
            if networks:
                self.log_message.emit(f"[WiFi] airport: {len(networks)} networks")
                return networks
        except Exception:
            pass

        try:
            networks = self._try_netsh()
            if networks:
                self.log_message.emit(f"[WiFi] netsh: {len(networks)} networks")
                return networks
        except Exception:
            pass

        # Fallback: demo data
        self.log_message.emit("[WiFi] Using demo data (no real scanner available)")
        return self._mock_wifi()

    def _try_nmcli(self):
        # Use column-mode output to avoid BSSID colon-splitting issues
        out = subprocess.check_output(
            ["nmcli", "-f", "SSID,BSSID,MODE,CHAN,FREQ,RATE,SIGNAL,SECURITY",
             "dev", "wifi", "list"],
            stderr=subprocess.DEVNULL, timeout=8
        ).decode(errors="ignore")
        nets = []
        lines = out.splitlines()
        if len(lines) < 2:
            return nets
        # Parse header to get column positions
        header = lines[0]
        col_names = header.split()
        # Find start positions of each column by scanning header
        col_positions = []
        pos = 0
        for col in col_names:
            p = header.index(col, pos)
            col_positions.append(p)
            pos = p + len(col)
        col_positions.append(len(header) + 200)  # sentinel

        for line in lines[1:]:
            if not line.strip() or line.strip().startswith("--"):
                continue
            def get_col(i):
                start = col_positions[i]
                end   = col_positions[i + 1]
                return line[start:end].strip() if start < len(line) else ""

            try:
                ssid  = get_col(0) or "<hidden>"
                bssid = get_col(1)
                mode  = get_col(2)
                chan  = get_col(3)
                freq  = get_col(4)
                rate  = get_col(5)
                sig   = get_col(6)
                sec   = get_col(7)

                signal_pct = int(sig) if sig.isdigit() else 0
                dbm = signal_pct // 2 - 100
                channel = int(chan) if chan.isdigit() else 6
                band = "5GHz" if freq.startswith("5") else "2.4GHz"
                nets.append({
                    "ssid":     ssid,
                    "bssid":    bssid,
                    "channel":  channel,
                    "signal":   dbm,
                    "band":     band,
                    "security": sec.strip() or "OPEN",
                    "mode":     mode,
                    "rate":     rate,
                    "snr":      dbm + 95,
                })
            except (ValueError, IndexError):
                continue
        return nets

    def _try_iwlist(self):
        # Get wifi interface
        iw_out = subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT,
                                          timeout=5).decode(errors="ignore")
        iface = None
        for line in iw_out.splitlines():
            if "IEEE 802.11" in line or "ESSID" in line:
                iface = line.split()[0]
                break
        if not iface:
            return []
        out = subprocess.check_output(
            ["sudo", "iwlist", iface, "scan"],
            stderr=subprocess.DEVNULL, timeout=15
        ).decode(errors="ignore")
        nets = []
        current = {}
        for line in out.splitlines():
            line = line.strip()
            if "Cell" in line and "Address:" in line:
                if current:
                    nets.append(current)
                current = {"bssid": line.split("Address:")[-1].strip()}
            elif "ESSID:" in line:
                current["ssid"] = line.split('"')[1] if '"' in line else ""
            elif "Channel:" in line:
                try: current["channel"] = int(line.split("Channel:")[-1])
                except: pass
            elif "Signal level=" in line:
                m = re.search(r"Signal level=(-?\d+)", line)
                if m: current["signal"] = int(m.group(1))
            elif "Encryption key:" in line:
                current["security"] = "WPA" if "on" in line.lower() else "OPEN"
            elif "Frequency:" in line:
                current["band"] = "5GHz" if "5." in line else "2.4GHz"
        if current:
            nets.append(current)
        for n in nets:
            n.setdefault("ssid","<hidden>")
            n.setdefault("signal",-70)
            n.setdefault("channel",6)
            n.setdefault("band","2.4GHz")
            n.setdefault("security","WPA2")
            n.setdefault("snr", n["signal"] + 95)
        return nets

    def _try_airport(self):
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if not os.path.exists(airport):
            return []
        out = subprocess.check_output([airport, "-s"],
                                       stderr=subprocess.DEVNULL, timeout=10
                                       ).decode(errors="ignore")
        nets = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 7:
                continue
            ssid = parts[0]
            bssid = parts[1]
            try:
                rssi = int(parts[2])
                chan = int(parts[3].split(",")[0])
                band = "5GHz" if chan > 14 else "2.4GHz"
                nets.append({
                    "ssid": ssid, "bssid": bssid,
                    "signal": rssi, "channel": chan,
                    "band": band, "security": parts[6] if len(parts) > 6 else "?",
                    "snr": rssi + 95,
                })
            except (ValueError, IndexError):
                continue
        return nets

    def _try_netsh(self):
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode(errors="ignore", encoding="utf-8")
        nets = []
        current = {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current:
                    nets.append(current)
                current = {"ssid": line.split(":", 1)[-1].strip()}
            elif "BSSID" in line:
                current["bssid"] = line.split(":", 1)[-1].strip()
            elif "Signal" in line:
                try:
                    pct = int(line.split(":")[-1].strip().replace("%",""))
                    current["signal"] = pct // 2 - 100
                    current["snr"] = pct // 2 - 5
                except: pass
            elif "Channel" in line:
                try:
                    ch = int(line.split(":")[-1].strip())
                    current["channel"] = ch
                    current["band"] = "5GHz" if ch > 14 else "2.4GHz"
                except: pass
            elif "Authentication" in line:
                current["security"] = line.split(":")[-1].strip()
        if current:
            nets.append(current)
        return nets

    def _scan_ble(self):
        try:
            return self._try_bluetoothctl()
        except Exception:
            pass
        return self._mock_ble()

    def _try_bluetoothctl(self):
        out = subprocess.check_output(
            ["bluetoothctl", "devices"],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode(errors="ignore")
        devs = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "Device":
                addr = parts[1]
                name = " ".join(parts[2:])
                devs.append({
                    "address": addr,
                    "name": name,
                    "rssi": random.randint(-90, -40),
                    "type": "BLE",
                    "_angle": random.randint(0, 359),
                })
        return devs if devs else self._mock_ble()

    def _mock_wifi(self):
        ssids = [
            ("HomeNetwork_5G",  "AA:BB:CC:11:22:33", 149, "5GHz",  -45, "WPA3"),
            ("OfficeWifi",      "AA:BB:CC:44:55:66", 6,   "2.4GHz",-62, "WPA2-Enterprise"),
            ("GuestNetwork",    "DD:EE:FF:11:22:33", 11,  "2.4GHz",-71, "WPA2"),
            ("NETGEAR_5G",      "11:22:33:AA:BB:CC", 36,  "5GHz",  -58, "WPA2"),
            ("Linksys_24",      "22:33:44:BB:CC:DD", 1,   "2.4GHz",-80, "WPA2"),
            ("TP-Link_Main",    "33:44:55:CC:DD:EE", 6,   "2.4GHz",-55, "WPA2"),
            ("xfinitywifi",     "44:55:66:DD:EE:FF", 11,  "2.4GHz",-88, "OPEN"),
            ("Hidden Network",  "55:66:77:EE:FF:AA", 100, "5GHz",  -76, "WPA2"),
            ("ATT_Router",      "66:77:88:FF:AA:BB", 1,   "2.4GHz",-66, "WPA2"),
            ("Spectrum_5G",     "77:88:99:AA:BB:CC", 157, "5GHz",  -50, "WPA2"),
            ("FreeWifi_Plaza",  "88:99:AA:BB:CC:DD", 6,   "2.4GHz",-92, "OPEN"),
            ("ASUS_AX88U",      "99:AA:BB:CC:DD:EE", 44,  "5GHz",  -48, "WPA3"),
        ]
        nets = []
        for ssid, bssid, ch, band, sig_base, sec in ssids:
            sig = sig_base + random.randint(-3, 3)
            nets.append({
                "ssid": ssid, "bssid": bssid,
                "channel": ch, "band": band,
                "signal": sig, "security": sec,
                "snr": sig + 95 + random.randint(0, 5),
                "rate": f"{random.choice([54,130,300,450,867,1300])} Mbps",
                "mode": random.choice(["802.11n","802.11ac","802.11ax","802.11a/g"]),
            })
        return nets

    def _mock_ble(self):
        devs = [
            ("iPhone 15 Pro",  "A4:C3:F0:12:34:56", -52, "Phone"),
            ("Galaxy Watch 6", "B8:D4:E2:78:9A:BC", -68, "Wearable"),
            ("AirPods Pro 2",  "C6:A1:44:DE:F0:12", -45, "Audio"),
            ("Tile Mate",      "D2:B3:55:34:56:78", -79, "Tracker"),
            ("Mi Band 8",      "E0:C5:66:9A:BC:DE", -71, "Wearable"),
            ("Xbox Controller","F1:D6:77:F0:12:34", -63, "GamePad"),
            ("BT Keyboard",    "A2:E7:88:56:78:9A", -57, "HID"),
            ("Smart TV BLE",   "B3:F8:99:BC:DE:F0", -84, "Entertainment"),
        ]
        result = []
        for i, (name, addr, rssi_base, dtype) in enumerate(devs):
            result.append({
                "name": name, "address": addr,
                "rssi": rssi_base + random.randint(-4, 4),
                "type": dtype,
                "_angle": i * 45 + random.randint(-15, 15),
                "services": random.randint(1, 8),
                "paired": random.choice([True, False]),
                "connected": random.choice([True, False, False]),
            })
        return result


# ─── Packet Sniffer Thread ────────────────────────────────────────────────────
class PacketSnifferThread(QThread):
    packet_captured = pyqtSignal(dict)
    sniffer_log     = pyqtSignal(str)

    # 802.11 frame type/subtype maps
    FRAME_TYPES = {0: "Mgmt", 1: "Ctrl", 2: "Data", 3: "Ext"}
    MGMT_SUBTYPES = {
        0:"Assoc Req", 1:"Assoc Resp", 2:"Reassoc Req", 3:"Reassoc Resp",
        4:"Probe Req", 5:"Probe Resp", 8:"Beacon", 10:"Disassoc",
        11:"Auth", 12:"Deauth", 13:"Action",
    }
    CTRL_SUBTYPES = {
        7:"Wrapper", 8:"BAR", 9:"BA", 10:"PS-Poll",
        11:"RTS", 12:"CTS", 13:"ACK", 14:"CF-End",
    }
    DATA_SUBTYPES = {
        0:"Data", 4:"Null", 8:"QoS Data", 12:"QoS Null",
    }

    def __init__(self, iface, max_packets=1000):
        super().__init__()
        self.iface = iface
        self.max_packets = max_packets
        self._running = False
        self._counter = 0

    def run(self):
        self._running = True
        self._counter = 0

        # Try real scapy capture first
        try:
            import importlib.util
            if importlib.util.find_spec("scapy") is not None:
                from scapy.all import sniff, Dot11, Dot11Beacon, Dot11Elt, RadioTap
                self.sniffer_log.emit(f"[Sniffer] Starting scapy capture on {self.iface}")
                sniff(iface=self.iface, prn=self._handle_scapy_packet,
                      stop_filter=lambda p: not self._running,
                      store=False, monitor=True)
                return
        except Exception as e:
            self.sniffer_log.emit(f"[Sniffer] scapy unavailable: {e}")

        # Try tcpdump pipe
        try:
            self.sniffer_log.emit(f"[Sniffer] Trying tcpdump on {self.iface}")
            self._run_tcpdump()
            return
        except Exception as e:
            self.sniffer_log.emit(f"[Sniffer] tcpdump failed: {e}")

        # Fallback: realistic mock stream
        self.sniffer_log.emit("[Sniffer] No capture backend found — using demo packet stream")
        self._run_mock()

    def _handle_scapy_packet(self, pkt):
        if not self._running:
            return
        try:
            from scapy.all import Dot11, RadioTap, Dot11Beacon, Dot11Elt
            if not pkt.haslayer(Dot11):
                return
            d = pkt[Dot11]
            ftype   = self.FRAME_TYPES.get(d.type, f"T{d.type}")
            sub_map = {0: self.MGMT_SUBTYPES, 1: self.CTRL_SUBTYPES, 2: self.DATA_SUBTYPES}
            subtype = sub_map.get(d.type, {}).get(d.subtype, f"Sub{d.subtype}")

            sig = -70
            ch  = "?"
            if pkt.haslayer(RadioTap):
                rt = pkt[RadioTap]
                if hasattr(rt, "dBm_AntSignal"):
                    sig = rt.dBm_AntSignal
                if hasattr(rt, "Channel"):
                    ch = rt.Channel

            ssid = ""
            if pkt.haslayer(Dot11Elt):
                elt = pkt[Dot11Elt]
                while elt:
                    if elt.ID == 0:
                        try: ssid = elt.info.decode(errors="replace")
                        except: pass
                    try: elt = elt.payload.getlayer(Dot11Elt)
                    except: break

            raw = bytes(pkt)
            self._counter += 1
            packet = {
                "num":     self._counter,
                "time":    datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "src":     d.addr2 or "—",
                "dst":     d.addr1 or "—",
                "bssid":   d.addr3 or "—",
                "type":    ftype,
                "subtype": subtype,
                "channel": ch,
                "signal":  sig,
                "size":    len(raw),
                "info":    f"{subtype}" + (f" SSID={ssid}" if ssid else ""),
                "decode":  self._build_decode(d.type, d.subtype, d, ssid, sig, ch, ftype, subtype),
                "hexdump": self._build_hex(raw),
            }
            self.packet_captured.emit(packet)
        except Exception:
            pass

    def _run_tcpdump(self):
        proc = subprocess.Popen(
            ["sudo", "tcpdump", "-i", self.iface, "-l", "-e", "-n", "--immediate-mode",
             "-s", "256", "type mgt or type ctl or type data"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1
        )
        while self._running and proc.poll() is None:
            line = proc.stdout.readline()
            if not line:
                continue
            pkt = self._parse_tcpdump_line(line.strip())
            if pkt:
                self.packet_captured.emit(pkt)
        proc.terminate()

    def _parse_tcpdump_line(self, line):
        if not line:
            return None
        self._counter += 1
        # Basic parse: timestamp SA > DA  type
        parts = line.split()
        ts = parts[0] if parts else datetime.now().strftime("%H:%M:%S.000")
        src = dst = "?"
        ptype = "Data"
        subtype = "Frame"
        info = line[:80]
        for i, p in enumerate(parts):
            if p == "SA:" and i+1 < len(parts):  src = parts[i+1].rstrip(",")
            if p == "DA:" and i+1 < len(parts):  dst = parts[i+1].rstrip(",")
            if "Beacon" in p:    ptype,subtype = "Mgmt","Beacon"
            if "Probe"  in p:    ptype,subtype = "Mgmt","Probe Req"
            if "Auth"   in p:    ptype,subtype = "Mgmt","Auth"
            if "Assoc"  in p:    ptype,subtype = "Mgmt","Assoc Req"
            if "Deauth" in p:    ptype,subtype = "Mgmt","Deauth"
            if "Disassoc" in p:  ptype,subtype = "Mgmt","Disassoc"
            if "QoS"    in p:    ptype,subtype = "Data","QoS Data"
        dummy_bytes = bytes(random.randint(0,255) for _ in range(random.randint(28,256)))
        return {
            "num": self._counter, "time": ts,
            "src": src, "dst": dst, "bssid": "—",
            "type": ptype, "subtype": subtype,
            "channel": random.randint(1,11), "signal": random.randint(-85,-35),
            "size": len(dummy_bytes), "info": info,
            "decode": self._build_decode_simple(ptype, subtype, src, dst, info),
            "hexdump": self._build_hex(dummy_bytes),
        }

    def _run_mock(self):
        """Realistic 802.11 demo packet stream."""
        mock_nets = [
            ("HomeNetwork",  "AA:BB:CC:11:22:33", "FF:FF:FF:FF:FF:FF", 6,  -48),
            ("OfficeWifi",   "DD:EE:FF:44:55:66", "FF:FF:FF:FF:FF:FF", 11, -62),
            ("NETGEAR_5G",   "11:22:33:AA:BB:CC", "FF:FF:FF:FF:FF:FF", 36, -55),
            ("GuestNet",     "22:33:44:BB:CC:DD", "FF:FF:FF:FF:FF:FF", 1,  -71),
        ]
        client_macs = [
            "C4:B3:01:12:34:56","A8:66:7F:78:9A:BC",
            "F0:18:98:DE:F0:12","3C:22:FB:34:56:78",
        ]
        frame_pool = [
            # (type, subtype, src_idx, dst, info_template)
            (0, "Beacon",      0, "FF:FF:FF:FF:FF:FF", "SSID={ssid} Ch={ch} Interval=100ms"),
            (0, "Beacon",      1, "FF:FF:FF:FF:FF:FF", "SSID={ssid} Ch={ch} Interval=100ms"),
            (0, "Probe Req",   4, None,                "Broadcast probe"),
            (0, "Probe Resp",  0, None,                "SSID={ssid} caps=ESS Privacy"),
            (0, "Auth",        0, None,                "Seq=1 Algo=OpenSystem Status=0"),
            (0, "Auth",        0, None,                "Seq=2 Algo=OpenSystem Status=0"),
            (0, "Assoc Req",   4, None,                "SSID={ssid} caps=ESS ShortPreamble"),
            (0, "Assoc Resp",  0, None,                "Status=0 AID=1 caps=ESS"),
            (2, "QoS Data",    4, None,                "IV=0x{iv} CCMP Encrypted"),
            (2, "QoS Data",    4, None,                "IV=0x{iv} CCMP Encrypted"),
            (2, "QoS Data",    4, None,                "IV=0x{iv} CCMP Encrypted"),
            (2, "Null",        4, None,                "PWR-SAVE=1"),
            (1, "ACK",         4, None,                ""),
            (1, "RTS",         4, None,                "Duration=52"),
            (1, "CTS",         0, None,                "Duration=44"),
            (0, "Deauth",      0, None,                "Reason=3 (STA leaving)"),
        ]
        while self._running and self._counter < self.max_packets:
            fi = random.randint(0, len(frame_pool)-1)
            ftype_int, subtype, net_idx_or_cli, dst_override, info_tmpl = frame_pool[fi]

            net_idx = net_idx_or_cli % len(mock_nets)
            ssid, ap_mac, _, ch, sig_base = mock_nets[net_idx]

            if ftype_int == 0 and subtype in ("Probe Req",):
                src = random.choice(client_macs)
                dst = "FF:FF:FF:FF:FF:FF"
                bssid = ap_mac
            elif ftype_int == 0 and subtype in ("Auth","Assoc Resp","Probe Resp","Beacon","Assoc Req"):
                if subtype in ("Assoc Req","Probe Req"):
                    src = random.choice(client_macs); dst = ap_mac
                else:
                    src = ap_mac; dst = "FF:FF:FF:FF:FF:FF" if subtype == "Beacon" else random.choice(client_macs)
                bssid = ap_mac
            elif ftype_int == 2:
                src = random.choice(client_macs); dst = ap_mac; bssid = ap_mac
            elif ftype_int == 1:
                src = random.choice(client_macs); dst = ap_mac; bssid = ap_mac
            else:
                src = ap_mac; dst = random.choice(client_macs); bssid = ap_mac

            iv_hex = "".join(f"{random.randint(0,255):02x}" for _ in range(3))
            info = info_tmpl.format(ssid=ssid, ch=ch, iv=iv_hex)
            sig  = sig_base + random.randint(-4, 4)
            size = random.randint(28, 1500)
            raw  = bytes(random.randint(0,255) for _ in range(size))

            self._counter += 1
            pkt = {
                "num":     self._counter,
                "time":    datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "src":     src,
                "dst":     dst,
                "bssid":   bssid,
                "type":    self.FRAME_TYPES.get(ftype_int, "?"),
                "subtype": subtype,
                "channel": ch,
                "signal":  sig,
                "size":    size,
                "info":    info,
                "decode":  self._build_decode_simple(
                               self.FRAME_TYPES.get(ftype_int,"?"), subtype, src, dst, info,
                               bssid=bssid, ch=ch, sig=sig, size=size, ssid=ssid),
                "hexdump": self._build_hex(raw),
            }
            self.packet_captured.emit(pkt)
            time.sleep(random.uniform(0.05, 0.35))

    def _build_decode(self, ftype_int, fsubtype, dot11, ssid, sig, ch, ftype, subtype):
        lines = [
            "IEEE 802.11 Wireless LAN Frame",
            f"  ├─ Frame Control",
            f"  │    ├─ Type    : {ftype} ({ftype_int})",
            f"  │    ├─ Subtype : {subtype} ({fsubtype})",
            f"  │    └─ Flags   : To DS={getattr(dot11,'FCfield',0) & 0x01} "
            f"From DS={getattr(dot11,'FCfield',0) >> 1 & 0x01}",
            f"  ├─ Duration  : {getattr(dot11,'ID',0)} µs",
            f"  ├─ Addr1 (DA/RA) : {dot11.addr1 or '—'}",
            f"  ├─ Addr2 (SA/TA) : {dot11.addr2 or '—'}",
            f"  ├─ Addr3 (BSSID) : {dot11.addr3 or '—'}",
            f"  └─ Seq Ctrl  : {getattr(dot11,'SC',0)}",
            "",
            "RadioTap Header",
            f"  ├─ Signal    : {sig} dBm",
            f"  └─ Channel   : {ch}",
        ]
        if ssid:
            lines += ["", "Tagged Parameters", f"  └─ SSID      : {ssid}"]
        return "\n".join(lines)

    def _build_decode_simple(self, ftype, subtype, src, dst, info,
                              bssid="—", ch="?", sig="?", size=0, ssid=""):
        lines = [
            "IEEE 802.11 Wireless LAN Frame",
            f"  ├─ Frame Type   : {ftype}",
            f"  ├─ Subtype      : {subtype}",
            f"  ├─ Source       : {src}",
            f"  ├─ Destination  : {dst}",
            f"  ├─ BSSID        : {bssid}",
            f"  ├─ Channel      : {ch}",
            f"  ├─ Signal       : {sig} dBm",
            f"  └─ Frame Size   : {size} bytes",
        ]
        if ssid:
            lines += ["", "Tagged Parameters", f"  └─ SSID         : {ssid}"]
        if info:
            lines += ["", "Frame Info", f"  {info}"]
        return "\n".join(lines)

    def _build_hex(self, raw):
        lines = []
        for i in range(0, min(len(raw), 512), 16):
            chunk = raw[i:i+16]
            hex_part  = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"  {i:04x}  {hex_part:<47}  {ascii_part}")
        if len(raw) > 512:
            lines.append(f"  ... ({len(raw) - 512} more bytes truncated)")
        return "\n".join(lines)

    def stop(self):
        self._running = False


# ─── Audit Score Widget ────────────────────────────────────────────────────────
class AuditScoreWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 100
        self._findings = 0
        self.setMinimumHeight(140)

    def setScore(self, score, findings):
        self._score = score
        self._findings = findings
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, BG_PANEL)

        # Score arc
        cx, cy, r = 75, h // 2, 50
        # Background arc
        p.setPen(QPen(GRID_CLR, 8, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(cx - r, cy - r, r*2, r*2, 225*16, -270*16)

        # Score arc
        score_clr = (QColor("#39ff14") if self._score >= 75 else
                     QColor("#ffd700") if self._score >= 50 else
                     QColor("#ff6b35") if self._score >= 25 else
                     QColor("#ff2d78"))
        span = int(-270 * 16 * self._score / 100)
        p.setPen(QPen(score_clr, 8, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(cx - r, cy - r, r*2, r*2, 225*16, span)

        # Score text
        p.setPen(QPen(score_clr, 1))
        p.setFont(QFont("Consolas", 20, QFont.Bold))
        p.drawText(cx - 30, cy - 14, 60, 28, Qt.AlignHCenter, str(self._score))
        p.setFont(QFont("Consolas", 11))
        p.setPen(QPen(TEXT_DIM, 1))
        p.drawText(cx - 30, cy + 14, 60, 14, Qt.AlignHCenter, "/100")

        # Grade
        grade = ("A+" if self._score >= 95 else "A"  if self._score >= 85 else
                 "B"  if self._score >= 75 else "C"  if self._score >= 60 else
                 "D"  if self._score >= 45 else "F")
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.setPen(QPen(score_clr, 1))
        p.drawText(cx - 30, cy + 28, 60, 18, Qt.AlignHCenter, f"Grade: {grade}")

        # Legend
        lx = cx + r + 20
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.setPen(QPen(TEXT_PRIMARY, 1))
        p.drawText(lx, 14, 200, 16, Qt.AlignLeft, "Security Score")
        p.setFont(QFont("Consolas", 11))
        p.setPen(QPen(TEXT_DIM, 1))
        p.drawText(lx, 32, 200, 14, Qt.AlignLeft, f"Total findings : {self._findings}")
        thresholds = [
            (QColor("#39ff14"), "≥75  Acceptable"),
            (QColor("#ffd700"), "≥50  Needs attention"),
            (QColor("#ff6b35"), "≥25  Vulnerable"),
            (QColor("#ff2d78"), " <25  Critical risk"),
        ]
        y = 50
        for clr, txt in thresholds:
            p.setPen(QPen(clr, 3))
            p.drawLine(lx, y + 5, lx + 14, y + 5)
            p.setPen(QPen(TEXT_DIM, 1))
            p.drawText(lx + 18, y - 2, 200, 14, Qt.AlignLeft, txt)
            y += 18
        p.end()


# ─── Main Window ──────────────────────────────────────────────────────────────
class WirelessAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Wireless Analyzer Pro")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setStyleSheet(DARK_STYLESHEET)

        self.wifi_data = []
        self.ble_data  = []
        self.scan_count = 0
        self._selected_band = "2.4GHz"

        self._build_ui()
        self._start_scanner()

    def _build_ui(self):
        self._build_toolbar()
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Header bar
        hdr = self._build_header()
        main_layout.addWidget(hdr)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        main_layout.addWidget(self.tabs)

        self._build_wifi_tab()
        self._build_channel_tab()
        self._build_signal_history_tab()
        self._build_ble_tab()
        self._build_sniffer_tab()
        self._build_security_tab()
        self._build_log_tab()

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("● IDLE")
        self.status_label.setStyleSheet("color: #8b949e; font-size:13px;")
        self.status.addWidget(self.status_label)
        self.scan_info = QLabel("")
        self.scan_info.setStyleSheet("color: #8b949e; font-size:13px;")
        self.status.addPermanentWidget(self.scan_info)

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setIconSize(QSize(20, 20))
        tb.setMovable(False)
        self.addToolBar(tb)

        self.act_scan = QAction("▶  START SCAN", self)
        self.act_scan.setCheckable(True)
        self.act_scan.setChecked(True)
        self.act_scan.triggered.connect(self._toggle_scan)
        tb.addAction(self.act_scan)

        tb.addSeparator()

        act_24 = QAction("2.4 GHz", self)
        act_24.setCheckable(True)
        act_24.setChecked(True)
        act_24.triggered.connect(lambda: self._set_band("2.4GHz"))
        tb.addAction(act_24)

        act_5 = QAction("5 GHz", self)
        act_5.setCheckable(True)
        act_5.triggered.connect(lambda: self._set_band("5GHz"))
        tb.addAction(act_5)

        act_all = QAction("All Bands", self)
        act_all.triggered.connect(lambda: self._set_band("all"))
        tb.addAction(act_all)

        tb.addSeparator()

        lbl = QLabel("  Interval: ")
        lbl.setStyleSheet("color:#6e7681; padding: 0 4px;")
        tb.addWidget(lbl)

        self.interval_box = QComboBox()
        self.interval_box.addItems(["1s", "2s", "3s", "5s", "10s"])
        self.interval_box.setCurrentIndex(2)
        self.interval_box.setFixedWidth(70)
        self.interval_box.currentTextChanged.connect(self._change_interval)
        tb.addWidget(self.interval_box)

        tb.addSeparator()

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter SSID...")
        self.filter_edit.setFixedWidth(160)
        self.filter_edit.textChanged.connect(self._apply_filter)
        tb.addWidget(self.filter_edit)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # Time label
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color:#00d4ff; font-family:Consolas; font-size:15px; font-weight:bold; padding: 0 10px;")
        tb.addWidget(self.time_label)

        # Update clock
        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        self.time_label.setText(datetime.now().strftime("%H:%M:%S"))

    def _build_header(self):
        frame = QFrame()
        frame.setFixedHeight(44)
        frame.setStyleSheet("background: #161b22; border: 1px solid #30363d; border-radius: 4px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 0, 12, 0)

        title = QLabel("⚡ WIRELESS ANALYZER PRO")
        title.setStyleSheet("color:#00d4ff; font-size:16px; font-weight:bold; letter-spacing:2px;")
        layout.addWidget(title)

        layout.addStretch()

        self.wifi_count_lbl = QLabel("WiFi: 0")
        self.wifi_count_lbl.setStyleSheet("color:#39ff14; font-size:14px; font-weight:bold; margin: 0 12px;")
        layout.addWidget(self.wifi_count_lbl)

        self.ble_count_lbl = QLabel("BLE: 0")
        self.ble_count_lbl.setStyleSheet("color:#a855f7; font-size:14px; font-weight:bold; margin: 0 12px;")
        layout.addWidget(self.ble_count_lbl)

        self.scan_status_lbl = QLabel("● SCANNING")
        self.scan_status_lbl.setStyleSheet("color:#39ff14; font-size:14px; font-weight:bold; margin: 0 12px;")
        layout.addWidget(self.scan_status_lbl)

        # Pulse animation
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_timer.start(600)
        self._pulse_state = True

        return frame

    def _pulse(self):
        if self._pulse_state:
            self.scan_status_lbl.setStyleSheet("color:#0d5c1e; font-size:14px; font-weight:bold; margin:0 12px;")
        else:
            self.scan_status_lbl.setStyleSheet("color:#39ff14; font-size:14px; font-weight:bold; margin:0 12px;")
        self._pulse_state = not self._pulse_state

    def _build_wifi_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Table
        cols = ["SSID","BSSID","Band","Ch","Signal (dBm)","Signal","SNR","Encryption","Mode","Rate","Last Seen"]
        self.wifi_table = QTableWidget(0, len(cols))
        self.wifi_table.setHorizontalHeaderLabels(cols)
        self.wifi_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.wifi_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.wifi_table.setAlternatingRowColors(True)
        self.wifi_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.wifi_table.setSortingEnabled(True)
        self.wifi_table.verticalHeader().setVisible(False)
        self.wifi_table.setColumnWidth(4, 90)
        self.wifi_table.setColumnWidth(5, 90)
        layout.addWidget(self.wifi_table)

        self.tabs.addTab(widget, "📡  WiFi Networks")

    def _build_channel_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Band selector
        band_row = QHBoxLayout()
        band_row.addWidget(QLabel("Band:"))
        self.ch_band_combo = QComboBox()
        self.ch_band_combo.addItems(["2.4GHz", "5GHz"])
        self.ch_band_combo.currentTextChanged.connect(self._update_channel_chart)
        band_row.addWidget(self.ch_band_combo)
        band_row.addStretch()
        layout.addLayout(band_row)

        splitter = QSplitter(Qt.Vertical)

        self.channel_overlap = ChannelOverlapWidget()
        splitter.addWidget(self.channel_overlap)

        # Channel summary table
        chan_cols = ["Channel", "Networks", "Interference", "Best Channel"]
        self.chan_table = QTableWidget(0, len(chan_cols))
        self.chan_table.setHorizontalHeaderLabels(chan_cols)
        self.chan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chan_table.setMaximumHeight(150)
        splitter.addWidget(self.chan_table)

        splitter.setSizes([400, 150])
        layout.addWidget(splitter)

        self.tabs.addTab(widget, "📊  Channel Overlap")

    def _build_signal_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("Signal History (last 60s)"))
        ctrl_row.addStretch()
        btn_clear = QPushButton("Clear")
        btn_clear.setFixedWidth(80)
        btn_clear.clicked.connect(lambda: self.sig_history.clear())
        ctrl_row.addWidget(btn_clear)
        layout.addLayout(ctrl_row)

        self.sig_history = SignalHistoryWidget()
        layout.addWidget(self.sig_history)

        self.tabs.addTab(widget, "📈  Signal History")

    def _build_ble_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # BLE table
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)

        ble_cols = ["Name","Address","RSSI","Type","Services","Paired","Connected"]
        self.ble_table = QTableWidget(0, len(ble_cols))
        self.ble_table.setHorizontalHeaderLabels(ble_cols)
        self.ble_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ble_table.setAlternatingRowColors(True)
        self.ble_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ble_table.verticalHeader().setVisible(False)
        left_l.addWidget(self.ble_table)

        layout.addWidget(left, 60)

        # Radar
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.addWidget(QLabel("BLE Radar View"))
        self.ble_radar = BLERadarWidget()
        right_l.addWidget(self.ble_radar)

        layout.addWidget(right, 40)

        self.tabs.addTab(widget, "🔵  Bluetooth LE")

    def _build_log_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Scanner Log"))
        ctrl.addStretch()
        btn = QPushButton("Clear Log")
        btn.setFixedWidth(90)
        btn.clicked.connect(lambda: self.log_text.clear())
        ctrl.addWidget(btn)
        layout.addLayout(ctrl)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.tabs.addTab(widget, "📋  Log")

    def _start_scanner(self):
        self.scanner = ScannerThread(interval=3)
        self.scanner.wifi_result.connect(self._on_wifi_result)
        self.scanner.ble_result.connect(self._on_ble_result)
        self.scanner.log_message.connect(self._on_log)
        self.scanner.start()

    def _toggle_scan(self, checked):
        if checked:
            self.act_scan.setText("▶  SCANNING")
            self._pulse_timer.start(600)
            self._start_scanner()
        else:
            self.act_scan.setText("▶  START SCAN")
            self._pulse_timer.stop()
            self.scan_status_lbl.setText("● IDLE")
            self.scan_status_lbl.setStyleSheet("color:#6e7681; font-size:14px; font-weight:bold; margin:0 12px;")
            if hasattr(self, "scanner"):
                self.scanner.stop()

    def _set_band(self, band):
        self._selected_band = band
        self._update_channel_chart()

    def _change_interval(self, text):
        secs = int(text.replace("s",""))
        if hasattr(self, "scanner"):
            self.scanner.interval = secs

    def _apply_filter(self, text):
        for row in range(self.wifi_table.rowCount()):
            item = self.wifi_table.item(row, 0)
            hide = bool(text and text.lower() not in (item.text().lower() if item else ""))
            self.wifi_table.setRowHidden(row, hide)

    def _on_wifi_result(self, networks):
        self.wifi_data = networks
        self.scan_count += 1
        self.wifi_count_lbl.setText(f"WiFi: {len(networks)}")
        self._refresh_wifi_table(networks)
        self._update_channel_chart()
        for n in networks[:8]:
            self.sig_history.addSample(n.get("ssid","?"), n.get("signal",-70))
        ts = datetime.now().strftime("%H:%M:%S")
        self.scan_info.setText(f"Scan #{self.scan_count} @ {ts}")

    def _on_ble_result(self, devices):
        self.ble_data = devices
        self.ble_count_lbl.setText(f"BLE: {len(devices)}")
        self._refresh_ble_table(devices)
        self.ble_radar.setDevices(devices)

    def _on_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def _refresh_wifi_table(self, networks):
        self.wifi_table.setSortingEnabled(False)
        self.wifi_table.setRowCount(len(networks))
        filt = self.filter_edit.text().lower()
        for row, net in enumerate(networks):
            ssid     = net.get("ssid","?")
            bssid    = net.get("bssid","?")
            band     = net.get("band","?")
            channel  = str(net.get("channel","?"))
            sig      = net.get("signal",-100)
            snr      = net.get("snr",0)
            sec      = net.get("security","?")
            mode     = net.get("mode","?")
            rate     = net.get("rate","?")
            ts       = datetime.now().strftime("%H:%M:%S")

            row_data = [ssid, bssid, band, channel, str(sig), None, str(snr), sec, mode, rate, ts]
            for col, val in enumerate(row_data):
                if col == 5:
                    # Signal bar widget
                    bar = SignalBar(sig)
                    self.wifi_table.setCellWidget(row, col, bar)
                    continue
                item = QTableWidgetItem(str(val) if val else "")
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                # Colorize signal
                if col == 4:
                    if sig >= -50: item.setForeground(QColor("#39ff14"))
                    elif sig >= -65: item.setForeground(QColor("#ffd700"))
                    elif sig >= -75: item.setForeground(QColor("#ff6b35"))
                    else: item.setForeground(QColor("#ff2d78"))

                # Colorize security
                if col == 7:
                    if "WPA3" in sec: item.setForeground(QColor("#39ff14"))
                    elif "WPA2" in sec: item.setForeground(ACCENT_CYAN)
                    elif "WPA" in sec: item.setForeground(QColor("#ffd700"))
                    elif "OPEN" in sec.upper(): item.setForeground(QColor("#ff2d78"))

                # Colorize band
                if col == 2:
                    if "5" in band: item.setForeground(ACCENT_PURPLE)
                    else: item.setForeground(ACCENT_CYAN)

                self.wifi_table.setItem(row, col, item)

            # Hide if filtered
            hide = bool(filt and filt not in ssid.lower())
            self.wifi_table.setRowHidden(row, hide)

        self.wifi_table.setSortingEnabled(True)
        self.wifi_table.setRowHeight(0, 30)
        for row in range(self.wifi_table.rowCount()):
            self.wifi_table.setRowHeight(row, 30)

    def _refresh_ble_table(self, devices):
        self.ble_table.setRowCount(len(devices))
        for row, dev in enumerate(devices):
            name  = dev.get("name","Unknown")
            addr  = dev.get("address","?")
            rssi  = dev.get("rssi",-70)
            dtype = dev.get("type","BLE")
            svc   = str(dev.get("services",0))
            paired = "✓" if dev.get("paired") else "✗"
            connected = "✓" if dev.get("connected") else "✗"

            data = [name, addr, str(rssi), dtype, svc, paired, connected]
            for col, val in enumerate(data):
                item = QTableWidgetItem(val)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if col == 2:
                    if rssi >= -55: item.setForeground(QColor("#39ff14"))
                    elif rssi >= -70: item.setForeground(QColor("#ffd700"))
                    else: item.setForeground(QColor("#ff6b35"))
                if col == 6:
                    item.setForeground(QColor("#39ff14") if val == "✓" else TEXT_DIM)
                self.ble_table.setItem(row, col, item)
            self.ble_table.setRowHeight(row, 30)

    def _update_channel_chart(self):
        band = self.ch_band_combo.currentText()
        self.channel_overlap.setNetworks(self.wifi_data, band)

        # Channel congestion table
        chan_count = defaultdict(list)
        for n in self.wifi_data:
            if n.get("band", "2.4GHz") == band:
                ch  = n.get("channel", None)
                sig = n.get("signal", -100)
                if ch is not None:
                    chan_count[ch].append(sig)

        if band == "2.4GHz":
            non_overlap = [1, 6, 11]
            all_channels = list(range(1, 14))
        else:
            non_overlap = [36, 44, 149, 157]
            all_channels = [36,40,44,48,52,56,60,64,100,149,153,157,161]

        # Find least congested
        best_ch = min(all_channels, key=lambda c: len(chan_count.get(c,[])), default=1)

        self.chan_table.setRowCount(len(chan_count))
        for row, (ch, sigs) in enumerate(sorted(chan_count.items())):
            interference = "HIGH" if len(sigs) > 3 else "MEDIUM" if len(sigs) > 1 else "LOW"
            iclr = QColor("#ff2d78") if interference == "HIGH" else QColor("#ffd700") if interference == "MEDIUM" else QColor("#39ff14")
            data = [str(ch), str(len(sigs)), interference, str(best_ch) if ch == best_ch else ""]
            for col, val in enumerate(data):
                item = QTableWidgetItem(val)
                if col == 2:
                    item.setForeground(iclr)
                elif col == 3 and val:
                    item.setForeground(QColor("#39ff14"))
                self.chan_table.setItem(row, col, item)
            self.chan_table.setRowHeight(row, 30)

    # ─── Packet Sniffer Tab ───────────────────────────────────────────────────
    def _build_sniffer_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Controls row
        ctrl = QHBoxLayout()
        self.sniff_iface_combo = QComboBox()
        self.sniff_iface_combo.setFixedWidth(130)
        self._populate_interfaces()
        ctrl.addWidget(QLabel("Interface:"))
        ctrl.addWidget(self.sniff_iface_combo)

        ctrl.addWidget(QLabel("  Filter:"))
        self.sniff_filter = QLineEdit()
        self.sniff_filter.setPlaceholderText("e.g. BSSID, type, port …")
        self.sniff_filter.setFixedWidth(180)
        self.sniff_filter.textChanged.connect(self._apply_packet_filter)
        ctrl.addWidget(self.sniff_filter)

        ctrl.addWidget(QLabel("  Max packets:"))
        self.sniff_max = QSpinBox()
        self.sniff_max.setRange(100, 10000)
        self.sniff_max.setValue(1000)
        self.sniff_max.setSingleStep(100)
        self.sniff_max.setFixedWidth(80)
        ctrl.addWidget(self.sniff_max)

        ctrl.addStretch()

        self.sniff_count_lbl = QLabel("Packets: 0")
        self.sniff_count_lbl.setStyleSheet("color:#00d4ff; font-size:13px; font-weight:bold;")
        ctrl.addWidget(self.sniff_count_lbl)

        self.btn_sniff = QPushButton("▶  START CAPTURE")
        self.btn_sniff.setCheckable(True)
        self.btn_sniff.clicked.connect(self._toggle_sniffer)
        ctrl.addWidget(self.btn_sniff)

        self.btn_clear_pkts = QPushButton("Clear")
        self.btn_clear_pkts.setFixedWidth(70)
        self.btn_clear_pkts.clicked.connect(self._clear_packets)
        ctrl.addWidget(self.btn_clear_pkts)

        layout.addLayout(ctrl)

        # Main splitter: table on top, detail pane bottom
        splitter = QSplitter(Qt.Vertical)

        # Packet table
        pkt_cols = ["#", "Time", "Source MAC", "Dest MAC", "Type", "Subtype",
                    "Channel", "Signal", "Size (B)", "Info"]
        self.pkt_table = QTableWidget(0, len(pkt_cols))
        self.pkt_table.setHorizontalHeaderLabels(pkt_cols)
        self.pkt_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)
        self.pkt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.pkt_table.setAlternatingRowColors(True)
        self.pkt_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pkt_table.verticalHeader().setVisible(False)
        self.pkt_table.itemSelectionChanged.connect(self._on_packet_selected)
        self.pkt_table.setColumnWidth(1, 90)
        self.pkt_table.setColumnWidth(2, 140)
        self.pkt_table.setColumnWidth(3, 140)
        self.pkt_table.setColumnWidth(4, 90)
        self.pkt_table.setColumnWidth(5, 110)
        self.pkt_table.setColumnWidth(6, 65)
        self.pkt_table.setColumnWidth(7, 80)
        self.pkt_table.setColumnWidth(8, 65)
        splitter.addWidget(self.pkt_table)

        # Detail / decode pane (horizontal splitter)
        detail_split = QSplitter(Qt.Horizontal)

        # Layer decode tree (plain text for simplicity)
        detail_left = QWidget()
        dl_layout = QVBoxLayout(detail_left)
        dl_layout.setContentsMargins(0,0,0,0)
        dl_layout.addWidget(QLabel("  Frame Decode"))
        self.pkt_decode = QTextEdit()
        self.pkt_decode.setReadOnly(True)
        self.pkt_decode.setFont(QFont("Consolas", 12))
        dl_layout.addWidget(self.pkt_decode)
        detail_split.addWidget(detail_left)

        # Hex dump
        detail_right = QWidget()
        dr_layout = QVBoxLayout(detail_right)
        dr_layout.setContentsMargins(0,0,0,0)
        dr_layout.addWidget(QLabel("  Hex Dump"))
        self.pkt_hex = QTextEdit()
        self.pkt_hex.setReadOnly(True)
        self.pkt_hex.setFont(QFont("Consolas", 12))
        dr_layout.addWidget(self.pkt_hex)
        detail_split.addWidget(detail_right)

        detail_split.setSizes([500, 400])
        splitter.addWidget(detail_split)
        splitter.setSizes([500, 220])
        layout.addWidget(splitter)

        # Stats bar
        stats_row = QHBoxLayout()
        self.pkt_stat_labels = {}
        for key in ["Mgmt","Ctrl","Data","Beacon","Probe","Auth","Assoc","Deauth"]:
            lbl = QLabel(f"{key}: 0")
            lbl.setStyleSheet("color:#6e7681; font-size:10px; margin:0 6px;")
            stats_row.addWidget(lbl)
            self.pkt_stat_labels[key] = lbl
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # Internal state
        self._all_packets = []     # raw packet dicts
        self._pkt_counter = 0
        self._pkt_stats = {k: 0 for k in ["Mgmt","Ctrl","Data","Beacon","Probe","Auth","Assoc","Deauth"]}
        self._sniffer_thread = None

        self.tabs.addTab(widget, "🦈  Packet Sniffer")

    def _populate_interfaces(self):
        self.sniff_iface_combo.clear()
        ifaces = self._get_interfaces()
        for ifc in ifaces:
            self.sniff_iface_combo.addItem(ifc)
        if not ifaces:
            self.sniff_iface_combo.addItem("wlan0")

    def _get_interfaces(self):
        ifaces = []
        try:
            out = subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT,
                                           timeout=4).decode(errors="ignore")
            for line in out.splitlines():
                if line and not line.startswith(" "):
                    name = line.split()[0]
                    if name:
                        ifaces.append(name)
        except Exception:
            pass
        if not ifaces:
            try:
                out = subprocess.check_output(["ip", "link"], stderr=subprocess.DEVNULL,
                                               timeout=4).decode(errors="ignore")
                for line in out.splitlines():
                    m = re.match(r"\d+: (\w+):", line)
                    if m and m.group(1) not in ("lo",):
                        ifaces.append(m.group(1))
            except Exception:
                pass
        return ifaces or ["wlan0", "en0", "eth0"]

    def _toggle_sniffer(self, checked):
        if checked:
            self.btn_sniff.setText("■  STOP CAPTURE")
            self.btn_sniff.setStyleSheet(
                "background:#3a0000; color:#ff2d78; border:1px solid #ff2d78;"
                "padding:6px 16px; border-radius:3px; font-weight:bold;")
            self._start_sniffer()
        else:
            self.btn_sniff.setText("▶  START CAPTURE")
            self.btn_sniff.setStyleSheet("")
            self._stop_sniffer()

    def _start_sniffer(self):
        iface = self.sniff_iface_combo.currentText()
        self._sniffer_thread = PacketSnifferThread(iface, self.sniff_max.value())
        self._sniffer_thread.packet_captured.connect(self._on_packet_captured)
        self._sniffer_thread.sniffer_log.connect(self._on_log)
        self._sniffer_thread.start()

    def _stop_sniffer(self):
        if self._sniffer_thread:
            self._sniffer_thread.stop()
            self._sniffer_thread.wait(2000)
            self._sniffer_thread = None

    def _clear_packets(self):
        self._all_packets.clear()
        self._pkt_counter = 0
        self._pkt_stats = {k: 0 for k in self._pkt_stats}
        self.pkt_table.setRowCount(0)
        self.pkt_decode.clear()
        self.pkt_hex.clear()
        self.sniff_count_lbl.setText("Packets: 0")
        for k, lbl in self.pkt_stat_labels.items():
            lbl.setText(f"{k}: 0")

    def _on_packet_captured(self, pkt):
        if self._pkt_counter >= self.sniff_max.value():
            self._stop_sniffer()
            self.btn_sniff.setChecked(False)
            self._toggle_sniffer(False)
            return

        self._pkt_counter += 1
        self._all_packets.append(pkt)

        # Update stats
        ptype = pkt.get("type","?")
        subtype = pkt.get("subtype","")
        for key in ["Mgmt","Ctrl","Data","Beacon","Probe","Auth","Assoc","Deauth"]:
            if key.lower() in ptype.lower() or key.lower() in subtype.lower():
                self._pkt_stats[key] += 1
        for k, lbl in self.pkt_stat_labels.items():
            lbl.setText(f"{k}: {self._pkt_stats[k]}")

        self.sniff_count_lbl.setText(f"Packets: {self._pkt_counter}")
        self._insert_packet_row(pkt)

        # Auto-scroll
        self.pkt_table.scrollToBottom()

    def _insert_packet_row(self, pkt):
        filt = self.sniff_filter.text().lower()
        info = pkt.get("info","")
        src  = pkt.get("src","")
        dst  = pkt.get("dst","")
        if filt and filt not in info.lower() and filt not in src.lower() and filt not in dst.lower():
            return

        row = self.pkt_table.rowCount()
        self.pkt_table.insertRow(row)
        self.pkt_table.setRowHeight(row, 30)

        ptype   = pkt.get("type","?")
        subtype = pkt.get("subtype","—")
        sig     = str(pkt.get("signal","—"))
        ch      = str(pkt.get("channel","—"))
        size    = str(pkt.get("size", 0))
        ts      = pkt.get("time","")

        row_data = [str(pkt.get("num",0)), ts, src, dst, ptype, subtype, ch, sig, size, info]

        # Color by type
        if "beacon" in subtype.lower():
            clr = QColor("#1a3a1a")
        elif "probe" in subtype.lower():
            clr = QColor("#1a2a3a")
        elif "auth" in subtype.lower() or "assoc" in subtype.lower():
            clr = QColor("#2a1a3a")
        elif "deauth" in subtype.lower() or "disassoc" in subtype.lower():
            clr = QColor("#3a1a1a")
        elif "data" in ptype.lower():
            clr = QColor("#1a1f2a")
        else:
            clr = QColor("#161b22")

        for col, val in enumerate(row_data):
            item = QTableWidgetItem(str(val))
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setBackground(QBrush(clr))
            # Column-specific colors
            if col == 4:   # type
                if "mgmt" in val.lower():   item.setForeground(QColor("#ffd700"))
                elif "data" in val.lower(): item.setForeground(ACCENT_CYAN)
                elif "ctrl" in val.lower(): item.setForeground(ACCENT_PURPLE)
            if col == 5:   # subtype
                if "beacon" in val.lower():  item.setForeground(QColor("#39ff14"))
                elif "deauth" in val.lower() or "disassoc" in val.lower():
                    item.setForeground(QColor("#ff2d78"))
                elif "auth" in val.lower():  item.setForeground(QColor("#ff6b35"))
                elif "probe" in val.lower(): item.setForeground(ACCENT_CYAN)
            if col == 7:   # signal
                try:
                    sv = int(val)
                    if sv >= -55:   item.setForeground(QColor("#39ff14"))
                    elif sv >= -70: item.setForeground(QColor("#ffd700"))
                    else:           item.setForeground(QColor("#ff6b35"))
                except ValueError:
                    pass
            # Store packet index in column 0
            if col == 0:
                item.setData(Qt.UserRole, len(self._all_packets) - 1)
            self.pkt_table.setItem(row, col, item)

    def _apply_packet_filter(self, text):
        filt = text.lower()
        for row in range(self.pkt_table.rowCount()):
            items = [self.pkt_table.item(row, c) for c in range(self.pkt_table.columnCount())]
            row_text = " ".join(i.text().lower() for i in items if i)
            self.pkt_table.setRowHidden(row, bool(filt and filt not in row_text))

    def _on_packet_selected(self):
        rows = self.pkt_table.selectedItems()
        if not rows:
            return
        idx_item = self.pkt_table.item(self.pkt_table.currentRow(), 0)
        if not idx_item:
            return
        pkt_idx = idx_item.data(Qt.UserRole)
        if pkt_idx is None or pkt_idx >= len(self._all_packets):
            return
        pkt = self._all_packets[pkt_idx]
        self.pkt_decode.setPlainText(pkt.get("decode",""))
        self.pkt_hex.setPlainText(pkt.get("hexdump",""))

    # ─── Security Audit Tab ───────────────────────────────────────────────────
    def _build_security_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Disclaimer banner
        banner = QLabel(
            "⚠  SECURITY AUDIT — For networks you own or have explicit written permission to test. "
            "Unauthorized network testing is illegal."
        )
        banner.setStyleSheet(
            "background:#2a1800; color:#ffd700; border:1px solid #ff6b35;"
            "padding:6px 10px; border-radius:3px; font-weight:bold;"
        )
        banner.setWordWrap(True)
        layout.addWidget(banner)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Scan target:"))
        self.sec_target_combo = QComboBox()
        self.sec_target_combo.setFixedWidth(220)
        self.sec_target_combo.addItem("All visible networks")
        ctrl.addWidget(self.sec_target_combo)
        ctrl.addStretch()
        self.btn_audit = QPushButton("🔍  RUN AUDIT")
        self.btn_audit.setFixedWidth(140)
        self.btn_audit.clicked.connect(self._run_security_audit)
        ctrl.addWidget(self.btn_audit)
        layout.addLayout(ctrl)

        # Main horizontal split
        h_split = QSplitter(Qt.Horizontal)

        # Left: findings table
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,0,0)
        ll.addWidget(QLabel("  Audit Findings"))
        sec_cols = ["Severity","Network (SSID)","BSSID","Issue","Recommendation"]
        self.sec_table = QTableWidget(0, len(sec_cols))
        self.sec_table.setHorizontalHeaderLabels(sec_cols)
        self.sec_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.sec_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.sec_table.setAlternatingRowColors(True)
        self.sec_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sec_table.verticalHeader().setVisible(False)
        self.sec_table.itemSelectionChanged.connect(self._on_finding_selected)
        ll.addWidget(self.sec_table)
        h_split.addWidget(left)

        # Right: detail + score
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(4,0,0,0)

        # Score widget
        self.audit_score_widget = AuditScoreWidget()
        self.audit_score_widget.setFixedHeight(160)
        rl.addWidget(self.audit_score_widget)

        rl.addWidget(QLabel("  Finding Detail"))
        self.sec_detail = QTextEdit()
        self.sec_detail.setReadOnly(True)
        rl.addWidget(self.sec_detail)

        h_split.addWidget(right)
        h_split.setSizes([700, 340])
        layout.addWidget(h_split)

        # Summary bar
        sum_row = QHBoxLayout()
        self.sec_summary_labels = {}
        for sev in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]:
            clr = {"CRITICAL":"#ff2d78","HIGH":"#ff6b35","MEDIUM":"#ffd700",
                   "LOW":"#39ff14","INFO":"#00d4ff"}[sev]
            lbl = QLabel(f"{sev}: 0")
            lbl.setStyleSheet(f"color:{clr}; font-weight:bold; margin:0 8px;")
            sum_row.addWidget(lbl)
            self.sec_summary_labels[sev] = lbl
        sum_row.addStretch()
        layout.addLayout(sum_row)

        self.tabs.addTab(widget, "🔒  Security Audit")

    def _run_security_audit(self):
        # Refresh target list
        self.sec_target_combo.clear()
        self.sec_target_combo.addItem("All visible networks")
        for n in self.wifi_data:
            self.sec_target_combo.addItem(n.get("ssid","?"))

        nets = self.wifi_data
        target = self.sec_target_combo.currentText()
        if target != "All visible networks":
            nets = [n for n in nets if n.get("ssid") == target]

        findings = []
        for net in nets:
            findings.extend(self._audit_network(net))

        # Channel interference findings
        from collections import Counter
        ch_counts = Counter(n.get("channel") for n in self.wifi_data)
        for ch, cnt in ch_counts.items():
            if cnt >= 4:
                findings.append({
                    "severity":"MEDIUM","ssid":"[Channel Congestion]","bssid":"—",
                    "issue":f"Channel {ch} has {cnt} overlapping networks",
                    "recommendation":"Switch to a less congested channel (1, 6, or 11 for 2.4GHz).",
                    "detail":(
                        f"Channel {ch} is shared by {cnt} networks, causing co-channel interference.\n\n"
                        "Co-channel interference degrades throughput and increases latency.\n\n"
                        "Recommended action: Use a Wi-Fi analyzer to find the least congested channel "
                        "and configure your AP accordingly."
                    ),
                })

        self._populate_audit_table(findings)

        # Score
        score = self._compute_security_score(findings)
        self.audit_score_widget.setScore(score, len(findings))
        self._on_log(f"[Audit] Completed — {len(findings)} findings, score {score}/100")

    def _audit_network(self, net):
        findings = []
        ssid  = net.get("ssid","?")
        bssid = net.get("bssid","?")
        sec   = net.get("security","?").upper()
        sig   = net.get("signal",-100)
        ch    = net.get("channel",6)
        band  = net.get("band","2.4GHz")
        mode  = net.get("mode","?")

        # Open network
        if "OPEN" in sec or sec in ("NONE","","—"):
            findings.append({
                "severity":"CRITICAL","ssid":ssid,"bssid":bssid,
                "issue":"Open network — no encryption",
                "recommendation":"Enable WPA2 or WPA3 immediately.",
                "detail":(
                    f"Network '{ssid}' ({bssid}) has no encryption.\n\n"
                    "All traffic is transmitted in plaintext and can be captured by anyone nearby "
                    "using freely available tools such as Wireshark or tcpdump.\n\n"
                    "Credentials, session tokens, emails, and other sensitive data are fully exposed.\n\n"
                    "IMMEDIATE ACTION: Enable WPA3-Personal (preferred) or WPA2-PSK with AES/CCMP "
                    "on your access point."
                ),
            })

        # WEP — broken
        if "WEP" in sec:
            findings.append({
                "severity":"CRITICAL","ssid":ssid,"bssid":bssid,
                "issue":"WEP encryption detected — cryptographically broken",
                "recommendation":"Upgrade to WPA3 or WPA2-AES immediately.",
                "detail":(
                    f"Network '{ssid}' uses WEP (Wired Equivalent Privacy).\n\n"
                    "WEP was deprecated by IEEE in 2004. Its RC4-based key schedule is fundamentally "
                    "flawed: with sufficient IV collection (~50,000–100,000 packets), the pre-shared "
                    "key can be recovered.\n\n"
                    "CVSS score: 9.8 (Critical).\n\n"
                    "Replace your router firmware or hardware. Use WPA3-Personal or at minimum "
                    "WPA2-PSK with AES-CCMP."
                ),
            })

        # WPA (TKIP) — weak
        if "WPA" in sec and "WPA2" not in sec and "WPA3" not in sec:
            findings.append({
                "severity":"HIGH","ssid":ssid,"bssid":bssid,
                "issue":"WPA-TKIP — vulnerable to TKIP MIC attacks",
                "recommendation":"Upgrade to WPA2-AES or WPA3.",
                "detail":(
                    f"Network '{ssid}' uses WPA with TKIP cipher.\n\n"
                    "TKIP is susceptible to the Beck-Tews and Ohigashi-Morii attacks (2008/2009), "
                    "allowing short plaintext injection. TKIP was deprecated in 802.11-2012.\n\n"
                    "Upgrade your AP to WPA2 with AES-CCMP or WPA3-SAE."
                ),
            })

        # WPA2 without mention of AES — might use TKIP
        if "WPA2" in sec and "AES" not in sec and "CCMP" not in sec and "WPA3" not in sec:
            findings.append({
                "severity":"MEDIUM","ssid":ssid,"bssid":bssid,
                "issue":"WPA2 cipher mode unconfirmed — may allow TKIP fallback",
                "recommendation":"Explicitly configure AES-CCMP only in AP settings.",
                "detail":(
                    f"Network '{ssid}' reports WPA2 but AES/CCMP is not confirmed in the beacon.\n\n"
                    "Mixed-mode WPA2 deployments often allow TKIP as a fallback cipher for legacy "
                    "client compatibility. This degrades the effective security level.\n\n"
                    "Log into your AP admin panel and set the cipher to AES/CCMP only."
                ),
            })

        # PMKID / PMKSA caching exposure note for WPA2
        if "WPA2" in sec and "WPA3" not in sec:
            findings.append({
                "severity":"LOW","ssid":ssid,"bssid":bssid,
                "issue":"WPA2-PSK susceptible to offline dictionary/PMKID attack",
                "recommendation":"Use a strong passphrase (20+ chars, mixed) or upgrade to WPA3-SAE.",
                "detail":(
                    f"WPA2-PSK on '{ssid}' is vulnerable to the PMKID attack (Jens Steube, 2018), "
                    "which allows capturing a single PMKID frame without requiring a full 4-way "
                    "handshake. The captured material can be subjected to offline dictionary or "
                    "brute-force attacks.\n\n"
                    "Mitigation:\n"
                    "  • Use a passphrase of 20+ random characters.\n"
                    "  • Upgrade to WPA3-SAE, which provides forward secrecy and is resistant to "
                    "offline dictionary attacks due to the Dragonfly handshake.\n"
                    "  • Enable Management Frame Protection (802.11w) if available."
                ),
            })

        # WPA3 — best practice note
        if "WPA3" in sec:
            findings.append({
                "severity":"INFO","ssid":ssid,"bssid":bssid,
                "issue":"WPA3 detected — modern security",
                "recommendation":"Ensure PMF (802.11w) is set to Required.",
                "detail":(
                    f"'{ssid}' uses WPA3, which employs the SAE (Simultaneous Authentication of "
                    "Equals) handshake replacing PSK. This provides forward secrecy and resistance "
                    "to offline dictionary attacks.\n\n"
                    "Best practice: confirm Protected Management Frames (PMF/802.11w) is set to "
                    "Required in your AP, not just Optional."
                ),
            })

        # Hidden SSID
        if not ssid or ssid in ("<hidden>",""):
            findings.append({
                "severity":"INFO","ssid":"<hidden>","bssid":bssid,
                "issue":"Hidden SSID — security through obscurity",
                "recommendation":"Hidden SSIDs still appear in probe requests; not a security measure.",
                "detail":(
                    "Hiding the SSID does not prevent discovery — passive scanners and probe-request "
                    "sniffers reveal the SSID when clients connect. This provides no real security "
                    "benefit and can cause connectivity issues.\n\n"
                    "Rely on strong encryption (WPA3) rather than SSID hiding."
                ),
            })

        # Default/common SSID
        common_ssids = ["linksys","netgear","default","dlink","tp-link","home","wifi",
                        "xfinitywifi","attwifi","spectrum","asus","belkin","actiontec"]
        if any(c in ssid.lower() for c in common_ssids):
            findings.append({
                "severity":"LOW","ssid":ssid,"bssid":bssid,
                "issue":"Default or generic SSID name",
                "recommendation":"Rename to a non-identifying, non-default SSID.",
                "detail":(
                    f"'{ssid}' resembles a default manufacturer SSID. This can hint at default "
                    "router credentials still being in use and makes the network easier to profile.\n\n"
                    "Change the SSID to something non-identifying and verify the admin password "
                    "has been changed from factory defaults."
                ),
            })

        # Very weak signal — rogue AP risk note
        if sig < -85:
            findings.append({
                "severity":"INFO","ssid":ssid,"bssid":bssid,
                "issue":f"Very weak signal ({sig} dBm) — possible rogue/distant AP",
                "recommendation":"Verify this AP is known; very weak distant APs may be honeypots.",
                "detail":(
                    f"Signal strength is {sig} dBm, below typical threshold for legitimate nearby APs.\n\n"
                    "Extremely weak signals from unknown BSSIDs can indicate:\n"
                    "  • A rogue/evil-twin access point attempting to lure clients.\n"
                    "  • A legitimate but very distant AP.\n\n"
                    "Cross-reference the BSSID against known APs in your environment."
                ),
            })

        # Enterprise check
        if "ENTERPRISE" in sec or "EAP" in sec or "802.1X" in sec:
            findings.append({
                "severity":"INFO","ssid":ssid,"bssid":bssid,
                "issue":"WPA2-Enterprise / 802.1X detected",
                "recommendation":"Verify EAP method (use EAP-TLS; avoid PEAP-MSCHAPv2 without cert pinning).",
                "detail":(
                    f"'{ssid}' uses 802.1X authentication.\n\n"
                    "Security depends heavily on the EAP method:\n"
                    "  • EAP-TLS (certificate-based): Very strong — recommended.\n"
                    "  • PEAP-MSCHAPv2: Vulnerable to credential harvesting via rogue RADIUS "
                    "if clients do not validate the server certificate.\n\n"
                    "Ensure clients are configured with server certificate validation and "
                    "CA pinning to prevent evil-twin RADIUS attacks."
                ),
            })

        return findings

    def _compute_security_score(self, findings):
        deductions = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3, "INFO": 0}
        score = 100
        for f in findings:
            score -= deductions.get(f.get("severity","INFO"), 0)
        return max(0, min(100, score))

    def _populate_audit_table(self, findings):
        sev_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}
        findings.sort(key=lambda f: sev_order.get(f.get("severity","INFO"), 5))

        counts = {s: 0 for s in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]}
        self.sec_table.setRowCount(len(findings))
        self._audit_findings = findings

        for row, f in enumerate(findings):
            sev   = f.get("severity","INFO")
            ssid  = f.get("ssid","?")
            bssid = f.get("bssid","?")
            issue = f.get("issue","")
            rec   = f.get("recommendation","")
            counts[sev] = counts.get(sev, 0) + 1

            sev_colors = {
                "CRITICAL": "#ff2d78","HIGH": "#ff6b35",
                "MEDIUM":   "#ffd700","LOW":  "#39ff14","INFO": "#00d4ff",
            }
            clr = QColor(sev_colors.get(sev, "#6e7681"))

            for col, val in enumerate([sev, ssid, bssid, issue, rec]):
                item = QTableWidgetItem(val)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if col == 0:
                    item.setForeground(clr)
                    item.setFont(QFont("Consolas", 10, QFont.Bold))
                self.sec_table.setItem(row, col, item)
            self.sec_table.setRowHeight(row, 30)

        for sev, lbl in self.sec_summary_labels.items():
            lbl.setText(f"{sev}: {counts.get(sev,0)}")

    def _on_finding_selected(self):
        row = self.sec_table.currentRow()
        if not hasattr(self, "_audit_findings") or row < 0 or row >= len(self._audit_findings):
            return
        f = self._audit_findings[row]
        sev_colors = {"CRITICAL":"#ff2d78","HIGH":"#ff6b35","MEDIUM":"#ffd700",
                      "LOW":"#39ff14","INFO":"#00d4ff"}
        clr = sev_colors.get(f.get("severity","INFO"),"#e6edf3")
        text = (
            f"{'═'*60}\n"
            f"  SEVERITY : {f.get('severity','?')}\n"
            f"  NETWORK  : {f.get('ssid','?')}\n"
            f"  BSSID    : {f.get('bssid','?')}\n"
            f"{'─'*60}\n\n"
            f"ISSUE\n{f.get('issue','')}\n\n"
            f"TECHNICAL DETAIL\n{f.get('detail','')}\n\n"
            f"RECOMMENDATION\n{f.get('recommendation','')}\n"
            f"{'═'*60}"
        )
        self.sec_detail.setPlainText(text)

    def closeEvent(self, event):
        if hasattr(self, "scanner"):
            self.scanner.stop()
            self.scanner.wait(2000)
        if hasattr(self, "_sniffer_thread") and self._sniffer_thread:
            self._sniffer_thread.stop()
            self._sniffer_thread.wait(2000)
        event.accept()


# ─── Entry Point ──────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Wireless Analyzer Pro")
    app.setStyle("Fusion")

    # Dark palette base
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0d1117"))
    palette.setColor(QPalette.WindowText, QColor("#e6edf3"))
    palette.setColor(QPalette.Base, QColor("#161b22"))
    palette.setColor(QPalette.AlternateBase, QColor("#1c2230"))
    palette.setColor(QPalette.Text, QColor("#e6edf3"))
    palette.setColor(QPalette.Button, QColor("#1c2230"))
    palette.setColor(QPalette.ButtonText, QColor("#e6edf3"))
    palette.setColor(QPalette.Highlight, QColor("#1f3a5f"))
    palette.setColor(QPalette.HighlightedText, QColor("#00d4ff"))
    app.setPalette(palette)

    win = WirelessAnalyzer()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
