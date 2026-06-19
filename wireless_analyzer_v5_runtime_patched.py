#!/usr/bin/env python3
"""
Runtime patch wrapper for wireless_analyzer_v5.py

What it fixes:
- Replaces demo / bluetoothctl BLE scanning with Bleak-based real BLE discovery.
- Removes silent demo fallback from Wi-Fi sniffing.
- Improves Windows interface discovery and interface-name resolution for Scapy/Npcap.
- Keeps your existing UI and app code unchanged by monkey-patching at runtime.

Usage:
1) Put this file in the SAME folder as wireless_analyzer_v5.py
2) (Optional, if you already use the WinRT Wi-Fi scan patch) also keep winrt_wifi_patch.py in the same folder
3) Install deps:
     pip install bleak scapy
   On Windows also install Npcap.
4) Run:
     python wireless_analyzer_v5_runtime_patched.py
"""

import asyncio
import hashlib
import importlib.util
import os
import platform
import sys
import time
from typing import Any, Dict, List


def _load_original_module():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import wireless_analyzer_v5 as appmod
    return appmod


appmod = _load_original_module()


# Optional: apply the prior WinRT Wi-Fi scan patch if present.
try:
    from winrt_wifi_patch import apply_winrt_patch
    apply_winrt_patch(appmod.ScannerThread)
except Exception:
    pass


def _stable_angle(text: str) -> int:
    h = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()
    return int(h[:8], 16) % 360


def _ble_type_from_name(name: str) -> str:
    n = (name or "").lower()
    if any(x in n for x in ["phone", "iphone", "pixel", "galaxy"]):
        return "Phone"
    if any(x in n for x in ["watch", "band"]):
        return "Wearable"
    if any(x in n for x in ["airpods", "buds", "head", "audio", "speaker"]):
        return "Audio"
    if any(x in n for x in ["tile", "tag", "tracker"]):
        return "Tracker"
    if any(x in n for x in ["keyboard", "mouse", "hid"]):
        return "HID"
    return "BLE"


def _scan_ble_real(self) -> List[Dict[str, Any]]:
    try:
        from bleak import BleakScanner
    except Exception as ex:
        self.log_message.emit(f"[BLE] bleak not installed: {ex}")
        return []

    async def _discover():
        try:
            return await BleakScanner.discover(return_adv=True, timeout=5.0)
        except TypeError:
            # Older bleak versions
            devs = await BleakScanner.discover(timeout=5.0)
            return {getattr(d, 'address', f'idx-{i}'): (d, None) for i, d in enumerate(devs)}

    try:
        try:
            found = asyncio.run(_discover())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                found = loop.run_until_complete(_discover())
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    except Exception as ex:
        self.log_message.emit(f"[BLE] discovery failed: {ex}")
        return []

    devs: List[Dict[str, Any]] = []
    for key, payload in found.items():
        if isinstance(payload, tuple):
            device, adv = payload
        else:
            device, adv = payload, None

        address = getattr(device, "address", None) or str(key)
        name = getattr(device, "name", None) or ""
        rssi = getattr(device, "rssi", None)
        service_uuids = []
        if adv is not None:
            name = name or getattr(adv, "local_name", "") or ""
            rssi = getattr(adv, "rssi", rssi)
            service_uuids = list(getattr(adv, "service_uuids", []) or [])

        if rssi is None:
            rssi = -100

        devs.append({
            "name": name or "<unknown>",
            "address": address,
            "rssi": int(rssi),
            "type": _ble_type_from_name(name),
            "services": len(service_uuids),
            "paired": False,
            "connected": False,
            "_angle": _stable_angle(address),
        })

    self.log_message.emit(f"[BLE] bleak: {len(devs)} devices")
    return devs


def _get_ifaces_patched(self):
    ifaces = []
    system = platform.system().lower()

    if "windows" in system:
        try:
            from scapy.arch.windows import get_windows_if_list
            rows = get_windows_if_list() or []
            for row in rows:
                for key in ("network_name", "description", "name", "pcap_name"):
                    val = row.get(key)
                    if val and val not in ifaces:
                        ifaces.append(val)
            if ifaces:
                return ifaces
        except Exception:
            pass
        try:
            import subprocess
            out = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                stderr=subprocess.DEVNULL,
                timeout=5
            ).decode(errors="ignore")
            for line in out.splitlines():
                if "Name" in line and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val and val not in ifaces:
                        ifaces.append(val)
        except Exception:
            pass
        return ifaces or ["Wi-Fi"]

    # keep original behavior on non-Windows if available
    try:
        return _orig_get_ifaces(self)
    except Exception:
        return ["wlan0"]


