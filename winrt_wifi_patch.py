"""
WinRT Wi-Fi patch for wireless_analyzer_v5.py.

What this fixes
- Replaces Windows Wi-Fi scanning with Windows.Devices.WiFi
- Emits fields in the exact shape expected by wireless_analyzer_v5.py:
  ssid, bssid, band, channel, signal, snr, security, mode, rate
- Uses exact band labels required by the channel-overlap widget:
  2.4GHz / 5GHz / 6GHz
- Normalizes security strings so the table coloring logic works better
- Maps WinRT PHY kind to human-readable 802.11 mode labels
- Provides a best-effort estimated PHY rate string instead of '?'

How to use
1) pip install winsdk
2) Put this file next to wireless_analyzer_v5.py
3) In wireless_analyzer_v5.py add:
       from winrt_wifi_patch import apply_winrt_patch
4) After ScannerThread is defined, add:
       apply_winrt_patch(ScannerThread)
5) Run on Windows with Location enabled
"""

from __future__ import annotations

import asyncio
import platform
from typing import Any, Dict, Iterable, List, Optional, Tuple

_ORIGINAL_SCAN_WIFI = None


def apply_winrt_patch(scanner_cls):
    global _ORIGINAL_SCAN_WIFI

    if getattr(scanner_cls, "_winrt_patch_applied", False):
        return scanner_cls

    if not hasattr(scanner_cls, "_scan_wifi"):
        raise AttributeError("ScannerThread is missing _scan_wifi")

    _ORIGINAL_SCAN_WIFI = scanner_cls._scan_wifi

    def _patched_scan_wifi(self, *args, **kwargs):
        if platform.system().lower() != "windows":
            return _ORIGINAL_SCAN_WIFI(self, *args, **kwargs)
        return _run_async(_scan_wifi_windows_winrt(self))

    scanner_cls._scan_wifi = _patched_scan_wifi
    scanner_cls._scan_wifi_windows_winrt = _scan_wifi_windows_winrt
    scanner_cls._winrt_patch_applied = True
    return scanner_cls


async def _scan_wifi_windows_winrt(self) -> List[Dict[str, Any]]:
    try:
        from winsdk.windows.devices.wifi import WiFiAdapter
    except Exception as e:
        raise RuntimeError(
            "WinRT Wi-Fi scanning requires the winsdk package. Install it with: pip install winsdk"
        ) from e

    access = await WiFiAdapter.request_access_async()
    access_name = _enum_tail(access).lower()
    if access_name not in {"allowed", "1"}:
        raise RuntimeError(
            "Windows.Devices.WiFi access was not allowed. Enable Windows Location and allow desktop apps to access location. "
            f"Access status: {access_name or access}"
        )

    adapters = list(await WiFiAdapter.find_all_adapters_async())
    if not adapters:
        raise RuntimeError("No Wi-Fi adapters were returned by Windows.Devices.WiFi")

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
            if not row:
                continue
            key = (
                str(row.get("ssid", "")),
                str(row.get("bssid", "")),
                int(row.get("channel", 0) or 0),
            )
            if key in seen:
                continue
            seen.add(key)
            results.append(row)

    results.sort(
        key=lambda r: (
            -int(r.get("signal", -100) or -100),
            str(r.get("ssid", "")).lower(),
            str(r.get("bssid", "")).lower(),
        ),
        reverse=True,
    )

    try:
        self.log_message.emit(f"[WiFi] WinRT: {len(results)} networks")
    except Exception:
        pass

    return results


def _network_to_row(net) -> Dict[str, Any]:
    ssid = _clean(_get_any_attr(net, "ssid", "SSID")) or "<hidden>"
    bssid = _clean(_get_any_attr(net, "bssid", "BSSID")).upper()

    freq_khz = _to_int(_get_any_attr(
        net,
        "channel_center_frequency_in_kilohertz",
        "channelCenterFrequencyInKilohertz",
        default=0,
    ), 0)
    freq_mhz = int(round(freq_khz / 1000.0)) if freq_khz else 0

    channel = _frequency_to_channel(freq_mhz)
    band = _band_from_frequency(freq_mhz, channel)

    rssi = _to_int(_get_any_attr(
        net,
        "network_rssi_in_decibel_milliwatts",
        "networkRssiInDecibelMilliwatts",
        "rssi",
        "RSSI",
        default=None,
    ), None)

    signal_bars = _to_int(_get_any_attr(net, "signal_bars", "signalBars", default=None), None)

    if rssi is None:
        rssi = _bars_to_rssi(signal_bars)
    if rssi is None:
        rssi = -100

    signal_percent = _rssi_to_percent(rssi, signal_bars)

    phy = _enum_tail(_get_any_attr(net, "phy_kind", "phyKind", default=""))
    mode = _phy_to_mode(phy, band)
    rate = _estimate_rate(mode, band)

    sec = _get_any_attr(net, "security_settings", "securitySettings", default=None)
    auth = _enum_tail(_get_any_attr(sec, "network_authentication_type", "networkAuthenticationType", default="")) if sec else ""
    enc = _enum_tail(_get_any_attr(sec, "network_encryption_type", "networkEncryptionType", default="")) if sec else ""
    security = _security_string(auth, enc)

    snr = _extract_snr(net, rssi, band)

    return {
        "ssid": ssid,
        "bssid": bssid,
        "band": band,
        "channel": channel,
        "signal": int(rssi),
        "snr": int(snr),
        "security": security,
        "mode": mode,
        "rate": rate,
        "signal_percent": int(signal_percent),
        "frequency_mhz": freq_mhz,
        "authentication": auth,
        "encryption": enc,
        "phy": phy,
        "source": "winrt",
    }


