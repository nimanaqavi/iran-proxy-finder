#!/usr/bin/env python3
"""
Ultra-fast Async Proxy Finder & Tester (Iran Censorship Bypass Suite)
Pure Python stdlib (YAGNI / Zero external dependencies).
"""

import argparse
import asyncio
import base64
import os
import re
import socket
import struct
import sys
import time

IPV4_RE = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
DEFAULT_PORTS = [1080, 10808, 2080, 8080, 8888, 3128, 443, 8443, 2053, 2082, 2083, 2087, 2095, 2096, 2052, 1090, 8291, 5998]
TELEGRAM_TARGET = ("149.154.167.91", 443)  # Telegram DC4

# ponytail: simple in-memory list; upgrade to SQLite / bloom-filter if target space > 500k IPs.
def extract_ips(source_text: str) -> set[str]:
    """Extract unique IPv4 addresses from text, URLs, configs, or raw dumps."""
    return set(IPV4_RE.findall(source_text))

async def test_socks5(ip: str, port: int, timeout: float = 2.5) -> tuple[bool, float]:
    """
    Pure stdlib asyncio SOCKS5 handshake directly against Telegram DC4.
    Returns (is_working, latency_ms).
    """
    t0 = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
        # SOCKS5 greeting: VER=5, NMETHODS=1, METHOD=0 (No Auth)
        writer.write(b'\x05\x01\x00')
        await asyncio.wait_for(writer.drain(), timeout=timeout)
        greeting_resp = await asyncio.wait_for(reader.readexactly(2), timeout=timeout)
        if greeting_resp != b'\x05\x00':
            writer.close()
            await writer.wait_closed()
            return False, 0.0

        # SOCKS5 CONNECT request: VER=5, CMD=1 (CONNECT), RSV=0, ATYP=1 (IPv4)
        target_ip_bytes = socket.inet_aton(TELEGRAM_TARGET[0])
        target_port_bytes = struct.pack(">H", TELEGRAM_TARGET[1])
        writer.write(b'\x05\x01\x00\x01' + target_ip_bytes + target_port_bytes)
        await asyncio.wait_for(writer.drain(), timeout=timeout)

        # Response: VER=5, REP=0 (Success), RSV=0, ATYP=1, BND.ADDR (4), BND.PORT (2) = 10 bytes
        resp = await asyncio.wait_for(reader.readexactly(10), timeout=timeout)
        writer.close()
        await writer.wait_closed()

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        if resp[1] == 0x00:  # 0x00 = succeeded
            return True, latency_ms
        return False, 0.0
    except Exception:
        return False, 0.0

async def scan_target(ip: str, port: int, sem: asyncio.Semaphore, timeout: float = 2.0) -> dict | None:
    async with sem:
        ok, latency = await test_socks5(ip, port, timeout=timeout)
        if ok:
            print(f"  [+] FOUND: {ip}:{port} ({latency}ms)")
            return {"ip": ip, "port": port, "latency": latency}
        return None

async def run_scan(ips: list[str], ports: list[int], concurrency: int = 150, timeout: float = 2.0):
    sem = asyncio.Semaphore(concurrency)
    tasks = [scan_target(ip, port, sem, timeout) for ip in ips for port in ports]
    print(f"[*] Scanning {len(ips)} IPs on {len(ports)} candidate ports ({len(tasks)} targets) with {concurrency} workers...")
    results = await asyncio.gather(*tasks)
    working = [r for r in results if r]
    working.sort(key=lambda x: x["latency"])
    return working

def save_results(working: list[dict], out_dir: str = "."):
    os.makedirs(out_dir, exist_ok=True)
    raw_file = os.path.join(out_dir, "working_socks.txt")
    tg_file = os.path.join(out_dir, "tg_links.txt")
    sub_file = os.path.join(out_dir, "sub.txt")

    socks_lines = []
    tg_lines = []
    for item in working:
        ip, port, lat = item["ip"], item["port"], item["latency"]
        tag = f"🇮🇷-Socks-{ip}:{port}-{lat}ms"
        socks_lines.append(f"socks://{ip}:{port}#{tag}")
        tg_lines.append(f"https://t.me/socks?server={ip}&port={port}")

    with open(raw_file, "w", encoding="utf-8") as f:
        f.write("\n".join(socks_lines) + "\n" if socks_lines else "")
    with open(tg_file, "w", encoding="utf-8") as f:
        f.write("\n".join(tg_lines) + "\n" if tg_lines else "")

    # Base64 subscription
    b64_content = base64.b64encode("\n".join(socks_lines).encode("utf-8")).decode("utf-8")
    with open(sub_file, "w", encoding="utf-8") as f:
        f.write(b64_content + "\n" if b64_content else "")

    print(f"\n[✓] Results saved:")
    print(f"    - SOCKS URIs: {raw_file}")
    print(f"    - Telegram links: {tg_file}")
    print(f"    - Base64 Subscription: {sub_file}")

def main():
    parser = argparse.ArgumentParser(description="Ultra-fast Async SOCKS Proxy Finder")
    parser.add_argument("-i", "--input", help="Input file containing IPs, configs, or links", default="data/all_ips.txt")
    parser.add_argument("-p", "--ports", help="Comma-separated ports or 'default'", default="default")
    parser.add_argument("-c", "--concurrency", type=int, default=150, help="Max concurrent connections (default: 150)")
    parser.add_argument("-t", "--timeout", type=float, default=2.0, help="Socket timeout in seconds (default: 2.0)")
    parser.add_argument("-o", "--out", default="output", help="Output directory (default: output)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] Input file '{args.input}' not found.")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    ips = list(extract_ips(raw_text))
    if not ips:
        print("[!] No valid IPv4 addresses found in input.")
        sys.exit(0)

    ports = DEFAULT_PORTS if args.ports == "default" else [int(p.strip()) for p in args.ports.split(",") if p.strip().isdigit()]
    print(f"[!] Extracted {len(ips)} unique IPs.")

    # ponytail: default loop handles ~500 sockets fine; use uvloop on Linux when scaling > 5k.

    working = asyncio.run(run_scan(ips, ports, concurrency=args.concurrency, timeout=args.timeout))
    print(f"\n[+] Scan finished: {len(working)} working proxies found out of {len(ips) * len(ports)} probes.")
    save_results(working, args.out)

if __name__ == "__main__":
    main()
