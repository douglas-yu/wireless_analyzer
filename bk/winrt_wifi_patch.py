"""
Drop-in WinRT Wi-Fi patch for wireless_analyzer_v5.py.

Purpose
- Replaces the Windows Wi-Fi scan path so it uses Windows.Devices.WiFi
  instead of parsing `netsh wlan show networks` output.
- Preserves the original scanner behavior on non-Windows platforms.

How to use
1) Install dependency on Windows:
       pip install winsdk
2) Put this file next to wireless_analyzer_v5.py
3) In wireless_analyzer_v5.py add:
       from winrt_wifi_patch import apply_winrt_patch
4) After ScannerThread is defined, add:
       apply_winrt_patch(ScannerThread)
5) Run the app on Windows.

Notes
- Windows may require Location to be enabled for Wi-Fi scanning APIs.
- This patch bypasses netsh only for Windows. Linux/macOS keep the old path.
"""

from __future__ import annotations

import asyncio
import math
import platform
from typing import Any, Dict, Iterable, List, Tuple


_ORIGINAL_SCAN_WIFI = None


def apply_winrt_patch(scanner_cls):
    """
    Monkey-patch scanner_cls._scan_wifi so Windows uses WinRT.

    Example:
        from winrt_wifi_patch import apply_winrt_patch
        apply_winrt_patch(ScannerThread)
    """
    global _ORIGINAL_SCAN_WIFI

    if getattr(scanner_cls, "_winrt_patch_applied", False):
        return scanner_cls

    if not hasattr(scanner_cls, "_scan_wifi"):
        raise AttributeError("ScannerThread is missing _scan_wifi")

    _ORIGINAL_SCAN_WIFI = scanner_cls._scan_wifi

    def _patched_scan_wifi(self, *args, **kwargs):
        system = platform.system().lower()
        if system == "windows":
            return _run_async(_scan_wifi_windows_winrt(self))
        return _ORIGINAL_SCAN_WIFI(self, *args, **kwargs)

    scanner_cls._scan_wifi = _patched_scan_wifi
    scanner_cls._scan_wifi_windows_winrt = _scan_wifi_windows_winrt
    scanner_cls._winrt_patch_applied = True
    return scanner_cls


