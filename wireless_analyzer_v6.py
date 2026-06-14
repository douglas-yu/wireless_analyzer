#!/usr/bin/env python3
"""
Wireless Analyzer Pro - WiFi & Bluetooth LE Scanner
"""
import sys, os, re, time, math, random, subprocess, threading
from datetime import datetime
from collections import defaultdict
from winrt_wifi_patch import apply_winrt_patch
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QComboBox, QSplitter, QStatusBar,
    QFrame, QGroupBox, QSizePolicy, QToolBar, QAction,
    QTextEdit, QScrollArea, QLineEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QPainterPath, QIcon, QPalette, QPolygonF
)

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DARK      = QColor("#0d1117")
BG_PANEL     = QColor("#161b22")
BG_CARD      = QColor("#1c2230")
ACCENT_CYAN  = QColor("#00d4ff")
ACCENT_GREEN = QColor("#39ff14")
ACCENT_ORANGE= QColor("#ff6b35")
ACCENT_PINK  = QColor("#ff2d78")
ACCENT_PURPLE= QColor("#a855f7")
TEXT_PRIMARY = QColor("#e6edf3")
TEXT_DIM     = QColor("#8b949e")
BORDER_CLR   = QColor("#30363d")
GRID_CLR     = QColor("#1f2937")

CHAN_COLORS = [
    "#00d4ff","#39ff14","#ff6b35","#ff2d78","#a855f7",
    "#ffd700","#00ff99","#ff4444","#44aaff","#ff8800",
    "#cc44ff","#00ffcc","#ff66aa","#88ff00","#ff0099",
]

