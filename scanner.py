# ============================================================
#  scanner.py  —  Auto-detect & scan connected networks
# ============================================================

import subprocess
import re
import socket
import platform
from datetime import datetime

try:
    from scapy.all import ARP, Ether, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

from config import NETWORK_RANGES


def get_active_networks() -> list:
    """
    Auto-detect which networks this PC is currently connected to
    by checking local IP addresses and matching against NETWORK_RANGES.
    Only returns networks we're actually connected to.
    """
    active = []
    try:
        # Get all local IPs of this machine
        hostname  = socket.gethostname()
        local_ips = socket.getaddrinfo(hostname, None)
        local_ipv4 = [info[4][0] for info in local_ips
                      if info[0] == socket.AF_INET]

        for network in NETWORK_RANGES:
            # Extract base e.g. "192.168.100" from "192.168.100.0/24"
            base = ".".join(network.split(".")[:3])
            for ip in local_ipv4:
                if ip.startswith(base):
                    active.append(network)
                    print(f"[NET] Active network detected: {network} (local IP: {ip})")
                    break

    except Exception as e:
        print(f"[WARN] Network detection failed: {e} — using all configured ranges")
        active = NETWORK_RANGES

    if not active:
        print("[WARN] No matching active networks found — scanning all configured ranges")
        active = NETWORK_RANGES

    return active


def arp_scan(network_range: str) -> list:
    """Scan a single network range via ARP."""
    if not SCAPY_AVAILABLE:
        return arp_table_scan()
    try:
        packet      = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_range)
        answered, _ = srp(packet, timeout=3, verbose=False)
        now         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [{"ip": rcv.psrc, "mac": rcv.hwsrc.upper(), "timestamp": now}
                for _, rcv in answered]
    except Exception as e:
        print(f"[ERROR] ARP scan failed for {network_range}: {e}")
        return []


def arp_table_scan() -> list:
    """Fallback: read system ARP table."""
    devices = []
    now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        output = subprocess.check_output(
            "arp -a", shell=True, stderr=subprocess.DEVNULL
        ).decode()
        if platform.system() == "Windows":
            pattern = r"(\d+\.\d+\.\d+\.\d+)\s+([\w-]{17})\s+dynamic"
            for ip, mac in re.findall(pattern, output, re.IGNORECASE):
                devices.append({"ip": ip, "mac": mac.replace("-", ":").upper(), "timestamp": now})
        else:
            pattern = r"\((\d+\.\d+\.\d+\.\d+)\) at ([\w:]{17})"
            for ip, mac in re.findall(pattern, output):
                devices.append({"ip": ip, "mac": mac.upper(), "timestamp": now})
    except Exception as e:
        print(f"[ERROR] ARP table read failed: {e}")
    return devices


def scan_network() -> list:
    """
    Auto-detect active networks and scan only those.
    Merges results and removes duplicates by MAC.
    """
    active_networks = get_active_networks()
    all_devices     = {}  # mac → device (dedup)

    for network in active_networks:
        print(f"[SCAN] Scanning {network} ...")
        devices = arp_scan(network) if SCAPY_AVAILABLE else arp_table_scan()
        for d in devices:
            all_devices[d["mac"]] = d

    total = len(all_devices)
    print(f"[SCAN] Found {total} unique device(s) across {len(active_networks)} active network(s).")
    return list(all_devices.values())


if __name__ == "__main__":
    print("Active networks:", get_active_networks())
    devices = scan_network()
    print(f"\n{'IP Address':<18} {'MAC Address':<20} {'Time'}")
    print("-" * 55)
    for d in devices:
        print(f"{d['ip']:<18} {d['mac']:<20} {d['timestamp']}")