def _resolve_iface_name(raw_name: str) -> str:
    system = platform.system().lower()
    if "windows" not in system:
        return raw_name

    try:
        from scapy.arch.windows import get_windows_if_list
        rows = get_windows_if_list() or []
        needle = (raw_name or "").strip().lower()
        # Exact lookup across likely fields.
        for row in rows:
            values = [str(row.get(k, "")) for k in ("network_name", "description", "name", "pcap_name", "guid")]
            lowered = [v.lower() for v in values if v]
            if needle and needle in lowered:
                return row.get("network_name") or row.get("pcap_name") or row.get("name") or raw_name
        # Substring lookup.
        for row in rows:
            values = [str(row.get(k, "")) for k in ("network_name", "description", "name", "pcap_name", "guid")]
            if any(needle and needle in v.lower() for v in values if v):
                return row.get("network_name") or row.get("pcap_name") or row.get("name") or raw_name
    except Exception:
        pass

    return raw_name


def _run_sniffer_patched(self):
    self._running = True
    self._counter = 0
    system = platform.system().lower()

    try:
        from scapy.all import sniff
    except Exception as ex:
        self.sniffer_log.emit(f"[Sniffer] scapy not available: {ex}")
        self.sniffer_log.emit("[Sniffer] Capture disabled. Install scapy and Npcap (Windows) or use a monitor-capable adapter.")
        return

    iface = _resolve_iface_name(getattr(self, "iface", ""))
    if not iface:
        self.sniffer_log.emit("[Sniffer] No interface selected")
        return

    self.sniffer_log.emit(f"[Sniffer] scapy capture on {iface}")
    if "windows" in system:
        self.sniffer_log.emit("[Sniffer] Windows requires Npcap; 802.11 capture also depends on adapter/driver monitor-mode support.")

    warned = False
    idle_loops = 0
    first_pass = True

    while self._running and self._counter < getattr(self, "max_packets", 1000):
        kwargs = {
            "iface": iface,
            "prn": self._handle_scapy,
            "store": False,
            "timeout": 1,
        }
        if "windows" not in system:
            kwargs["monitor"] = True

        try:
            sniff(**kwargs)
        except Exception as ex:
            if first_pass and "windows" not in system and kwargs.get("monitor"):
                first_pass = False
                self.sniffer_log.emit(f"[Sniffer] monitor mode capture failed, retrying without monitor flag: {ex}")
                try:
                    sniff(iface=iface, prn=self._handle_scapy, store=False, timeout=1)
                    continue
                except Exception as ex2:
                    self.sniffer_log.emit(f"[Sniffer] capture failed: {ex2}")
                    break
            else:
                self.sniffer_log.emit(f"[Sniffer] capture failed: {ex}")
                break

        if self._counter == 0:
            idle_loops += 1
            if idle_loops >= 5 and not warned:
                warned = True
                if "windows" in system:
                    self.sniffer_log.emit(
                        "[Sniffer] No packets captured yet. Verify Npcap is installed, run as Administrator, and use a Wi-Fi adapter/driver that supports monitor-mode 802.11 capture."
                    )
                else:
                    self.sniffer_log.emit(
                        "[Sniffer] No packets captured yet. Verify the selected interface is the wireless adapter and supports monitor mode."
                    )
        else:
            idle_loops = 0

    if self._counter == 0:
        self.sniffer_log.emit("[Sniffer] Stopped with 0 packets. Demo mode is disabled by this patch.")


# Keep originals in case non-Windows behavior needs to delegate.
_orig_scan_ble = appmod.ScannerThread._scan_ble
_orig_get_ifaces = appmod.WirelessAnalyzer._get_ifaces
_orig_sniffer_run = appmod.PacketSnifferThread.run


# Apply patches.
appmod.ScannerThread._scan_ble = _scan_ble_real
appmod.WirelessAnalyzer._get_ifaces = _get_ifaces_patched
appmod.PacketSnifferThread.run = _run_sniffer_patched


def main():
    appmod.main()


if __name__ == "__main__":
    main()