async def _scan_wifi_windows_winrt(self) -> List[Dict[str, Any]]:
    try:
        from winsdk.windows.devices.wifi import WiFiAdapter
    except Exception as e:
        raise RuntimeError(
            "WinRT Wi-Fi scanning requires the `winsdk` package. "
            "Install it with: pip install winsdk"
        ) from e

    access = await WiFiAdapter.request_access_async()
    access_name = _enum_tail(access).lower()
    if access_name not in {"allowed", "1"}:
        raise RuntimeError(
            "Windows.Devices.WiFi access was not allowed. "
            "Enable Location in Windows settings and allow desktop apps to access it. "
            f"Access status: {access_name or access}"
        )

    adapters = await WiFiAdapter.find_all_adapters_async()
    adapters = list(adapters)
    if not adapters:
        raise RuntimeError(
            "No Wi-Fi adapters were returned by Windows.Devices.WiFi. "
            "Make sure the system has a supported Wi-Fi adapter and Location is enabled."
        )

    results: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, int]] = set()

    for adapter in adapters:
        try:
            await adapter.scan_async()
        except Exception:
            continue

        report = getattr(adapter, "network_report", None)
        if report is None:
            continue

        networks = list(getattr(report, "available_networks", []) or [])
        for net in networks:
            row = _network_to_row(net)
            dedupe_key = (
                str(row.get("ssid", "")),
                str(row.get("bssid", "")),
                int(row.get("channel", 0) or 0),
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            results.append(row)

    results.sort(
        key=lambda r: (
            -int(r.get("signal_percent", 0) or 0),
            str(r.get("ssid", "")),
            str(r.get("bssid", "")),
        )
    )
    return results


def _network_to_row(net) -> Dict[str, Any]:
    ssid = _clean(getattr(net, "ssid", ""))
    bssid = _clean(getattr(net, "bssid", ""))

    freq_khz = getattr(net, "channel_center_frequency_in_kilohertz", 0) or 0
    freq_mhz = int(round(freq_khz / 1000)) if freq_khz else 0
    channel = _frequency_to_channel(freq_mhz)
    band = _band_from_frequency(freq_mhz)

    rssi_dbm = getattr(net, "network_rssi_in_decibel_milliwatts", None)
    try:
        rssi_dbm = int(rssi_dbm) if rssi_dbm is not None else None
    except Exception:
        rssi_dbm = None

    signal_bars = getattr(net, "signal_bars", None)
    signal_percent = _bars_or_rssi_to_percent(signal_bars, rssi_dbm)

    phy = _enum_tail(getattr(net, "phy_kind", ""))
    sec = getattr(net, "security_settings", None)
    auth = _enum_tail(getattr(sec, "network_authentication_type", "")) if sec else ""
    enc = _enum_tail(getattr(sec, "network_encryption_type", "")) if sec else ""
    security = _security_string(auth, enc)

    # Wide alias set for compatibility with different table models.
    row = {
        "ssid": ssid,
        "bssid": bssid,
        "channel": channel,
        "frequency_mhz": freq_mhz,
        "band": band,
        "rssi_dbm": rssi_dbm,
        "signal_percent": signal_percent,
        "security": security,
        "authentication": auth,
        "encryption": enc,
        "phy": phy,
        "radio_type": phy,
        "source": "winrt",
        "SSID": ssid,
        "BSSID": bssid,
        "Channel": channel,
        "FrequencyMHz": freq_mhz,
        "Band": band,
        "RSSI": rssi_dbm,
        "Signal": signal_percent,
        "SignalPercent": signal_percent,
        "SignalDBM": rssi_dbm,
        "Security": security,
        "Authentication": auth,
        "Encryption": enc,
        "Phy": phy,
        "RadioType": phy,
        "Source": "winrt",
    }
    return row


def _bars_or_rssi_to_percent(signal_bars, rssi_dbm: int | None) -> int:
    try:
        bars = int(signal_bars)
        if 0 <= bars <= 4:
            return int(round((bars / 4.0) * 100))
    except Exception:
        pass

    if rssi_dbm is None:
        return 0

    # Clamp common Wi-Fi RSSI range [-100, -50] into [0, 100]
    pct = 2 * (rssi_dbm + 100)
    return max(0, min(100, int(round(pct))))


def _band_from_frequency(freq_mhz: int) -> str:
    if 2400 <= freq_mhz <= 2500:
        return "2.4 GHz"
    if 4900 <= freq_mhz <= 5900:
        return "5 GHz"
    if 5925 <= freq_mhz <= 7125:
        return "6 GHz"
    return "Unknown"


def _frequency_to_channel(freq_mhz: int) -> int:
    if freq_mhz == 2484:
        return 14
    if 2412 <= freq_mhz <= 2472:
        return (freq_mhz - 2407) // 5
    if 5000 <= freq_mhz <= 5895:
        return (freq_mhz - 5000) // 5
    if 5955 <= freq_mhz <= 7115:
        return (freq_mhz - 5950) // 5
    return 0


def _security_string(auth: str, enc: str) -> str:
    a = (auth or "").strip()
    e = (enc or "").strip()
    if not a and not e:
        return "Unknown"
    if a.lower().startswith("open") and (not e or e.lower().startswith("none")):
        return "Open"
    if a and e:
        return f"{a} / {e}"
    return a or e


def _enum_tail(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if "." in text:
        text = text.split(".")[-1]
    if ":" in text:
        text = text.split(":")[-1]
    return text.strip()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _run_async(coro):
    try:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            asyncio.set_event_loop(None)
            loop.close()
    except Exception:
        return asyncio.run(coro)
