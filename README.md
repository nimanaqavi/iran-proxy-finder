# Iran Proxy Finder & Auto Tester

High-performance, async proxy finder and validator optimized for Iranian network restrictions and censorship bypass.

## Features
- **Zero-Dependency Stdlib Core:** Built entirely on Python 3 `asyncio` and `socket` (no nmap or heavy dependencies required).
- **Multi-Source IP Extraction:** Automatically parses raw IP lists, CIDR blocks, Telegram links, and V2Ray configs (`vless://`, `vmess://`, `trojan://`, `ss://`, `socks://`).
- **High-Concurrency Port Probing:** Probes high-yield proxy ports (1080, 10808, 2080, 8080, 8888, 3128, etc.) with 150+ async workers.
- **Direct SOCKS5 Handshake Validation:** Validates end-to-end SOCKS5 connectivity against Telegram Datacenter 4 (`149.154.167.91:443`) and records latency.
- **Multi-Format Export:**
  - Raw SOCKS URIs (`output/working_socks.txt`)
  - One-click Telegram Socks links (`output/tg_links.txt`)
  - Base64 Subscription format for V2Ray / v2rayN / Sing-box / Nekobox (`output/sub.txt`)
- **v2rayN Integration:** Direct subscription syncing tool via `add_sub.py`.

## Quick Start

### 1. Run Proxy Finder
```bash
python finder.py -i data/all_ips.txt -c 150 -t 2.0 -o output
```

Options:
- `-i, --input`: Path to input file (IPs or configs). Default: `data/all_ips.txt`.
- `-p, --ports`: Comma-separated port list or `default`.
- `-c, --concurrency`: Number of concurrent workers (default: `150`).
- `-t, --timeout`: Socket timeout in seconds (default: `2.0`).
- `-o, --out`: Output directory (default: `output`).

### 2. Sync Subscription with v2rayN
```bash
python add_sub.py
```

## Directory Structure
- `finder.py`: Main async scanner and SOCKS validator.
- `add_sub.py`: SQLite subscription injector for local v2rayN client.
- `data/`: Extracted IPs, legacy seeds, and candidate configs.
- `legacy/`: Original PowerShell & Python scan scripts.
- `output/`: Generated working configs, Telegram links, and Base64 subscription.