def _get_any_attr(obj, *names, default=None):
    if obj is None:
        return default
    for name in names:
        try:
            if hasattr(obj, name):
                return getattr(obj, name)
        except Exception:
            pass
    return default


def _extract_snr(net, rssi: int, band: str) -> int:
    direct = _to_int(_get_any_attr(
        net,
        "snr",
        "SNR",
        "signal_noise_ratio_in_decibels",
        "signalNoiseRatioInDecibels",
        "network_snr_in_decibels",
        "networkSnrInDecibels",
        default=None,
    ), None)
    if direct is not None and direct >= 0:
        return direct

    noise_floor = -95 if band == "2.4GHz" else -98 if band == "5GHz" else -96
    return max(0, min(60, rssi - noise_floor))


def _rssi_to_percent(rssi: int, signal_bars: Optional[int]) -> int:
    if signal_bars is not None and 0 <= signal_bars <= 4:
        # Prefer a smoother mapping than 0/25/50/75/100.
        bar_map = {0: 5, 1: 25, 2: 50, 3: 75, 4: 100}
        return bar_map.get(signal_bars, 0)
    pct = int(round((max(-100, min(-30, rssi)) + 100) / 70.0 * 100))
    return max(0, min(100, pct))


def _bars_to_rssi(signal_bars: Optional[int]) -> Optional[int]:
    if signal_bars is None:
        return None
    return {
        0: -95,
        1: -82,
        2: -72,
        3: -62,
        4: -50,
    }.get(int(signal_bars), None)


def _band_from_frequency(freq_mhz: int, channel: int) -> str:
    if 1 <= channel <= 14 or 2400 <= freq_mhz <= 2500:
        return "2.4GHz"
    if 4900 <= freq_mhz <= 5900 or 30 <= channel <= 200:
        return "5GHz"
    if 5925 <= freq_mhz <= 7125:
        return "6GHz"
    return "2.4GHz" if channel and channel <= 14 else "5GHz"


def _frequency_to_channel(freq_mhz: int) -> int:
    if not freq_mhz:
        return 0
    if freq_mhz == 2484:
        return 14
    if 2412 <= freq_mhz <= 2472:
        return int((freq_mhz - 2407) / 5)
    if 5000 <= freq_mhz <= 5900:
        return int((freq_mhz - 5000) / 5)
    if 5955 <= freq_mhz <= 7115:
        return int((freq_mhz - 5950) / 5)
    return 0


def _phy_to_mode(phy: str, band: str) -> str:
    t = _norm(phy)
    if "eht" in t or "be" in t:
        return "802.11be"
    if "he" in t or "ax" in t:
        return "802.11ax"
    if "vht" in t or "ac" in t:
        return "802.11ac"
    if "ht" in t or "n" == t:
        return "802.11n"
    if "erp" in t:
        return "802.11g"
    if "ofdm" in t:
        return "802.11a" if band == "5GHz" else "802.11g"
    if "hrdsss" in t or "dsss" in t:
        return "802.11b"
    return "802.11"


def _estimate_rate(mode: str, band: str) -> str:
    # WinRT available-network scan results do not expose AP-specific negotiated data rate.
    # Provide a best-effort capability label instead of '?'.
    estimates = {
        "802.11b": "Up to 11 Mbps",
        "802.11a": "Up to 54 Mbps",
        "802.11g": "Up to 54 Mbps",
        "802.11n": "Up to 600 Mbps",
        "802.11ac": "Up to 3466 Mbps",
        "802.11ax": "Up to 9608 Mbps",
        "802.11be": "Up to 46000 Mbps",
        "802.11": "N/A via WinRT",
    }
    return estimates.get(mode, "N/A via WinRT")


def _security_string(auth: str, enc: str) -> str:
    a = _norm(auth)
    e = _norm(enc)

    if any(x in a for x in ["open80211", "none", "open"]) and any(x in e for x in ["none", "unknown", ""]):
        return "OPEN"
    if "wep" in e or "wep" in a or "sharedkey" in a:
        return "WEP"

    cipher = ""
    if "ccmp" in e or "aes" in e:
        cipher = "-AES"
    elif "tkip" in e:
        cipher = "-TKIP"
    elif e and e not in {"none", "unknown"}:
        cipher = f"-{enc}"

    if any(x in a for x in ["wpa3", "sae"]):
        return f"WPA3{cipher}" if cipher else "WPA3"
    if "rsna" in a or "wpa2" in a:
        if any(x in a for x in ["enterprise", "8021x"]):
            return f"WPA2-Enterprise{cipher}" if cipher else "WPA2-Enterprise"
        if "psk" in a:
            return f"WPA2-PSK{cipher}" if cipher else "WPA2-PSK"
        return f"WPA2{cipher}" if cipher else "WPA2"
    if "wpa" in a:
        if any(x in a for x in ["enterprise", "8021x"]):
            return f"WPA-Enterprise{cipher}" if cipher else "WPA-Enterprise"
        if "psk" in a:
            return f"WPA-PSK{cipher}" if cipher else "WPA-PSK"
        return f"WPA{cipher}" if cipher else "WPA"

    if a and e and e not in {"none", "unknown"}:
        return f"{auth}/{enc}"
    if a:
        return auth
    if e and e not in {"none", "unknown"}:
        return enc
    return "OPEN"


def _enum_tail(value: Any) -> str:
    s = _clean(value)
    if not s:
        return ""
    if "." in s:
        s = s.split(".")[-1]
    return s


def _norm(value: Any) -> str:
    return _clean(value).replace("_", "").replace("-", "").replace(" ", "").lower()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        return str(value).strip()
    except Exception:
        return ""


def _to_int(value: Any, default: Optional[int] = 0) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        try:
            return int(float(str(value).strip()))
        except Exception:
            return default


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
