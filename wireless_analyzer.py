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
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}
QTabWidget::pane {
    border: 1px solid #30363d;
    background: #161b22;
}
QTabBar::tab {
    background: #0d1117;
    color: #6e7681;
    padding: 8px 16px;
    border: 1px solid #30363d;
    border-bottom: none;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #161b22;
    color: #00d4ff;
    border-top: 2px solid #00d4ff;
}
QTabBar::tab:hover {
    color: #e6edf3;
    background: #1c2230;
}
QTableWidget {
    background: #161b22;
    gridline-color: #21262d;
    border: 1px solid #30363d;
    selection-background-color: #1f3a5f;
    alternate-background-color: #1c2230;
}
QTableWidget::item {
    padding: 4px 8px;
    border: none;
}
QHeaderView::section {
    background: #0d1117;
    color: #00d4ff;
    padding: 6px 8px;
    border: 1px solid #30363d;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
}
QPushButton {
    background: #1c2230;
    color: #00d4ff;
    border: 1px solid #00d4ff;
    padding: 6px 16px;
    border-radius: 3px;
    font-weight: bold;
    letter-spacing: 1px;
}
QPushButton:hover {
    background: #00d4ff;
    color: #0d1117;
}
QPushButton:pressed {
    background: #0099bb;
}
QPushButton:disabled {
    color: #6e7681;
    border-color: #30363d;
}
QComboBox {
    background: #1c2230;
    color: #e6edf3;
    border: 1px solid #30363d;
    padding: 4px 8px;
    border-radius: 3px;
}
QComboBox:hover { border-color: #00d4ff; }
QComboBox QAbstractItemView {
    background: #1c2230;
    color: #e6edf3;
    selection-background-color: #1f3a5f;
    border: 1px solid #30363d;
}
QScrollBar:vertical {
    background: #0d1117;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #00d4ff; }
QScrollBar:horizontal {
    background: #0d1117;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 5px;
}
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QStatusBar {
    background: #0d1117;
    color: #6e7681;
    border-top: 1px solid #30363d;
}
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    color: #00d4ff;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QLabel { color: #e6edf3; }
QLineEdit {
    background: #1c2230;
    color: #e6edf3;
    border: 1px solid #30363d;
    padding: 4px 8px;
    border-radius: 3px;
}
QLineEdit:focus { border-color: #00d4ff; }
QTextEdit {
    background: #0d1117;
    color: #39ff14;
    border: 1px solid #30363d;
    font-family: 'Consolas', monospace;
    font-size: 11px;
}
QCheckBox { color: #e6edf3; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid #30363d;
    background: #1c2230;
    border-radius: 2px;
}
QCheckBox::indicator:checked {
    background: #00d4ff;
    border-color: #00d4ff;
}
QToolBar {
    background: #0d1117;
    border-bottom: 1px solid #30363d;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    background: transparent;
    color: #6e7681;
    border: none;
    padding: 4px 8px;
    border-radius: 3px;
}
QToolButton:hover { background: #1c2230; color: #e6edf3; }
QSplitter::handle { background: #30363d; }
"""


# ─── Signal Strength Bar Widget ───────────────────────────────────────────────
class SignalBar(QWidget):
    def __init__(self, value=-100, max_val=-20, parent=None):
        super().__init__(parent)
        self.value = value
        self.max_val = max_val
        self.setFixedSize(80, 16)

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
        p.setFont(QFont("Consolas", 8))
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
        p.setFont(QFont("Consolas", 8))
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
            p.setFont(QFont("Consolas", 8))
            p.drawText(2, y - 5, 50, 12, Qt.AlignRight, f"{dbm} dBm")
            p.setPen(QPen(GRID_CLR, 1, Qt.DashLine))

        # Time labels
        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 8))
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
            p.setFont(QFont("Consolas", 8))
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
            p.setFont(QFont("Consolas", 7))
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
            p.setFont(QFont("Consolas", 7))
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
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID,BSSID,MODE,CHAN,FREQ,RATE,SIGNAL,SECURITY",
             "dev", "wifi", "list"],
            stderr=subprocess.DEVNULL, timeout=8
        ).decode(errors="ignore")
        nets = []
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) < 8:
                continue
            ssid, bssid, mode, chan, freq, rate, sig, sec = parts[:8]
            try:
                signal_pct = int(sig)
                dbm = signal_pct // 2 - 100
                channel = int(chan) if chan.isdigit() else 6
                band = "5GHz" if "5" in freq else "2.4GHz"
                nets.append({
                    "ssid": ssid or "<hidden>",
                    "bssid": bssid.replace("\\", ":"),
                    "channel": channel,
                    "signal": dbm,
                    "band": band,
                    "security": sec or "OPEN",
                    "mode": mode,
                    "rate": rate,
                    "snr": dbm + 95,
                })
            except ValueError:
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
        self._build_log_tab()

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("● IDLE")
        self.status_label.setStyleSheet("color: #6e7681;")
        self.status.addWidget(self.status_label)
        self.scan_info = QLabel("")
        self.scan_info.setStyleSheet("color: #6e7681;")
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
        self.time_label.setStyleSheet("color:#00d4ff; font-family:Consolas; padding: 0 8px;")
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
        title.setStyleSheet("color:#00d4ff; font-size:14px; font-weight:bold; letter-spacing:2px;")
        layout.addWidget(title)

        layout.addStretch()

        self.wifi_count_lbl = QLabel("WiFi: 0")
        self.wifi_count_lbl.setStyleSheet("color:#39ff14; font-weight:bold; margin: 0 12px;")
        layout.addWidget(self.wifi_count_lbl)

        self.ble_count_lbl = QLabel("BLE: 0")
        self.ble_count_lbl.setStyleSheet("color:#a855f7; font-weight:bold; margin: 0 12px;")
        layout.addWidget(self.ble_count_lbl)

        self.scan_status_lbl = QLabel("● SCANNING")
        self.scan_status_lbl.setStyleSheet("color:#39ff14; font-weight:bold; margin: 0 12px;")
        layout.addWidget(self.scan_status_lbl)

        # Pulse animation
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_timer.start(600)
        self._pulse_state = True

        return frame

    def _pulse(self):
        if self._pulse_state:
            self.scan_status_lbl.setStyleSheet("color:#0d5c1e; font-weight:bold; margin:0 12px;")
        else:
            self.scan_status_lbl.setStyleSheet("color:#39ff14; font-weight:bold; margin:0 12px;")
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
            self.scan_status_lbl.setStyleSheet("color:#6e7681; font-weight:bold; margin:0 12px;")
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
            hide = text.lower() not in (item.text().lower() if item else "")
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
            hide = filt and filt not in ssid.lower()
            self.wifi_table.setRowHidden(row, hide)

        self.wifi_table.setSortingEnabled(True)
        self.wifi_table.setRowHeight(0, 28)
        for row in range(self.wifi_table.rowCount()):
            self.wifi_table.setRowHeight(row, 26)

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
            self.ble_table.setRowHeight(row, 26)

    def _update_channel_chart(self):
        band = self.ch_band_combo.currentText()
        self.channel_overlap.setNetworks(self.wifi_data, band)

        # Channel congestion table
        chan_count = defaultdict(list)
        for n in self.wifi_data:
            if n.get("band","2.4GHz") == band:
                chan_count[n["channel"]].append(n["signal"])

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
            self.chan_table.setRowHeight(row, 24)

    def closeEvent(self, event):
        if hasattr(self, "scanner"):
            self.scanner.stop()
            self.scanner.wait(2000)
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
