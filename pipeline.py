#!/usr/bin/env python3
"""
Full Automation Pipeline:
1. Ingests raw configs / links from file or stdin.
2. Runs config-tester-v4 with multi-core Xray & Sing-box.
3. Filters working configs, sorts by speed/latency.
4. Updates output/sub.txt.
5. Commits and pushes to GitHub (instant live subscription update).
6. Copies working configs to Windows Clipboard.
"""

import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TESTER_SCRIPT = os.path.join(BASE_DIR, "config-tester-v4.py")
XRAY_PATH = r"D:\v2rayN-windows-64-desktop\v2rayN-windows-64\bin\xray\xray.exe"
SINGBOX_PATH = r"D:\v2rayN-windows-64-desktop\v2rayN-windows-64\bin\sing_box\sing-box.exe"
SUB_FILE = os.path.join(BASE_DIR, "output", "sub.txt")
TEMP_INPUT = os.path.join(BASE_DIR, "data", "incoming_configs.txt")
TEMP_OUTPUT = os.path.join(BASE_DIR, "output", "temp_verified.txt")

def run_pipeline(input_path: str, threads: int = 16, timeout: float = 4.0):
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        return False

    print(f"[*] Testing configs from: {input_path}")
    test_cmd = [
        "uv", "run", "--with", "requests[socks]",
        TESTER_SCRIPT,
        "-i", input_path,
        "-o", TEMP_OUTPUT,
        "-t", "1",
        "--threads", str(threads),
        "--timeout", str(timeout),
        "--rounds", "1",
        "--skip-r2",
        "--sort", "speed",
        "--xray-path", XRAY_PATH,
        "--singbox-path", SINGBOX_PATH,
    ]

    res = subprocess.run(test_cmd, cwd=BASE_DIR)
    if res.returncode != 0 or not os.path.exists(TEMP_OUTPUT):
        print("[!] Testing ended or produced no working configs.")
        return False

    with open(TEMP_OUTPUT, "r", encoding="utf-8") as f:
        verified_lines = [l.strip() for l in f if l.strip()]

    if not verified_lines:
        print("[!] 0 working configs found.")
        return False

    print(f"[✓] Found {len(verified_lines)} verified working configs!")

    # Write to output/sub.txt
    os.makedirs(os.path.dirname(SUB_FILE), exist_ok=True)
    with open(SUB_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(verified_lines) + "\n")

    # Copy to Windows Clipboard
    try:
        subprocess.run(
            ["powershell.exe", "-Command", f"Get-Content -Raw '{SUB_FILE}' | Set-Clipboard"],
            check=False
        )
        print("[✓] Copied to Windows Clipboard!")
    except Exception:
        pass

    # Git commit & push
    try:
        print("[*] Pushing update to GitHub...")
        subprocess.run(["git", "add", "output/sub.txt"], cwd=BASE_DIR, check=True)
        commit_msg = f"chore: update subscription with {len(verified_lines)} verified configs"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
        print("[✓] GitHub subscription updated successfully!")
    except subprocess.CalledProcessError as e:
        print(f"[!] Git push note: {e}")

    print("\n[🎉] Done! Now just click 'Update subscription' in v2rayN!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Config Test & Auto-Sub Sync Pipeline")
    parser.add_argument("-i", "--input", default=TEMP_INPUT, help="Path to input configs file")
    parser.add_argument("-t", "--threads", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=4.0)
    args = parser.parse_args()

    run_pipeline(args.input, args.threads, args.timeout)
