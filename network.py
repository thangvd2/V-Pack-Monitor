# =============================================================================
# V-Pack Monitor - CamDongHang
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

"""LAN scanner module - find device IP by MAC address using ARP table and ping sweep."""

import ipaddress
import platform
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_local_subnet() -> str:
    """Detect the local network subnet automatically."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Falls back to hostname-based detection if no internet connectivity
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        if local_ip and not local_ip.startswith("127."):
            prefix = ".".join(local_ip.split(".")[:3])
            return f"{prefix}.0/24"
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip and not local_ip.startswith("127."):
            prefix = ".".join(local_ip.split(".")[:3])
            return f"{prefix}.0/24"
    except Exception:
        pass
    return "192.168.1.0/24"


def normalize_mac(mac: str) -> str:
    """Normalize a MAC address to uppercase colon-separated format.

    Accepts: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF,
             aabb.ccdd.eeff, aabbccddeeff, 30:24:50:48:9:38
    Returns: AA:BB:CC:DD:EE:FF
    """
    parts = re.split(r"[\s:\-\.]", mac.strip())
    hex_chars = "".join(p.zfill(2) for p in parts if p).upper()
    return ":".join(hex_chars[i : i + 2] for i in range(0, 12, 2))


def validate_mac(mac: str) -> bool:
    """Return True if the string looks like a valid MAC address."""
    parts = re.split(r"[\s:\-\.]", mac.strip())
    hex_chars = "".join(p.zfill(2) for p in parts if p)
    return bool(re.fullmatch(r"[0-9A-Fa-f]{12}", hex_chars))


def _parse_arp_table() -> list[dict]:
    """Parse the system ARP table into a list of {ip, mac} dicts."""
    results = []
    try:
        proc = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = proc.stdout
        # Match lines with IP and MAC across Windows/Mac/Linux
        # Windows:  192.168.1.1   aa-bb-cc-dd-ee-ff   dynamic
        # Mac/Linux: ? (192.168.1.1) at aa:bb:cc:dd:ee:ff on en0
        for line in output.splitlines():
            if "(incomplete)" in line:
                continue
            m = re.search(
                r"\((\d{1,3}(?:\.\d{1,3}){3})\)\s+at\s+([0-9a-fA-F]{1,2}(?:[:\-][0-9a-fA-F]{1,2}){5})",
                line,
            ) or re.search(
                r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F]{1,2}(?:[:\-][0-9a-fA-F]{1,2}){5})",
                line,
            )
            if m:
                ip = m.group(1)
                try:
                    mac = normalize_mac(m.group(2))
                except (ValueError, IndexError):
                    continue
                if mac != "FF:FF:FF:FF:FF:FF":
                    results.append({"ip": ip, "mac": mac})
    except Exception:
        pass
    return results


def _ping_host(ip: str):
    """Ping a single host to populate the ARP table. Thread-safe."""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(
                ["ping", "-n", "1", "-w", "1000", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
        else:
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
    except Exception:
        pass


def _is_private_ip(ip_str):
    """Check if an IP address is in a private range."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return addr.is_private
    except ValueError:
        return False


def scan_lan_for_mac(target_mac: str, subnet: str | None = None) -> str | None:
    """Scan the LAN to find a device's IP address by its MAC address.

    Args:
        target_mac: MAC address in any common format.
        subnet: Optional subnet like '192.168.1.0/24'. Auto-detected if None.

    Returns:
        IP address string if found, None otherwise.
    """
    if not validate_mac(target_mac):
        return None

    target = normalize_mac(target_mac)

    # Step 1: Check ARP table first (instant if device was recently seen)
    for entry in _parse_arp_table():
        if entry["mac"] == target:
            return entry["ip"]

    # Step 2: Ping sweep to populate ARP table
    if subnet is None:
        subnet = get_local_subnet()
    prefix = subnet.rsplit(".", 1)[0]
    # e.g. '192.168.1.0/24' -> '192.168.1'

    if not _is_private_ip(f"{prefix}.1"):
        return None  # Don't scan non-private ranges

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(_ping_host, f"{prefix}.{i}"): i for i in range(1, 255)}
        for future in as_completed(futures, timeout=17):
            try:
                future.result(timeout=5)
            except Exception:
                pass

    # Step 3: Re-read ARP table after sweep
    for entry in _parse_arp_table():
        if entry["mac"] == target:
            return entry["ip"]

    return None


def scan_lan_all() -> list[dict]:
    """Return all MAC-IP pairs found in the system ARP table.

    Returns:
        List of dicts like [{"ip": "192.168.1.55", "mac": "AA:BB:CC:DD:EE:FF"}, ...]
    """
    return _parse_arp_table()
