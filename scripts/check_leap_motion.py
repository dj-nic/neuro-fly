#!/usr/bin/env python3
"""Diagnose Ultraleap USB, SDK, Python binding, and (optionally) live frames.

This script uses only the Python standard library unless ``--smoke-seconds``
is supplied and the official ``leap`` Python binding is installed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import threading
import time


USB_VENDOR_LEAP = "f182"
USB_VENDOR_LABELS = ("leap motion", "ultraleap", "leapmotion")


def _run(command: list[str], timeout_s: float = 5.0) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (result.stdout or "") + (result.stderr or "")


def _matches_leap(text: str) -> bool:
    lowered = text.lower()
    return any(label in lowered for label in USB_VENDOR_LABELS) or bool(
        re.search(r"(?:vid_|id )f182(?::|&pid_|\b)", lowered)
    )


def _linux_usb_devices() -> list[str]:
    devices: list[str] = []
    root = Path("/sys/bus/usb/devices")
    if root.is_dir():
        for device_dir in sorted(root.iterdir()):
            vendor_file = device_dir / "idVendor"
            product_file = device_dir / "idProduct"
            try:
                vendor = vendor_file.read_text(encoding="ascii").strip().lower()
                product = product_file.read_text(encoding="ascii").strip().lower()
            except OSError:
                continue
            if not vendor or not product:
                continue
            try:
                name = (device_dir / "product").read_text(encoding="utf-8").strip()
            except OSError:
                name = ""
            try:
                manufacturer = (device_dir / "manufacturer").read_text(encoding="utf-8").strip()
            except OSError:
                manufacturer = ""
            description = " ".join(part for part in (manufacturer, name) if part)
            line = f"{device_dir.name}: {vendor}:{product} {description}".strip()
            if vendor == USB_VENDOR_LEAP or _matches_leap(line):
                devices.append(line)
        if devices:
            return devices

    lsusb = shutil.which("lsusb")
    if lsusb:
        return [
            line.strip()
            for line in _run([lsusb]).splitlines()
            if _matches_leap(line)
        ]
    return []


def _windows_usb_devices() -> list[str]:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        return []
    command = (
        "Get-PnpDevice -PresentOnly | "
        "Where-Object { $_.FriendlyName -match 'Leap|Ultra' -or "
        "$_.InstanceId -match 'VID_F182' } | "
        "Select-Object -Property FriendlyName,InstanceId | ConvertTo-Json -Compress"
    )
    output = _run([powershell, "-NoProfile", "-Command", command])
    if not output.strip():
        return []
    try:
        devices = json.loads(output)
    except json.JSONDecodeError:
        return [line.strip() for line in output.splitlines() if _matches_leap(line)]
    if isinstance(devices, dict):
        devices = [devices]
    return [
        f"{device.get('FriendlyName', 'Leap device')} ({device.get('InstanceId', '')})"
        for device in devices
        if isinstance(device, dict)
    ]


def _mac_usb_devices() -> list[str]:
    output = _run(["system_profiler", "SPUSBDataType", "-detailLevel", "mini"], 10.0)
    lines = output.splitlines()
    devices: list[str] = []
    for index, line in enumerate(lines):
        if _matches_leap(line):
            details = [line.strip()]
            if index + 1 < len(lines):
                details.append(lines[index + 1].strip())
            devices.append(" ".join(part for part in details if part))
    return devices


def find_usb_devices() -> list[str]:
    system = platform.system()
    if system == "Linux":
        return _linux_usb_devices()
    if system == "Windows":
        return _windows_usb_devices()
    if system == "Darwin":
        return _mac_usb_devices()
    return []


def leap_sdk_candidates() -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("LEAPSDK_INSTALL_LOCATION")
    if override:
        candidates.append(Path(override))

    system = platform.system()
    if system == "Windows":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidates.append(Path(program_files) / "Ultraleap" / "LeapSDK")
    elif system == "Linux":
        candidates.extend(
            [
                Path("/opt/ultraleap/LeapSDK"),
                Path("/usr/lib/ultraleap-hand-tracking-service"),
                Path("/usr/lib/x86_64-linux-gnu"),
                Path("/usr/lib/aarch64-linux-gnu"),
                Path("/usr/share/doc/ultraleap-hand-tracking-service"),
                Path("/usr/lib/aarch64-linux-gnu/ultraleap-hand-tracking-service"),
            ]
        )
    elif system == "Darwin":
        candidates.append(
            Path("/Applications/Ultraleap Hand Tracking.app/Contents/LeapSDK")
        )
    return candidates


def find_sdk_libraries() -> list[Path]:
    names_by_system = {
        "Windows": ("LeapC.dll", "Leap.dll"),
        "Linux": ("libLeapC.so", "libLeapC.so.5", "libLeap.so"),
        "Darwin": ("libLeapC.dylib", "libLeapC.5.dylib", "libLeap.dylib"),
    }
    names = names_by_system.get(platform.system(), ())
    found: list[Path] = []
    for root in leap_sdk_candidates():
        for relative in (Path(""), Path("lib"), Path("lib") / "x64", Path("lib") / "aarch64"):
            for name in names:
                path = root / relative / name
                if path.is_file() and path not in found:
                    found.append(path)
        cffi = root / "leapc_cffi"
        if cffi.is_dir():
            for name in names:
                path = cffi / name
                if path.is_file() and path not in found:
                    found.append(path)
    return found


def run_sdk_smoke(seconds: float) -> tuple[bool, int, int, str]:
    """Connect to the installed service and count tracking frames and hands."""
    try:
        import leap  # type: ignore[import-not-found]
        class FrameListener(leap.Listener):  # type: ignore[name-defined]
            def __init__(self) -> None:
                self.frames = 0
                self.hands = 0
                self.changed = threading.Event()

            def on_tracking_event(self, event: object) -> None:
                self.frames += 1
                self.hands += len(getattr(event, "hands", []))
                self.changed.set()
    except Exception as exc:  # Import may fail when the native CFFI library is missing.
        return False, 0, 0, f"Python-Binding 'leap' nicht importierbar: {exc}"

    listener = FrameListener()
    try:
        connection = leap.Connection(listeners=[listener], poll_timeout=0.1)
        with connection.open(timeout=min(10.0, max(2.0, seconds))):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                listener.changed.wait(timeout=min(0.25, max(0.0, deadline - time.monotonic())))
                listener.changed.clear()
        detail = f"{listener.frames} Tracking-Frames, {listener.hands} Hand-Erkennungen"
        return listener.frames > 0, listener.frames, listener.hands, detail
    except Exception as exc:
        return False, listener.frames, listener.hands, f"Verbindung/Laufzeittest fehlgeschlagen: {exc}"


def support_note() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Linux" and machine in {"aarch64", "arm64", "armv7l", "armv8l"}:
        return (
            "Linux/ARM: Ultraleap dokumentiert LeapC-Pfade für Raspberry Pi OS und "
            "Python-Bindings für Linux ARM. Die allgemeine Linux-Service-Anleitung "
            "nennt dagegen Ubuntu 22.04 x86_64. Pi-3B+-Runtime, Controller-Modell "
            "und aktuelle Python-Version daher praktisch verifizieren."
        )
    if system == "Linux":
        return "Linux/x86_64: Ultraleap dokumentiert Ubuntu 22.04 x86_64 als unterstützte Linux-Umgebung."
    if system == "Windows":
        return "Windows: Ultraleap stellt Hand-Tracking-Software und LeapC-SDK für Windows bereit."
    return "Für diese Plattform bitte Ultraleap-Kompatibilität und SDK-Pfade separat prüfen."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke-seconds",
        type=float,
        default=0.0,
        metavar="SEKUNDEN",
        help="LeapC-Service verbinden und für diese Dauer echte Tracking-Frames erwarten; Hand über dem Gerät bewegen.",
    )
    parser.add_argument(
        "--verbose-usb",
        action="store_true",
        help="Unter Linux alle USB-Einträge aus sysfs anzeigen.",
    )
    args = parser.parse_args()
    if not math.isfinite(args.smoke_seconds) or args.smoke_seconds < 0.0:
        parser.error("--smoke-seconds muss eine endliche Zahl größer oder gleich 0 sein")
    if 0.0 < args.smoke_seconds < 0.5:
        parser.error("--smoke-seconds muss 0 (aus) oder mindestens 0.5 sein")

    print(f"System: {platform.system()} {platform.release()} | Architektur: {platform.machine()}")
    print(f"Python: {platform.python_version()} ({sys.executable})")
    print(f"Kompatibilitätshinweis: {support_note()}")

    devices = find_usb_devices()
    if devices:
        print("USB-Gerät: ERKANNT")
        for device in devices:
            print(f"  {device}")
    else:
        print("USB-Gerät: nicht eindeutig als Leap/Ultraleap erkannt")
        if platform.system() == "Linux":
            print("  Tipp: lsusb vor und nach dem Einstecken vergleichen; --verbose-usb zeigt erkannte sysfs-Geräte.")

    libraries = find_sdk_libraries()
    if libraries:
        print("LeapC/Leap-SDK-Bibliothek: gefunden")
        for library in libraries:
            print(f"  {library}")
    else:
        print("LeapC/Leap-SDK-Bibliothek: an den üblichen Installationsorten nicht gefunden")

    try:
        binding_available = importlib.util.find_spec("leap") is not None
    except (ImportError, ValueError):
        binding_available = False
    print(f"Python-Binding 'leap': {'gefunden' if binding_available else 'nicht installiert/auffindbar'}")

    if args.verbose_usb and platform.system() == "Linux":
        usb_root = Path("/sys/bus/usb/devices")
        if usb_root.is_dir():
            print("USB-Geräte (sysfs):")
            count = 0
            for device_dir in sorted(usb_root.iterdir()):
                try:
                    vendor = (device_dir / "idVendor").read_text(encoding="ascii").strip()
                    product = (device_dir / "idProduct").read_text(encoding="ascii").strip()
                except OSError:
                    continue
                try:
                    name = (device_dir / "product").read_text(encoding="utf-8").strip()
                except OSError:
                    name = ""
                print(f"  {device_dir.name}: {vendor}:{product} {name}".rstrip())
                count += 1
            if not count:
                print("  Keine USB-Geräte aus sysfs auslesbar.")

    if args.smoke_seconds:
        connected, frames, hands, detail = run_sdk_smoke(args.smoke_seconds)
        if connected:
            print(f"LeapC-Laufzeittest: TRACKING-FRAMES EMPFANGEN ({detail})")
            if hands == 0:
                print("  Keine Hand erkannt: Hand sichtbar über dem Gerät bewegen und erneut probieren.")
            return 0
        print(f"LeapC-Laufzeittest: NICHT BESTÄTIGT ({detail})")
        return 2

    print("Laufzeittest: übersprungen. Für einen echten SDK-Test --smoke-seconds 5 verwenden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