STYLE = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}
QTabWidget::pane { border: 1px solid #30363d; background: #161b22; }
QTabBar::tab {
    background: #0d1117; color: #8b949e;
    padding: 10px 22px; border: 1px solid #30363d;
    border-bottom: none; margin-right: 2px;
    font-size: 14px; font-weight: bold;
}
QTabBar::tab:selected { background: #161b22; color: #00d4ff; border-top: 2px solid #00d4ff; }
QTabBar::tab:hover    { color: #e6edf3; background: #1c2230; }
QTableWidget {
    background: #161b22; gridline-color: #21262d;
    border: 1px solid #30363d;
    selection-background-color: #1f3a5f;
    alternate-background-color: #1c2230;
    font-size: 13px;
}
QTableWidget::item { padding: 5px 10px; border: none; }
QHeaderView::section {
    background: #0d1117; color: #00d4ff;
    padding: 8px 10px; border: 1px solid #30363d;
    font-weight: bold; font-size: 13px; letter-spacing: 1px;
}
QPushButton {
    background: #1c2230; color: #00d4ff;
    border: 1px solid #00d4ff; padding: 8px 18px;
    border-radius: 4px; font-weight: bold; font-size: 13px;
}
QPushButton:hover   { background: #00d4ff; color: #0d1117; }
QPushButton:pressed { background: #0099bb; }
QPushButton:disabled{ color: #6e7681; border-color: #30363d; }
QComboBox {
    background: #1c2230; color: #e6edf3;
    border: 1px solid #30363d; padding: 5px 10px;
    border-radius: 4px; font-size: 13px; min-height: 28px;
}
QComboBox:hover { border-color: #00d4ff; }
QComboBox QAbstractItemView {
    background: #1c2230; color: #e6edf3;
    selection-background-color: #1f3a5f;
    border: 1px solid #30363d; font-size: 13px;
}
QScrollBar:vertical   { background:#0d1117; width:12px; border:none; }
QScrollBar:horizontal { background:#0d1117; height:12px; border:none; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #30363d; border-radius: 6px; min-height: 24px;
}
QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover { background: #00d4ff; }
QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; }
QStatusBar { background:#0d1117; color:#8b949e; border-top:1px solid #30363d; font-size:13px; }
QLabel     { color:#e6edf3; font-size:14px; }
QLineEdit  { background:#1c2230; color:#e6edf3; border:1px solid #30363d; padding:5px 10px; border-radius:4px; font-size:13px; }
QLineEdit:focus { border-color:#00d4ff; }
QTextEdit  { background:#0d1117; color:#39ff14; border:1px solid #30363d; font-family:'Consolas','Courier New',monospace; font-size:13px; }
QCheckBox  { color:#e6edf3; spacing:8px; font-size:13px; }
QCheckBox::indicator { width:16px; height:16px; border:1px solid #30363d; background:#1c2230; border-radius:3px; }
QCheckBox::indicator:checked { background:#00d4ff; border-color:#00d4ff; }
QToolBar   { background:#0d1117; border-bottom:1px solid #30363d; spacing:6px; padding:5px; }
QToolButton{ background:transparent; color:#8b949e; border:none; padding:6px 12px; border-radius:4px; font-size:13px; }
QToolButton:hover { background:#1c2230; color:#e6edf3; }
QSplitter::handle { background:#30363d; }
QSpinBox   { background:#1c2230; color:#e6edf3; border:1px solid #30363d; padding:5px 8px; border-radius:4px; font-size:13px; }
QGroupBox  { border:1px solid #30363d; border-radius:4px; margin-top:10px; padding-top:10px; color:#00d4ff; font-weight:bold; font-size:14px; }
QGroupBox::title { subcontrol-origin:margin; left:8px; padding:0 4px; }
"""


# ── Signal Bar ────────────────────────────────────────────────────────────────
class SignalBar(QWidget):
    def __init__(self, value=-100, parent=None):
        super().__init__(parent)
        self.value = value
        self.setFixedSize(100, 22)

    def setValue(self, v):
        self.value = v
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pct = max(0.0, min(1.0, (self.value + 100) / 80.0))
        bars, gap = 5, 3
        bw = (w - gap * (bars - 1)) // bars
        for i in range(bars):
            filled = pct >= (i + 1) / bars
            x  = i * (bw + gap)
            bh = int(h * (i + 1) / bars)
            rect = QRect(x, h - bh, bw, bh)
            if filled:
                c = QColor("#39ff14") if pct > 0.7 else QColor("#ffd700") if pct > 0.4 else QColor("#ff6b35")
            else:
                c = QColor("#1c2230")
            p.fillRect(rect, c)
        p.end()

# ── Channel Overlap ───────────────────────────────────────────────────────────
class ChannelOverlapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.networks = []
        self.band = "2.4GHz"
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setNetworks(self, nets, band="2.4GHz"):
        self.networks = [n for n in nets if n.get("band","2.4GHz") == band]
        self.band = band
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, BG_PANEL)
        ml, mr, mt, mb = 65, 20, 24, 48
        pw = w - ml - mr
        ph = h - mt - mb

        p.setPen(QPen(GRID_CLR, 1))
        for i in range(5):
            y = mt + int(ph * i / 4)
            p.drawLine(ml, y, ml + pw, y)
            p.setPen(QPen(TEXT_DIM, 1))
            p.setFont(QFont("Consolas", 11))
            p.drawText(2, y - 6, 60, 16, Qt.AlignRight, f"{-20 - i*20}")
            p.setPen(QPen(GRID_CLR, 1))

        if self.band == "2.4GHz":
            channels  = list(range(1, 15))
            ch_start, ch_end = 1, 14
        else:
            channels  = [36,40,44,48,52,56,60,64,100,104,108,112,116,120,
                         124,128,132,136,140,149,153,157,161,165]
            ch_start, ch_end = 36, 165
        span = ch_end - ch_start + 2

        def ch_x(ch):
            return ml + int((ch - ch_start + 0.5) / span * pw)
        def db_y(dbm):
            f = (max(-100, min(-20, dbm)) + 20) / (-80.0)
            return mt + int(f * ph)

        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 11))
        for ch in channels:
            x = ch_x(ch)
            p.drawLine(x, mt + ph, x, mt + ph + 4)
            p.drawText(x - 12, h - mb + 8, 24, 16, Qt.AlignHCenter, str(ch))

        p.setPen(QPen(TEXT_PRIMARY, 1))
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        p.drawText(0, h - 16, w, 16, Qt.AlignHCenter, f"Channel  ({self.band})")

        for idx, net in enumerate(self.networks):
            ch  = net.get("channel", 6)
            sig = net.get("signal", -70)
            ssid = net.get("ssid", "?")
            color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
            w_ch = 2.2 if self.band == "2.4GHz" else 2.0
            path = QPainterPath()
            steps = 80
            pts = []
            for s in range(steps + 1):
                t = (s / steps) * w_ch * 6 - w_ch * 3
                amp = math.exp(-0.5 * t**2) * (sig + 100) / 80
                y = db_y(-100 + amp * 80)
                pts.append(QPointF(ch_x(ch + t / 3), y))
            if pts:
                bot = db_y(-100)
                path.moveTo(QPointF(pts[0].x(), bot))
                for pt in pts: path.lineTo(pt)
                path.lineTo(QPointF(pts[-1].x(), bot))
                path.closeSubpath()
                fill = QColor(color); fill.setAlpha(55)
                p.fillPath(path, QBrush(fill))
                stroke = QColor(color); stroke.setAlpha(230)
                p.strokePath(path, QPen(stroke, 2))
            px, py = ch_x(ch), db_y(sig) - 6
            p.setPen(QPen(color, 1))
            p.setFont(QFont("Consolas", 11, QFont.Bold))
            lbl = ssid[:12]
            p.drawText(px - 36, py - 16, 72, 14, Qt.AlignHCenter, lbl)

        p.setPen(QPen(BORDER_CLR, 1))
        p.drawRect(ml, mt, pw, ph)
        p.end()

# ── Signal History ────────────────────────────────────────────────────────────
class SignalHistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = {}
        self.max_pts = 60
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def addSample(self, ssid, dbm):
        self.history.setdefault(ssid, []).append(dbm)
        if len(self.history[ssid]) > self.max_pts:
            self.history[ssid].pop(0)
        self.update()

    def clear(self):
        self.history.clear(); self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, BG_PANEL)
        ml, mr, mt, mb = 60, 12, 12, 34
        pw, ph = w - ml - mr, h - mt - mb

        p.setPen(QPen(GRID_CLR, 1, Qt.DashLine))
        for i in range(5):
            y = mt + int(ph * i / 4)
            p.drawLine(ml, y, ml + pw, y)
            p.setPen(QPen(TEXT_DIM, 1))
            p.setFont(QFont("Consolas", 11))
            p.drawText(2, y - 6, 56, 14, Qt.AlignRight, f"{-20 - i*20} dBm")
            p.setPen(QPen(GRID_CLR, 1, Qt.DashLine))

        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 11))
        for i in range(0, self.max_pts + 1, 10):
            x = ml + int(i / self.max_pts * pw)
            t = self.max_pts - i
            p.drawText(x - 14, h - mb + 8, 28, 14, Qt.AlignHCenter,
                       f"-{t}s" if t else "now")

        for idx, (ssid, vals) in enumerate(list(self.history.items())[:12]):
            if len(vals) < 2: continue
            color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
            p.setPen(QPen(color, 2))
            n = len(vals)
            pts = []
            for i, v in enumerate(vals):
                x = ml + int((self.max_pts - n + i) / self.max_pts * pw)
                f = (max(-100, min(-20, v)) + 20) / (-80.0)
                pts.append(QPointF(x, mt + int(f * ph)))
            for i in range(len(pts) - 1):
                p.drawLine(pts[i], pts[i + 1])

        if self.history:
            lx, ly = ml + 8, mt + 8
            p.setFont(QFont("Consolas", 11))
            for idx, ssid in enumerate(list(self.history.keys())[:8]):
                color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
                p.setPen(QPen(color, 2))
                p.drawLine(lx, ly + 6, lx + 18, ly + 6)
                p.setPen(QPen(TEXT_PRIMARY, 1))
                p.drawText(lx + 22, ly - 1, 120, 14, Qt.AlignLeft, ssid[:16])
                ly += 18
                if ly > mt + ph - 8: break

        p.setPen(QPen(BORDER_CLR, 1))
        p.drawRect(ml, mt, pw, ph)
        p.end()

# ── BLE Radar ─────────────────────────────────────────────────────────────────
class BLERadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = []
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._ang = 0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(50)

    def _tick(self):
        self._ang = (self._ang + 2) % 360; self.update()

    def setDevices(self, devs):
        self.devices = devs; self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 24
        p.fillRect(0, 0, w, h, BG_PANEL)

        for i in range(1, 5):
            rr = int(r * i / 4)
            p.setPen(QPen(GRID_CLR, 1))
            p.drawEllipse(QPointF(cx, cy), rr, rr)
            p.setPen(QPen(TEXT_DIM, 1))
            p.setFont(QFont("Consolas", 11))
            p.drawText(cx + rr + 3, cy - 5, 36, 14, Qt.AlignLeft, f"{-20 - i*20}")

        ar = math.radians(self._ang)
        for i in range(70):
            a = ar - math.radians(i)
            alpha = int(28 * (1 - i / 70))
            p.setPen(QPen(QColor(0, 212, 255, alpha), 1.5))
            p.drawLine(cx, cy, int(cx + r * math.cos(a)), int(cy - r * math.sin(a)))
        p.setPen(QPen(QColor(0, 212, 255, 200), 1.5))
        p.drawLine(cx, cy, int(cx + r * math.cos(ar)), int(cy - r * math.sin(ar)))

        p.setPen(QPen(GRID_CLR, 1))
        p.drawLine(cx - r, cy, cx + r, cy)
        p.drawLine(cx, cy - r, cx, cy + r)

        for idx, dev in enumerate(self.devices[:16]):
            sig   = dev.get("rssi", -70)
            angle = dev.get("_angle", idx * 45) % 360
            frac  = max(0.0, min(1.0, (sig + 100) / 80.0))
            dist  = (1.0 - frac) * r * 0.92
            ang_r = math.radians(angle)
            dx = cx + dist * math.cos(ang_r)
            dy = cy - dist * math.sin(ang_r)
            color = QColor(CHAN_COLORS[idx % len(CHAN_COLORS)])
            p.setPen(QPen(color, 2)); p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(dx, dy), 6, 6)
            p.setPen(QPen(color, 1))
            p.setFont(QFont("Consolas", 11))
            name = dev.get("name", dev.get("address","?"))[:12]
            p.drawText(int(dx) + 9, int(dy) - 5, 100, 14, Qt.AlignLeft, name)

        p.setBrush(QBrush(ACCENT_CYAN)); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), 5, 5)

        p.setPen(QPen(TEXT_DIM, 1))
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        p.drawText(0, 4, w, 16, Qt.AlignHCenter, "BLE RADAR")
        p.end()

# ── Audit Score Widget ────────────────────────────────────────────────────────
class AuditScoreWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 100; self._findings = 0
        self.setMinimumHeight(150)

    def setScore(self, score, findings):
        self._score = score; self._findings = findings; self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, BG_PANEL)
        cx, cy, r = 80, h // 2, 55
        p.setPen(QPen(GRID_CLR, 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(cx - r, cy - r, r*2, r*2, 225*16, -270*16)
        sc = self._score
        clr = (QColor("#39ff14") if sc >= 75 else QColor("#ffd700") if sc >= 50
               else QColor("#ff6b35") if sc >= 25 else QColor("#ff2d78"))
        span = int(-270 * 16 * sc / 100)
        p.setPen(QPen(clr, 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(cx - r, cy - r, r*2, r*2, 225*16, span)
        p.setPen(QPen(clr, 1))
        p.setFont(QFont("Consolas", 22, QFont.Bold))
        p.drawText(cx - 32, cy - 14, 64, 30, Qt.AlignHCenter, str(sc))
        p.setFont(QFont("Consolas", 11))
        p.setPen(QPen(TEXT_DIM, 1))
        p.drawText(cx - 32, cy + 16, 64, 14, Qt.AlignHCenter, "/100")
        grade = ("A+" if sc>=95 else "A" if sc>=85 else "B" if sc>=75
                 else "C" if sc>=60 else "D" if sc>=45 else "F")
        p.setFont(QFont("Consolas", 13, QFont.Bold))
        p.setPen(QPen(clr, 1))
        p.drawText(cx - 40, cy + 32, 80, 18, Qt.AlignHCenter, f"Grade: {grade}")

        lx = cx + r + 24
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        p.setPen(QPen(TEXT_PRIMARY, 1))
        p.drawText(lx, 14, 220, 18, Qt.AlignLeft, "Security Score")
        p.setFont(QFont("Consolas", 11))
        p.setPen(QPen(TEXT_DIM, 1))
        p.drawText(lx, 34, 220, 14, Qt.AlignLeft, f"Total findings: {self._findings}")
        thresholds = [
            (QColor("#39ff14"), "≥75  Acceptable"),
            (QColor("#ffd700"), "≥50  Needs attention"),
            (QColor("#ff6b35"), "≥25  Vulnerable"),
            (QColor("#ff2d78"), " <25  Critical risk"),
        ]
        y = 52
        for c, txt in thresholds:
            p.setPen(QPen(c, 3)); p.drawLine(lx, y + 6, lx + 16, y + 6)
            p.setPen(QPen(TEXT_DIM, 1))
            p.drawText(lx + 20, y, 220, 16, Qt.AlignLeft, txt)
            y += 20
        p.end()

# ── Scanner Thread ────────────────────────────────────────────────────────────
class ScannerThread(QThread):
    wifi_result = pyqtSignal(list)
    ble_result  = pyqtSignal(list)
    log_message = pyqtSignal(str)

    def __init__(self, interval=3):
        super().__init__()
        self.interval = interval
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            self.wifi_result.emit(self._scan_wifi())
            self.ble_result.emit(self._scan_ble())
            for _ in range(self.interval * 10):
                if not self._running: break
                time.sleep(0.1)

    def stop(self): self._running = False

    # ── wifi ──────────────────────────────────────────────────────────────────
    def _scan_wifi(self):
        for fn in [self._try_nmcli, self._try_iwlist,
                   self._try_airport, self._try_netsh]:
            try:
                nets = fn()
                if nets:
                    self.log_message.emit(f"[WiFi] {fn.__name__}: {len(nets)} networks")
                    return nets
            except Exception as ex:
                self.log_message.emit(f"[WiFi] {fn.__name__} failed: {ex}")
        self.log_message.emit("[WiFi] Using demo data")
        return self._mock_wifi()

    def _try_nmcli(self):
        """Column-mode nmcli so BSSID colons don't break splitting."""
        out = subprocess.check_output(
            ["nmcli", "-f", "SSID,BSSID,MODE,CHAN,FREQ,RATE,SIGNAL,SECURITY",
             "dev", "wifi", "list"],
            stderr=subprocess.DEVNULL, timeout=8
        ).decode(errors="ignore")
        lines = [l for l in out.splitlines() if l.strip()]
        if len(lines) < 2:
            return []
        # Build column start positions from header
        header = lines[0]
        cols   = header.split()
        starts = [header.index(c) for c in cols]
        starts.append(len(header) + 999)

        def gcol(line, i):
            s = starts[i]
            e = starts[i + 1]
            return line[s:e].strip() if s < len(line) else ""

        nets = []
        for line in lines[1:]:
            if not line.strip() or set(line.strip()) <= set("- "):
                continue
            try:
                ssid  = gcol(line, 0) or "<hidden>"
                bssid = gcol(line, 1)
                mode  = gcol(line, 2)
                chan  = gcol(line, 3)
                freq  = gcol(line, 4)
                rate  = gcol(line, 5)
                sig   = gcol(line, 6)
                sec   = gcol(line, 7)
                pct   = int(sig) if sig.isdigit() else 50
                dbm   = pct // 2 - 100
                ch    = int(chan) if chan.isdigit() else 6
                band  = "5GHz" if freq.startswith("5") else "2.4GHz"
                nets.append({
                    "ssid": ssid, "bssid": bssid,
                    "channel": ch, "signal": dbm,
                    "band": band, "security": sec or "OPEN",
                    "mode": mode, "rate": rate,
                    "snr": dbm + 95,
                })
            except (ValueError, IndexError):
                continue
        return nets

    def _try_iwlist(self):
        iw = subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT,
                                      timeout=5).decode(errors="ignore")
        iface = next((l.split()[0] for l in iw.splitlines()
                      if l and ("IEEE 802.11" in l or "ESSID" in l)), None)
        if not iface: return []
        out = subprocess.check_output(["sudo","iwlist",iface,"scan"],
                                       stderr=subprocess.DEVNULL, timeout=15
                                       ).decode(errors="ignore")
        nets, cur = [], {}
        for line in out.splitlines():
            line = line.strip()
            if "Cell" in line and "Address:" in line:
                if cur: nets.append(cur)
                cur = {"bssid": line.split("Address:")[-1].strip()}
            elif "ESSID:" in line:
                cur["ssid"] = line.split('"')[1] if '"' in line else "<hidden>"
            elif "Channel:" in line:
                try: cur["channel"] = int(line.split("Channel:")[-1])
                except: pass
            elif "Signal level=" in line:
                m = re.search(r"Signal level=(-?\d+)", line)
                if m: cur["signal"] = int(m.group(1))
            elif "Encryption key:" in line:
                cur["security"] = "WPA" if "on" in line.lower() else "OPEN"
            elif "Frequency:" in line:
                cur["band"] = "5GHz" if "5." in line else "2.4GHz"
            elif "Bit Rates:" in line:
                cur["rate"] = line.split(":")[-1].strip()
            elif "IE: IEEE 802.11i" in line or "WPA2" in line:
                cur["security"] = "WPA2"
        if cur: nets.append(cur)
        for n in nets:
            n.setdefault("ssid","<hidden>"); n.setdefault("signal",-70)
            n.setdefault("channel",6);       n.setdefault("band","2.4GHz")
            n.setdefault("security","WPA2"); n.setdefault("rate","?")
            n.setdefault("mode","802.11");   n["snr"] = n["signal"] + 95
        return nets

    def _try_airport(self):
        ap = ("/System/Library/PrivateFrameworks/Apple80211.framework"
              "/Versions/Current/Resources/airport")
        if not os.path.exists(ap): return []
        out = subprocess.check_output([ap,"-s"],stderr=subprocess.DEVNULL,
                                       timeout=10).decode(errors="ignore")
        nets = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 7: continue
            try:
                rssi = int(parts[2]); ch = int(parts[3].split(",")[0])
                nets.append({
                    "ssid": parts[0], "bssid": parts[1],
                    "signal": rssi, "channel": ch,
                    "band": "5GHz" if ch > 14 else "2.4GHz",
                    "security": parts[6], "snr": rssi + 95,
                    "rate": "?", "mode": "802.11",
                })
            except (ValueError, IndexError): continue
        return nets

    def _try_netsh(self):
        out = subprocess.check_output(
            ["netsh","wlan","show","networks","mode=bssid"],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode(errors="ignore")
        nets, cur = [], {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if cur: nets.append(cur)
                cur = {"ssid": line.split(":",1)[-1].strip()}
            elif "BSSID" in line:
                cur["bssid"] = line.split(":",1)[-1].strip()
            elif "Signal" in line:
                try:
                    pct = int(line.split(":")[-1].strip().replace("%",""))
                    cur["signal"] = pct // 2 - 100; cur["snr"] = pct // 2 - 5
                except: pass
            elif "Channel" in line:
                try:
                    ch = int(line.split(":")[-1].strip())
                    cur["channel"] = ch
                    cur["band"] = "5GHz" if ch > 14 else "2.4GHz"
                except: pass
            elif "Authentication" in line:
                cur["security"] = line.split(":")[-1].strip()
            elif "Radio type" in line:
                cur["mode"] = line.split(":")[-1].strip()
            elif "Basic rates" in line or "Other rates" in line:
                cur.setdefault("rate", line.split(":")[-1].strip())
        if cur: nets.append(cur)
        for n in nets:
            n.setdefault("channel",6); n.setdefault("band","2.4GHz")
            n.setdefault("mode","802.11"); n.setdefault("rate","?")
            n.setdefault("snr", n.get("signal",-70) + 95)
        return nets

    def _mock_wifi(self):
        data = [
            ("HomeNetwork_5G",   "AA:BB:CC:11:22:33", 149, "5GHz",  -45, "WPA3",          "802.11ax", "1201 Mbps"),
            ("OfficeWifi",       "AA:BB:CC:44:55:66", 6,   "2.4GHz",-62, "WPA2-Enterprise","802.11n",  "300 Mbps"),
            ("GuestNetwork",     "DD:EE:FF:11:22:33", 11,  "2.4GHz",-71, "WPA2",           "802.11n",  "130 Mbps"),
            ("NETGEAR_5G",       "11:22:33:AA:BB:CC", 36,  "5GHz",  -58, "WPA2",           "802.11ac", "867 Mbps"),
            ("Linksys_24",       "22:33:44:BB:CC:DD", 1,   "2.4GHz",-80, "WPA2",           "802.11g",  "54 Mbps"),
            ("TP-Link_Main",     "33:44:55:CC:DD:EE", 6,   "2.4GHz",-55, "WPA2",           "802.11ac", "450 Mbps"),
            ("xfinitywifi",      "44:55:66:DD:EE:FF", 11,  "2.4GHz",-88, "OPEN",           "802.11g",  "54 Mbps"),
            ("ATT_Router",       "66:77:88:FF:AA:BB", 1,   "2.4GHz",-66, "WPA2",           "802.11n",  "300 Mbps"),
            ("Spectrum_5G",      "77:88:99:AA:BB:CC", 157, "5GHz",  -50, "WPA2",           "802.11ac", "867 Mbps"),
            ("FreeWifi_Plaza",   "88:99:AA:BB:CC:DD", 6,   "2.4GHz",-92, "OPEN",           "802.11g",  "54 Mbps"),
            ("ASUS_AX88U",       "99:AA:BB:CC:DD:EE", 44,  "5GHz",  -48, "WPA3",           "802.11ax", "2402 Mbps"),
            ("HiddenNetwork",    "55:66:77:EE:FF:AA", 100, "5GHz",  -76, "WPA2",           "802.11ac", "433 Mbps"),
        ]
        nets = []
        for ssid, bssid, ch, band, sig_base, sec, mode, rate in data:
            sig = sig_base + random.randint(-3, 3)
            nets.append({
                "ssid": ssid, "bssid": bssid, "channel": ch, "band": band,
                "signal": sig, "security": sec, "mode": mode, "rate": rate,
                "snr": sig + 95 + random.randint(0, 5),
            })
        return nets

    # ── ble ───────────────────────────────────────────────────────────────────
    def _scan_ble(self):
        try:
            out = subprocess.check_output(["bluetoothctl","devices"],
                                           stderr=subprocess.DEVNULL,timeout=5
                                           ).decode(errors="ignore")
            devs = []
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "Device":
                    devs.append({"address": parts[1],
                                 "name": " ".join(parts[2:]),
                                 "rssi": random.randint(-90,-40),
                                 "type":"BLE","_angle":random.randint(0,359)})
            if devs: return devs
        except Exception: pass
        return self._mock_ble()

    def _mock_ble(self):
        data = [
            ("iPhone 15 Pro",   "A4:C3:F0:12:34:56", -52, "Phone"),
            ("Galaxy Watch 6",  "B8:D4:E2:78:9A:BC", -68, "Wearable"),
            ("AirPods Pro 2",   "C6:A1:44:DE:F0:12", -45, "Audio"),
            ("Tile Mate",       "D2:B3:55:34:56:78", -79, "Tracker"),
            ("Mi Band 8",       "E0:C5:66:9A:BC:DE", -71, "Wearable"),
            ("Xbox Controller", "F1:D6:77:F0:12:34", -63, "GamePad"),
            ("BT Keyboard",     "A2:E7:88:56:78:9A", -57, "HID"),
            ("Smart TV BLE",    "B3:F8:99:BC:DE:F0", -84, "Entertainment"),
        ]
        return [{"name":n,"address":a,"rssi":r+random.randint(-3,3),
                 "type":t,"_angle":i*45+random.randint(-15,15),
                 "services":random.randint(1,8),
                 "paired":random.choice([True,False]),
                 "connected":random.choice([True,False,False])}
                for i,(n,a,r,t) in enumerate(data)]
apply_winrt_patch(ScannerThread)
# ── Packet Sniffer Thread ─────────────────────────────────────────────────────
class PacketSnifferThread(QThread):
    packet_captured = pyqtSignal(dict)
    sniffer_log     = pyqtSignal(str)

    FRAME_TYPES    = {0:"Mgmt", 1:"Ctrl", 2:"Data", 3:"Ext"}
    MGMT_SUBTYPES  = {0:"Assoc Req",1:"Assoc Resp",4:"Probe Req",5:"Probe Resp",
                      8:"Beacon",10:"Disassoc",11:"Auth",12:"Deauth",13:"Action"}
    CTRL_SUBTYPES  = {11:"RTS",12:"CTS",13:"ACK",14:"CF-End"}
    DATA_SUBTYPES  = {0:"Data",4:"Null",8:"QoS Data",12:"QoS Null"}

    def __init__(self, iface, max_packets=1000):
        super().__init__()
        self.iface = iface; self.max_packets = max_packets
        self._running = False; self._counter = 0

    def run(self):
        self._running = True; self._counter = 0
        try:
            import importlib.util
            if importlib.util.find_spec("scapy"):
                from scapy.all import sniff
                self.sniffer_log.emit(f"[Sniffer] scapy capture on {self.iface}")
                sniff(iface=self.iface, prn=self._handle_scapy,
                      stop_filter=lambda _: not self._running,
                      store=False, monitor=True)
                return
        except Exception as e:
            self.sniffer_log.emit(f"[Sniffer] scapy: {e}")
        try:
            self.sniffer_log.emit(f"[Sniffer] tcpdump on {self.iface}")
            self._run_tcpdump(); return
        except Exception as e:
            self.sniffer_log.emit(f"[Sniffer] tcpdump: {e}")
        self.sniffer_log.emit("[Sniffer] Demo stream active")
        self._run_mock()

    def _handle_scapy(self, pkt):
        if not self._running: return
        try:
            from scapy.all import Dot11, RadioTap, Dot11Elt
            if not pkt.haslayer(Dot11): return
            d = pkt[Dot11]
            ftype   = self.FRAME_TYPES.get(d.type, f"T{d.type}")
            sub_map = {0:self.MGMT_SUBTYPES,1:self.CTRL_SUBTYPES,2:self.DATA_SUBTYPES}
            subtype = sub_map.get(d.type,{}).get(d.subtype, f"Sub{d.subtype}")
            sig = -70; ch = "?"
            if pkt.haslayer(RadioTap):
                rt = pkt[RadioTap]
                if hasattr(rt,"dBm_AntSignal"): sig = rt.dBm_AntSignal
                if hasattr(rt,"Channel"): ch = rt.Channel
            ssid = ""
            if pkt.haslayer(Dot11Elt):
                elt = pkt[Dot11Elt]
                while elt:
                    if elt.ID == 0:
                        try: ssid = elt.info.decode(errors="replace")
                        except: pass
                    try: elt = elt.payload.getlayer(Dot11Elt)
                    except: break
            raw = bytes(pkt); self._counter += 1
            self.packet_captured.emit(self._build_pkt(
                self._counter, d.type, d.subtype, ftype, subtype,
                d.addr2 or "—", d.addr1 or "—", d.addr3 or "—",
                ch, sig, len(raw), ssid, raw))
        except Exception: pass

    def _run_tcpdump(self):
        proc = subprocess.Popen(
            ["sudo","tcpdump","-i",self.iface,"-l","-e","-n",
             "--immediate-mode","-s","256","type mgt or type ctl or type data"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        while self._running and proc.poll() is None:
            line = proc.stdout.readline()
            if not line: continue
            pkt = self._parse_tcpdump(line.strip())
            if pkt: self.packet_captured.emit(pkt)
        proc.terminate()

    def _parse_tcpdump(self, line):
        if not line: return None
        self._counter += 1
        parts = line.split()
        ts = parts[0] if parts else datetime.now().strftime("%H:%M:%S.000")
        src = dst = "?"; ptype = "Data"; subtype = "Frame"
        for i, px in enumerate(parts):
            if px=="SA:" and i+1<len(parts): src = parts[i+1].rstrip(",")
            if px=="DA:" and i+1<len(parts): dst = parts[i+1].rstrip(",")
            if "Beacon"   in px: ptype,subtype = "Mgmt","Beacon"
            if "Probe"    in px: ptype,subtype = "Mgmt","Probe Req"
            if "Auth"     in px: ptype,subtype = "Mgmt","Auth"
            if "Assoc"    in px: ptype,subtype = "Mgmt","Assoc Req"
            if "Deauth"   in px: ptype,subtype = "Mgmt","Deauth"
            if "Disassoc" in px: ptype,subtype = "Mgmt","Disassoc"
            if "QoS"      in px: ptype,subtype = "Data","QoS Data"
        raw = bytes(random.randint(0,255) for _ in range(random.randint(28,256)))
        return self._build_pkt(self._counter, 0, 0, ptype, subtype,
                                src, dst, "—",
                                random.randint(1,13), random.randint(-85,-35),
                                len(raw), "", raw, info=line[:80])

    def _run_mock(self):
        mock_nets = [
            ("HomeNetwork",  "AA:BB:CC:11:22:33", 6,  -48),
            ("OfficeWifi",   "DD:EE:FF:44:55:66", 11, -62),
            ("NETGEAR_5G",   "11:22:33:AA:BB:CC", 36, -55),
            ("GuestNet",     "22:33:44:BB:CC:DD", 1,  -71),
        ]
        clients = ["C4:B3:01:12:34:56","A8:66:7F:78:9A:BC",
                   "F0:18:98:DE:F0:12","3C:22:FB:34:56:78"]
        frames = [
            (0,"Beacon",0,True),   (0,"Beacon",1,True),
            (0,"Probe Req",0,False),(0,"Probe Resp",0,True),
            (0,"Auth",0,True),     (0,"Assoc Req",0,False),
            (0,"Assoc Resp",0,True),(0,"Deauth",0,True),
            (2,"QoS Data",0,False),(2,"QoS Data",0,False),
            (2,"QoS Data",0,False),(2,"Null",0,False),
            (1,"ACK",0,False),     (1,"RTS",0,False),
        ]
        while self._running and self._counter < self.max_packets:
            ftype_i,subtype,net_i,from_ap = random.choice(frames)
            ssid,ap,ch,sig_b = mock_nets[net_i % len(mock_nets)]
            cli = random.choice(clients)
            src = ap if from_ap else cli
            dst = "FF:FF:FF:FF:FF:FF" if subtype=="Beacon" else (cli if from_ap else ap)
            sig = sig_b + random.randint(-4,4)
            raw = bytes(random.randint(0,255) for _ in range(random.randint(28,1500)))
            self._counter += 1
            iv = "".join(f"{random.randint(0,255):02x}" for _ in range(3))
            info = f"SSID={ssid}" if subtype in ("Beacon","Probe Resp","Assoc Req") else \
                   f"IV=0x{iv} CCMP" if ftype_i==2 else ""
            self.packet_captured.emit(self._build_pkt(
                self._counter, ftype_i, 0,
                self.FRAME_TYPES.get(ftype_i,"?"), subtype,
                src, dst, ap, ch, sig, len(raw), ssid, raw, info=info))
            time.sleep(random.uniform(0.04, 0.30))

    def _build_pkt(self, num, ftype_i, fsub_i, ftype, subtype,
                   src, dst, bssid, ch, sig, size, ssid, raw, info=""):
        if not info:
            info = f"SSID={ssid}" if ssid else subtype
        return {
            "num": num,
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "src": src, "dst": dst, "bssid": bssid,
            "type": ftype, "subtype": subtype,
            "channel": ch, "signal": sig, "size": size,
            "info": info,
            "decode": "\n".join([
                "IEEE 802.11 Wireless LAN",
                f"  ├─ Type     : {ftype} ({ftype_i})",
                f"  ├─ Subtype  : {subtype}",
                f"  ├─ Src (SA) : {src}",
                f"  ├─ Dst (DA) : {dst}",
                f"  ├─ BSSID    : {bssid}",
                f"  ├─ Channel  : {ch}",
                f"  ├─ Signal   : {sig} dBm",
                f"  └─ Size     : {size} bytes",
                *(["", "Tagged Parameters", f"  └─ SSID     : {ssid}"] if ssid else []),
                *(["", "Frame Info", f"  {info}"] if info else []),
            ]),
            "hexdump": self._hexdump(raw),
        }

    def _hexdump(self, raw):
        lines = []
        for i in range(0, min(len(raw), 512), 16):
            ch = raw[i:i+16]
            h  = " ".join(f"{b:02x}" for b in ch)
            a  = "".join(chr(b) if 32<=b<127 else "." for b in ch)
            lines.append(f"  {i:04x}  {h:<47}  {a}")
        if len(raw) > 512:
            lines.append(f"  ... ({len(raw)-512} bytes truncated)")
        return "\n".join(lines)

    def stop(self): self._running = False

# ── Main Window ───────────────────────────────────────────────────────────────
class WirelessAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Wireless Analyzer Pro")
        self.setMinimumSize(1200, 800)
        self.resize(1440, 900)
        self.setStyleSheet(STYLE)
        self.wifi_data = []; self.ble_data = []
        self.scan_count = 0
        self._all_packets = []; self._pkt_counter = 0
        self._pkt_stats = {k:0 for k in ["Mgmt","Ctrl","Data","Beacon",
                                           "Probe","Auth","Assoc","Deauth"]}
        self._sniffer_thread = None
        self._audit_findings = []
        self._build_ui()
        self._start_scanner()

    # ── UI shell ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_toolbar()
        central = QWidget(); self.setCentralWidget(central)
        layout  = QVBoxLayout(central)
        layout.setContentsMargins(8,8,8,8); layout.setSpacing(6)
        layout.addWidget(self._build_header())
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._build_wifi_tab()
        self._build_channel_tab()
        self._build_history_tab()
        self._build_ble_tab()
        self._build_sniffer_tab()
        self._build_security_tab()
        self._build_log_tab()
        sb = QStatusBar(); self.setStatusBar(sb)
        self.status_lbl  = QLabel("● IDLE")
        self.status_lbl.setStyleSheet("color:#8b949e; font-size:13px;")
        self.scan_info   = QLabel("")
        self.scan_info.setStyleSheet("color:#8b949e; font-size:13px;")
        sb.addWidget(self.status_lbl)
        sb.addPermanentWidget(self.scan_info)

    def _build_toolbar(self):
        tb = self.addToolBar("Main"); tb.setMovable(False)
        self.act_scan = QAction("▶  START SCAN", self)
        self.act_scan.setCheckable(True); self.act_scan.setChecked(True)
        self.act_scan.triggered.connect(self._toggle_scan)
        tb.addAction(self.act_scan); tb.addSeparator()
        for label, band in [("2.4 GHz","2.4GHz"),("5 GHz","5GHz"),("All Bands","all")]:
            a = QAction(label, self); a.triggered.connect(lambda _,b=band: self._set_band(b))
            tb.addAction(a)
        tb.addSeparator()
        tb.addWidget(QLabel("  Interval: "))
        self.interval_box = QComboBox()
        self.interval_box.addItems(["1s","2s","3s","5s","10s"])
        self.interval_box.setCurrentIndex(2)
        self.interval_box.setFixedWidth(80)
        self.interval_box.currentTextChanged.connect(
            lambda t: setattr(self.scanner, "interval", int(t.replace("s",""))))
        tb.addWidget(self.interval_box); tb.addSeparator()
        tb.addWidget(QLabel("  Filter SSID: "))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("type to filter…")
        self.filter_edit.setFixedWidth(180)
        self.filter_edit.textChanged.connect(self._apply_wifi_filter)
        tb.addWidget(self.filter_edit)
        sp = QWidget(); sp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(sp)
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet(
            "color:#00d4ff; font-family:Consolas; font-size:15px; font-weight:bold; padding:0 12px;")
        tb.addWidget(self.time_lbl)
        t = QTimer(self); t.timeout.connect(
            lambda: self.time_lbl.setText(datetime.now().strftime("%H:%M:%S")))
        t.start(1000); self.time_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    def _build_header(self):
        f = QFrame(); f.setFixedHeight(46)
        f.setStyleSheet("background:#161b22; border:1px solid #30363d; border-radius:4px;")
        lo = QHBoxLayout(f); lo.setContentsMargins(14,0,14,0)
        title = QLabel("⚡  WIRELESS ANALYZER PRO")
        title.setStyleSheet("color:#00d4ff; font-size:16px; font-weight:bold; letter-spacing:2px;")
        lo.addWidget(title); lo.addStretch()
        self.wifi_cnt = QLabel("WiFi: 0")
        self.wifi_cnt.setStyleSheet("color:#39ff14; font-size:14px; font-weight:bold; margin:0 14px;")
        self.ble_cnt  = QLabel("BLE: 0")
        self.ble_cnt.setStyleSheet("color:#a855f7; font-size:14px; font-weight:bold; margin:0 14px;")
        self.scan_lbl = QLabel("● SCANNING")
        self.scan_lbl.setStyleSheet("color:#39ff14; font-size:14px; font-weight:bold; margin:0 14px;")
        for w in [self.wifi_cnt, self.ble_cnt, self.scan_lbl]: lo.addWidget(w)
        self._pulse_on = True
        pt = QTimer(self); pt.timeout.connect(self._pulse); pt.start(600)
        return f

    def _pulse(self):
        self.scan_lbl.setStyleSheet(
            f"color:{'#39ff14' if self._pulse_on else '#0d5c1e'};"
            "font-size:14px; font-weight:bold; margin:0 14px;")
        self._pulse_on = not self._pulse_on

    # ── WiFi tab ──────────────────────────────────────────────────────────────
    def _build_wifi_tab(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(4,4,4,4)
        cols = ["SSID","BSSID","Band","Ch","Signal (dBm)","Level","SNR (dB)",
                "Encryption","Mode","Rate","Last Seen"]
        self.wifi_table = QTableWidget(0, len(cols))
        self.wifi_table.setHorizontalHeaderLabels(cols)
        self.wifi_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.wifi_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.wifi_table.setAlternatingRowColors(True)
        self.wifi_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.wifi_table.setSortingEnabled(True)
        self.wifi_table.verticalHeader().setVisible(False)
        for c,w2 in [(2,70),(3,45),(4,100),(5,110),(6,80),(7,160),(8,100),(9,110),(10,90)]:
            self.wifi_table.setColumnWidth(c, w2)
        lo.addWidget(self.wifi_table)
        self.tabs.addTab(w, "📡  WiFi Networks")

    # ── Channel tab ───────────────────────────────────────────────────────────
    def _build_channel_tab(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(4,4,4,4)
        brow = QHBoxLayout()
        brow.addWidget(QLabel("Band:"))
        self.ch_band = QComboBox(); self.ch_band.addItems(["2.4GHz","5GHz"])
        self.ch_band.currentTextChanged.connect(self._update_channel_chart)
        brow.addWidget(self.ch_band); brow.addStretch()
        lo.addLayout(brow)
        sp = QSplitter(Qt.Vertical)
        self.ch_overlap = ChannelOverlapWidget(); sp.addWidget(self.ch_overlap)
        cols = ["Channel","Networks","Interference","Best?"]
        self.chan_table = QTableWidget(0, len(cols))
        self.chan_table.setHorizontalHeaderLabels(cols)
        self.chan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chan_table.setMaximumHeight(160); sp.addWidget(self.chan_table)
        sp.setSizes([420,160]); lo.addWidget(sp)
        self.tabs.addTab(w, "📊  Channel Overlap")

    # ── History tab ───────────────────────────────────────────────────────────
    def _build_history_tab(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(4,4,4,4)
        row = QHBoxLayout(); row.addWidget(QLabel("Signal History  (last 60 s)"))
        row.addStretch()
        bc = QPushButton("Clear"); bc.setFixedWidth(90)
        bc.clicked.connect(lambda: self.sig_hist.clear())
        row.addWidget(bc); lo.addLayout(row)
        self.sig_hist = SignalHistoryWidget(); lo.addWidget(self.sig_hist)
        self.tabs.addTab(w, "📈  Signal History")

    # ── BLE tab ───────────────────────────────────────────────────────────────
    def _build_ble_tab(self):
        w = QWidget(); lo = QHBoxLayout(w); lo.setContentsMargins(4,4,4,4)
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0)
        cols = ["Name","Address","RSSI","Type","Services","Paired","Connected"]
        self.ble_table = QTableWidget(0, len(cols))
        self.ble_table.setHorizontalHeaderLabels(cols)
        self.ble_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ble_table.setAlternatingRowColors(True)
        self.ble_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ble_table.verticalHeader().setVisible(False)
        ll.addWidget(self.ble_table)
        lo.addWidget(left, 60)
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0)
        rl.addWidget(QLabel("BLE Radar"))
        self.ble_radar = BLERadarWidget(); rl.addWidget(self.ble_radar)
        lo.addWidget(right, 40)
        self.tabs.addTab(w, "🔵  Bluetooth LE")

    # ── Sniffer tab ───────────────────────────────────────────────────────────
    def _build_sniffer_tab(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(4,4,4,4); lo.setSpacing(4)
        ctrl = QHBoxLayout()
        self.sniff_iface = QComboBox(); self.sniff_iface.setFixedWidth(140)
        for ifc in self._get_ifaces(): self.sniff_iface.addItem(ifc)
        ctrl.addWidget(QLabel("Interface:")); ctrl.addWidget(self.sniff_iface)
        ctrl.addWidget(QLabel("  Filter:"))
        self.sniff_filt = QLineEdit(); self.sniff_filt.setPlaceholderText("MAC, type, SSID…")
        self.sniff_filt.setFixedWidth(200)
        self.sniff_filt.textChanged.connect(self._apply_pkt_filter)
        ctrl.addWidget(self.sniff_filt)
        ctrl.addWidget(QLabel("  Max:"))
        self.sniff_max = QSpinBox(); self.sniff_max.setRange(100,10000)
        self.sniff_max.setValue(1000); self.sniff_max.setSingleStep(100)
        self.sniff_max.setFixedWidth(90)
        ctrl.addWidget(self.sniff_max); ctrl.addStretch()
        self.pkt_cnt_lbl = QLabel("Packets: 0")
        self.pkt_cnt_lbl.setStyleSheet("color:#00d4ff; font-size:13px; font-weight:bold;")
        ctrl.addWidget(self.pkt_cnt_lbl)
        self.btn_sniff = QPushButton("▶  START CAPTURE")
        self.btn_sniff.setCheckable(True)
        self.btn_sniff.clicked.connect(self._toggle_sniffer)
        ctrl.addWidget(self.btn_sniff)
        btn_clr = QPushButton("Clear"); btn_clr.setFixedWidth(80)
        btn_clr.clicked.connect(self._clear_packets); ctrl.addWidget(btn_clr)
        lo.addLayout(ctrl)

        sp = QSplitter(Qt.Vertical)
        cols = ["#","Time","Source MAC","Dest MAC","Type","Subtype",
                "Chan","Signal","Size","Info"]
        self.pkt_table = QTableWidget(0, len(cols))
        self.pkt_table.setHorizontalHeaderLabels(cols)
        self.pkt_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)
        self.pkt_table.setAlternatingRowColors(True)
        self.pkt_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pkt_table.verticalHeader().setVisible(False)
        self.pkt_table.itemSelectionChanged.connect(self._on_pkt_selected)
        for c,cw in [(0,50),(1,100),(2,150),(3,150),(4,70),(5,120),(6,50),(7,80),(8,70)]:
            self.pkt_table.setColumnWidth(c, cw)
        sp.addWidget(self.pkt_table)

        detail = QSplitter(Qt.Horizontal)
        dL = QWidget(); dLL = QVBoxLayout(dL); dLL.setContentsMargins(0,0,0,0)
        dLL.addWidget(QLabel("  Frame Decode"))
        self.pkt_decode = QTextEdit(); self.pkt_decode.setReadOnly(True)
        dLL.addWidget(self.pkt_decode); detail.addWidget(dL)
        dR = QWidget(); dRL = QVBoxLayout(dR); dRL.setContentsMargins(0,0,0,0)
        dRL.addWidget(QLabel("  Hex Dump"))
        self.pkt_hex = QTextEdit(); self.pkt_hex.setReadOnly(True)
        dRL.addWidget(self.pkt_hex); detail.addWidget(dR)
        detail.setSizes([500,400]); sp.addWidget(detail)
        sp.setSizes([520,240]); lo.addWidget(sp)

        stat_row = QHBoxLayout()
        self.stat_lbls = {}
        for k in ["Mgmt","Ctrl","Data","Beacon","Probe","Auth","Assoc","Deauth"]:
            lbl = QLabel(f"{k}: 0")
            lbl.setStyleSheet("color:#6e7681; font-size:12px; margin:0 6px;")
            stat_row.addWidget(lbl); self.stat_lbls[k] = lbl
        stat_row.addStretch(); lo.addLayout(stat_row)
        self.tabs.addTab(w, "🦈  Packet Sniffer")

    def _get_ifaces(self):
        ifaces = []
        try:
            out = subprocess.check_output(["iwconfig"],stderr=subprocess.STDOUT,
                                           timeout=4).decode(errors="ignore")
            for line in out.splitlines():
                if line and not line.startswith(" "):
                    ifaces.append(line.split()[0])
        except: pass
        if not ifaces:
            try:
                out = subprocess.check_output(["ip","link"],stderr=subprocess.DEVNULL,
                                               timeout=4).decode(errors="ignore")
                for line in out.splitlines():
                    m = re.match(r"\d+: (\w+):", line)
                    if m and m.group(1) != "lo": ifaces.append(m.group(1))
            except: pass
        return ifaces or ["wlan0","en0","eth0"]

    # ── Security tab ──────────────────────────────────────────────────────────
    def _build_security_tab(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(4,4,4,4)
        banner = QLabel("⚠  SECURITY AUDIT — Only use on networks you own or have explicit written permission to test.")
        banner.setStyleSheet(
            "background:#2a1800; color:#ffd700; border:1px solid #ff6b35;"
            "padding:8px 12px; border-radius:4px; font-weight:bold; font-size:13px;")
        banner.setWordWrap(True); lo.addWidget(banner)
        ctrl = QHBoxLayout(); ctrl.addWidget(QLabel("Target:"))
        self.sec_target = QComboBox(); self.sec_target.setFixedWidth(240)
        self.sec_target.addItem("All visible networks")
        ctrl.addWidget(self.sec_target); ctrl.addStretch()
        self.btn_audit = QPushButton("🔍  RUN AUDIT")
        self.btn_audit.setFixedWidth(160)
        self.btn_audit.clicked.connect(self._run_audit)
        ctrl.addWidget(self.btn_audit); lo.addLayout(ctrl)

        hs = QSplitter(Qt.Horizontal)
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0)
        ll.addWidget(QLabel("  Findings"))
        cols = ["Severity","SSID","BSSID","Issue","Recommendation"]
        self.sec_table = QTableWidget(0, len(cols))
        self.sec_table.setHorizontalHeaderLabels(cols)
        self.sec_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.sec_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.sec_table.setAlternatingRowColors(True)
        self.sec_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sec_table.verticalHeader().setVisible(False)
        self.sec_table.itemSelectionChanged.connect(self._on_finding_selected)
        ll.addWidget(self.sec_table); hs.addWidget(left)

        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(4,0,0,0)
        self.score_widget = AuditScoreWidget()
        self.score_widget.setFixedHeight(160); rl.addWidget(self.score_widget)
        rl.addWidget(QLabel("  Detail"))
        self.sec_detail = QTextEdit(); self.sec_detail.setReadOnly(True)
        rl.addWidget(self.sec_detail); hs.addWidget(right)
        hs.setSizes([720,360]); lo.addWidget(hs)

        sum_row = QHBoxLayout()
        self.sev_lbls = {}
        for sev, clr in [("CRITICAL","#ff2d78"),("HIGH","#ff6b35"),
                          ("MEDIUM","#ffd700"),("LOW","#39ff14"),("INFO","#00d4ff")]:
            lbl = QLabel(f"{sev}: 0")
            lbl.setStyleSheet(f"color:{clr}; font-weight:bold; font-size:13px; margin:0 10px;")
            sum_row.addWidget(lbl); self.sev_lbls[sev] = lbl
        sum_row.addStretch(); lo.addLayout(sum_row)
        self.tabs.addTab(w, "🔒  Security Audit")

    # ── Log tab ───────────────────────────────────────────────────────────────
    def _build_log_tab(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(4,4,4,4)
        ctrl = QHBoxLayout(); ctrl.addWidget(QLabel("Scanner Log")); ctrl.addStretch()
        bc = QPushButton("Clear"); bc.setFixedWidth(90)
        bc.clicked.connect(lambda: self.log_text.clear())
        ctrl.addWidget(bc); lo.addLayout(ctrl)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True)
        lo.addWidget(self.log_text)
        self.tabs.addTab(w, "📋  Log")

    # ── Scanner ───────────────────────────────────────────────────────────────
    def _start_scanner(self):
        self.scanner = ScannerThread(interval=3)
        self.scanner.wifi_result.connect(self._on_wifi)
        self.scanner.ble_result.connect(self._on_ble)
        self.scanner.log_message.connect(self._on_log)
        self.scanner.start()

    def _toggle_scan(self, checked):
        if checked:
            self.act_scan.setText("▶  SCANNING")
            self._start_scanner()
        else:
            self.act_scan.setText("▶  START SCAN")
            self.scan_lbl.setText("● IDLE")
            self.scan_lbl.setStyleSheet(
                "color:#6e7681; font-size:14px; font-weight:bold; margin:0 14px;")
            if hasattr(self,"scanner"): self.scanner.stop()

    def _set_band(self, band):
        self._band = band; self._update_channel_chart()

    def _apply_wifi_filter(self, text):
        filt = text.lower()
        for row in range(self.wifi_table.rowCount()):
            item = self.wifi_table.item(row, 0)
            hide = bool(filt and filt not in (item.text().lower() if item else ""))
            self.wifi_table.setRowHidden(row, hide)

    # ── Data callbacks ────────────────────────────────────────────────────────
    def _on_wifi(self, nets):
        self.wifi_data = nets; self.scan_count += 1
        self.wifi_cnt.setText(f"WiFi: {len(nets)}")
        self._refresh_wifi_table(nets)
        self._update_channel_chart()
        for n in nets[:10]:
            self.sig_hist.addSample(n.get("ssid","?"), n.get("signal",-70))
        self.sec_target.clear()
        self.sec_target.addItem("All visible networks")
        for n in nets: self.sec_target.addItem(n.get("ssid","?"))
        self.scan_info.setText(
            f"Scan #{self.scan_count} @ {datetime.now().strftime('%H:%M:%S')}")

    def _on_ble(self, devs):
        self.ble_data = devs
        self.ble_cnt.setText(f"BLE: {len(devs)}")
        self._refresh_ble_table(devs)
        self.ble_radar.setDevices(devs)

    def _on_log(self, msg):
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # ── Refresh tables ────────────────────────────────────────────────────────
    def _refresh_wifi_table(self, nets):
        self.wifi_table.setSortingEnabled(False)
        self.wifi_table.setRowCount(len(nets))
        filt = self.filter_edit.text().lower()
        for row, net in enumerate(nets):
            ssid    = net.get("ssid",    "?")
            bssid   = net.get("bssid",   "?")
            band    = net.get("band",    "?")
            channel = str(net.get("channel", "?"))
            sig     = net.get("signal",  -100)
            snr     = net.get("snr",     0)
            sec     = net.get("security","?")
            mode    = net.get("mode",    "?")
            rate    = net.get("rate",    "?")
            ts      = datetime.now().strftime("%H:%M:%S")

            vals = [ssid, bssid, band, channel, str(sig), None,
                    str(snr), sec, mode, rate, ts]
            for col, val in enumerate(vals):
                if col == 5:
                    bar = SignalBar(sig)
                    self.wifi_table.setCellWidget(row, col, bar)
                    continue
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if col == 4:   # signal dBm
                    item.setForeground(
                        QColor("#39ff14") if sig>=-50 else
                        QColor("#ffd700") if sig>=-65 else
                        QColor("#ff6b35") if sig>=-75 else QColor("#ff2d78"))
                if col == 7:   # encryption
                    item.setForeground(
                        QColor("#39ff14") if "WPA3" in sec else
                        ACCENT_CYAN       if "WPA2" in sec else
                        QColor("#ffd700") if "WPA"  in sec else
                        QColor("#ff2d78") if "OPEN" in sec.upper() else TEXT_PRIMARY)
                if col == 2:   # band
                    item.setForeground(ACCENT_PURPLE if "5" in band else ACCENT_CYAN)
                self.wifi_table.setItem(row, col, item)

            self.wifi_table.setRowHeight(row, 30)
            hide = bool(filt and filt not in ssid.lower())
            self.wifi_table.setRowHidden(row, hide)
        self.wifi_table.setSortingEnabled(True)

    def _refresh_ble_table(self, devs):
        self.ble_table.setRowCount(len(devs))
        for row, dev in enumerate(devs):
            rssi = dev.get("rssi", -70)
            vals = [dev.get("name","?"), dev.get("address","?"),
                    str(rssi), dev.get("type","BLE"),
                    str(dev.get("services",0)),
                    "✓" if dev.get("paired")    else "✗",
                    "✓" if dev.get("connected") else "✗"]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if col == 2:
                    item.setForeground(
                        QColor("#39ff14") if rssi>=-55 else
                        QColor("#ffd700") if rssi>=-70 else QColor("#ff6b35"))
                if col == 6:
                    item.setForeground(QColor("#39ff14") if val=="✓" else TEXT_DIM)
                self.ble_table.setItem(row, col, item)
            self.ble_table.setRowHeight(row, 30)

    # ── Channel chart ─────────────────────────────────────────────────────────
    def _update_channel_chart(self):
        band = self.ch_band.currentText()
        self.ch_overlap.setNetworks(self.wifi_data, band)
        chan_count = defaultdict(list)
        for n in self.wifi_data:
            if n.get("band","2.4GHz") == band:
                ch  = n.get("channel", None)
                sig = n.get("signal", -100)
                if ch is not None:
                    chan_count[ch].append(sig)
        non_overlap = [1,6,11] if band=="2.4GHz" else [36,44,149,157]
        all_ch = list(range(1,14)) if band=="2.4GHz" else \
                 [36,40,44,48,52,56,60,64,100,149,153,157,161]
        best = min(all_ch, key=lambda c: len(chan_count.get(c,[])), default=6)
        self.chan_table.setRowCount(len(chan_count))
        for row,(ch,sigs) in enumerate(sorted(chan_count.items())):
            n = len(sigs)
            inter = "HIGH" if n>=4 else "MEDIUM" if n>=2 else "LOW"
            iclr  = (QColor("#ff2d78") if inter=="HIGH" else
                     QColor("#ffd700") if inter=="MEDIUM" else QColor("#39ff14"))
            for col,val in enumerate([str(ch),str(n),inter,
                                       "★ Best" if ch==best else ""]):
                item = QTableWidgetItem(val)
                if col==2: item.setForeground(iclr)
                if col==3 and val: item.setForeground(QColor("#39ff14"))
                self.chan_table.setItem(row,col,item)
            self.chan_table.setRowHeight(row,30)

    # ── Sniffer controls ──────────────────────────────────────────────────────
    def _toggle_sniffer(self, checked):
        if checked:
            self.btn_sniff.setText("■  STOP CAPTURE")
            self.btn_sniff.setStyleSheet(
                "background:#3a0000; color:#ff2d78; border:1px solid #ff2d78;"
                "padding:8px 18px; border-radius:4px; font-weight:bold; font-size:13px;")
            self._sniffer_thread = PacketSnifferThread(
                self.sniff_iface.currentText(), self.sniff_max.value())
            self._sniffer_thread.packet_captured.connect(self._on_pkt)
            self._sniffer_thread.sniffer_log.connect(self._on_log)
            self._sniffer_thread.start()
        else:
            self.btn_sniff.setText("▶  START CAPTURE")
            self.btn_sniff.setStyleSheet("")
            if self._sniffer_thread:
                self._sniffer_thread.stop(); self._sniffer_thread.wait(2000)
                self._sniffer_thread = None

    def _clear_packets(self):
        self._all_packets.clear(); self._pkt_counter = 0
        self._pkt_stats = {k:0 for k in self._pkt_stats}
        self.pkt_table.setRowCount(0)
        self.pkt_decode.clear(); self.pkt_hex.clear()
        self.pkt_cnt_lbl.setText("Packets: 0")
        for k,l in self.stat_lbls.items(): l.setText(f"{k}: 0")

    def _on_pkt(self, pkt):
        if self._pkt_counter >= self.sniff_max.value():
            self.btn_sniff.setChecked(False); self._toggle_sniffer(False); return
        self._pkt_counter += 1
        self._all_packets.append(pkt)
        sub = pkt.get("subtype","").lower()
        pt  = pkt.get("type","").lower()
        for k in ["Mgmt","Ctrl","Data","Beacon","Probe","Auth","Assoc","Deauth"]:
            if k.lower() in pt or k.lower() in sub:
                self._pkt_stats[k] += 1
        for k,l in self.stat_lbls.items(): l.setText(f"{k}: {self._pkt_stats[k]}")
        self.pkt_cnt_lbl.setText(f"Packets: {self._pkt_counter}")
        self._insert_pkt_row(pkt)
        self.pkt_table.scrollToBottom()

    def _insert_pkt_row(self, pkt):
        filt = self.sniff_filt.text().lower()
        if filt:
            combined = " ".join(str(pkt.get(k,"")) for k in
                                ["src","dst","type","subtype","info"]).lower()
            if filt not in combined: return
        row = self.pkt_table.rowCount()
        self.pkt_table.insertRow(row)
        self.pkt_table.setRowHeight(row, 30)
        sub = pkt.get("subtype","").lower()
        bg = (QColor("#1a3a1a") if "beacon"  in sub else
              QColor("#1a2a3a") if "probe"   in sub else
              QColor("#2a1a3a") if "auth"    in sub or "assoc" in sub else
              QColor("#3a1a1a") if "deauth"  in sub or "disassoc" in sub else
              QColor("#1a1f2a") if "data"    in pkt.get("type","").lower() else
              BG_PANEL)
        vals = [str(pkt.get("num",0)), pkt.get("time",""),
                pkt.get("src",""), pkt.get("dst",""),
                pkt.get("type",""), pkt.get("subtype",""),
                str(pkt.get("channel","?")), str(pkt.get("signal","?")),
                str(pkt.get("size",0)), pkt.get("info","")]
        for col, val in enumerate(vals):
            item = QTableWidgetItem(val)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setBackground(QBrush(bg))
            t = pkt.get("type","").lower(); s = pkt.get("subtype","").lower()
            if col==4:
                item.setForeground(QColor("#ffd700") if "mgmt" in t else
                                   ACCENT_CYAN       if "data" in t else
                                   ACCENT_PURPLE     if "ctrl" in t else TEXT_PRIMARY)
            if col==5:
                item.setForeground(
                    QColor("#39ff14") if "beacon"  in s else
                    QColor("#ff2d78") if "deauth"  in s or "disassoc" in s else
                    QColor("#ff6b35") if "auth"    in s else
                    ACCENT_CYAN       if "probe"   in s else TEXT_PRIMARY)
            if col==7:
                try:
                    sv = int(val)
                    item.setForeground(QColor("#39ff14") if sv>=-55 else
                                       QColor("#ffd700") if sv>=-70 else
                                       QColor("#ff6b35"))
                except ValueError: pass
            if col==0: item.setData(Qt.UserRole, len(self._all_packets)-1)
            self.pkt_table.setItem(row, col, item)

    def _apply_pkt_filter(self, text):
        filt = text.lower()
        for row in range(self.pkt_table.rowCount()):
            items = [self.pkt_table.item(row,c)
                     for c in range(self.pkt_table.columnCount())]
            txt = " ".join(i.text().lower() for i in items if i)
            self.pkt_table.setRowHidden(row, bool(filt and filt not in txt))

    def _on_pkt_selected(self):
        row = self.pkt_table.currentRow()
        item = self.pkt_table.item(row, 0) if row >= 0 else None
        if item is None: return
        idx = item.data(Qt.UserRole)
        if idx is not None and idx < len(self._all_packets):
            pkt = self._all_packets[idx]
            self.pkt_decode.setPlainText(pkt.get("decode",""))
            self.pkt_hex.setPlainText(pkt.get("hexdump",""))

    # ── Security audit ────────────────────────────────────────────────────────
    def _run_audit(self):
        target = self.sec_target.currentText()
        nets = self.wifi_data if target=="All visible networks" else \
               [n for n in self.wifi_data if n.get("ssid")==target]
        findings = []
        for n in nets: findings.extend(self._audit_net(n))
        ch_cnt = defaultdict(int)
        for n in self.wifi_data: ch_cnt[n.get("channel",0)] += 1
        for ch,cnt in ch_cnt.items():
            if cnt >= 4:
                findings.append({
                    "severity":"MEDIUM","ssid":"[Channel]","bssid":"—",
                    "issue":f"Channel {ch} has {cnt} overlapping networks",
                    "recommendation":"Use a less congested channel.",
                    "detail":f"Channel {ch} is used by {cnt} networks causing co-channel interference.",
                })
        sev_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}
        findings.sort(key=lambda f: sev_order.get(f.get("severity","INFO"),5))
        self._audit_findings = findings
        self.sec_table.setRowCount(len(findings))
        counts = {s:0 for s in sev_order}
        SEV_CLR = {"CRITICAL":"#ff2d78","HIGH":"#ff6b35",
                   "MEDIUM":"#ffd700","LOW":"#39ff14","INFO":"#00d4ff"}
        for row, f in enumerate(findings):
            sev = f.get("severity","INFO"); counts[sev] = counts.get(sev,0)+1
            for col,val in enumerate([sev,f.get("ssid",""),f.get("bssid",""),
                                       f.get("issue",""),f.get("recommendation","")]):
                item = QTableWidgetItem(val)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if col==0:
                    item.setForeground(QColor(SEV_CLR.get(sev,"#e6edf3")))
                    item.setFont(QFont("Consolas",12,QFont.Bold))
                self.sec_table.setItem(row,col,item)
            self.sec_table.setRowHeight(row,30)
        for sev,lbl in self.sev_lbls.items(): lbl.setText(f"{sev}: {counts.get(sev,0)}")
        score = max(0, min(100, 100 - sum(
            {"CRITICAL":25,"HIGH":15,"MEDIUM":8,"LOW":3,"INFO":0}.get(f.get("severity","INFO"),0)
            for f in findings)))
        self.score_widget.setScore(score, len(findings))
        self._on_log(f"[Audit] {len(findings)} findings, score {score}/100")

    def _audit_net(self, net):
        findings = []
        ssid = net.get("ssid","?"); bssid = net.get("bssid","?")
        sec  = net.get("security","?").upper(); sig = net.get("signal",-100)
        SEV_CLR = {"CRITICAL":"#ff2d78","HIGH":"#ff6b35",
                   "MEDIUM":"#ffd700","LOW":"#39ff14","INFO":"#00d4ff"}
        def add(severity, issue, rec, detail):
            findings.append({"severity":severity,"ssid":ssid,"bssid":bssid,
                              "issue":issue,"recommendation":rec,"detail":detail})
        if "OPEN" in sec or sec in ("NONE","","—"):
            add("CRITICAL","Open network — no encryption",
                "Enable WPA3 or WPA2-AES immediately.",
                f"'{ssid}' transmits all traffic in plaintext. Anyone within range "
                "can capture credentials, session tokens and private data with freely "
                "available tools (Wireshark, tcpdump).")
        if "WEP" in sec:
            add("CRITICAL","WEP encryption — cryptographically broken",
                "Replace with WPA3 or WPA2-AES immediately.",
                "WEP was deprecated in 2004. Its RC4 IV reuse allows key recovery "
                "from ~50 000 captured packets. CVSS 9.8.")
        if "WPA" in sec and "WPA2" not in sec and "WPA3" not in sec:
            add("HIGH","WPA-TKIP — vulnerable to Beck-Tews / TKIP MIC attacks",
                "Upgrade to WPA2-AES or WPA3.",
                "TKIP was deprecated in 802.11-2012. Partial plaintext recovery "
                "possible in under 15 minutes.")
        if "WPA2" in sec and "WPA3" not in sec:
            add("LOW","WPA2-PSK — offline PMKID/dictionary attack possible",
                "Use 20+ char random passphrase or upgrade to WPA3-SAE.",
                "Jens Steube (2018) showed PMKID can be captured without a full "
                "handshake and attacked offline. WPA3-SAE prevents this via the "
                "Dragonfly handshake.")
        if "WPA3" in sec:
            add("INFO","WPA3 detected — strong security",
                "Verify PMF (802.11w) is set to Required, not Optional.",
                f"'{ssid}' uses WPA3-SAE providing forward secrecy and resistance "
                "to offline dictionary attacks.")
        if any(c in ssid.lower() for c in
               ["linksys","netgear","default","dlink","tp-link","asus","belkin"]):
            add("LOW","Default/generic SSID name",
                "Rename and verify admin password is not factory default.",
                "Default SSIDs indicate possible default credentials still in use.")
        if sig < -85:
            add("INFO",f"Weak signal ({sig} dBm) — possible rogue AP",
                "Verify this BSSID against known AP inventory.",
                "Very weak signals from unknown BSSIDs may indicate evil-twin APs.")
        if not ssid or ssid == "<hidden>":
            add("INFO","Hidden SSID — security through obscurity",
                "SSID is revealed in probe requests; use strong encryption instead.",
                "Hidden SSIDs provide no real protection and cause connectivity issues.")
        return findings

    def _on_finding_selected(self):
        row = self.sec_table.currentRow()
        if row < 0 or row >= len(self._audit_findings): return
        f = self._audit_findings[row]
        SEV_CLR = {"CRITICAL":"#ff2d78","HIGH":"#ff6b35",
                   "MEDIUM":"#ffd700","LOW":"#39ff14","INFO":"#00d4ff"}
        self.sec_detail.setPlainText(
            f"{'═'*56}\n"
            f"  SEVERITY      : {f.get('severity','?')}\n"
            f"  NETWORK (SSID): {f.get('ssid','?')}\n"
            f"  BSSID         : {f.get('bssid','?')}\n"
            f"{'─'*56}\n\n"
            f"ISSUE\n{f.get('issue','')}\n\n"
            f"TECHNICAL DETAIL\n{f.get('detail','')}\n\n"
            f"RECOMMENDATION\n{f.get('recommendation','')}\n"
            f"{'═'*56}"
        )

    # ── Cleanup ───────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        if hasattr(self,"scanner"): self.scanner.stop(); self.scanner.wait(2000)
        if self._sniffer_thread:
            self._sniffer_thread.stop(); self._sniffer_thread.wait(2000)
        event.accept()

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Wireless Analyzer Pro")
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window,           QColor("#0d1117"))
    pal.setColor(QPalette.WindowText,       QColor("#e6edf3"))
    pal.setColor(QPalette.Base,             QColor("#161b22"))
    pal.setColor(QPalette.AlternateBase,    QColor("#1c2230"))
    pal.setColor(QPalette.Text,             QColor("#e6edf3"))
    pal.setColor(QPalette.Button,           QColor("#1c2230"))
    pal.setColor(QPalette.ButtonText,       QColor("#e6edf3"))
    pal.setColor(QPalette.Highlight,        QColor("#1f3a5f"))
    pal.setColor(QPalette.HighlightedText,  QColor("#00d4ff"))
    app.setPalette(pal)
    win = WirelessAnalyzer()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
