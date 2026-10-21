#!/usr/bin/env python3
"""
Gemini reachability checker with country-restriction detection.

Reuses config-tester-v4.py's parsing/build/launch machinery, but instead of a
bare status-code check it inspects the actual Gemini response and the exit IP's
country, so configs that trigger "Gemini isn't available in your country" are
rejected.

Usage:
  python gcheck.py -i configs.txt -o ok.txt [--threads 8] [--dump-bad 2]
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
TESTER = os.path.join(BASE, "config-tester-v4.py")

spec = importlib.util.spec_from_file_location("ct4", TESTER)
ct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct)

# The tester resolves cores from CLI args in main(); import leaves them None.
ct.XRAY_PATH = ct.XRAY_PATH or r"D:\v2rayN-windows-64-desktop\v2rayN-windows-64\bin\xray\xray.exe"
ct.SINGBOX_PATH = ct.SINGBOX_PATH or r"D:\v2rayN-windows-64-desktop\v2rayN-windows-64\bin\sing_box\sing-box.exe"

GEMINI_URL = "https://gemini.google.com/app"
COUNTRY_URL = "https://www.cloudflare.com/cdn-cgi/trace"

# Server-side markers of the region lock / unsupported-country interstitial.
BAD_MARKERS = [
    "isn't currently available in your country",
    "is not currently available in your country",
    "not available in your country",
    "unsupported_country",
    "unsupported country",
    "country_unsupported",
    "google.com/url?q=https://support.google.com/gemini",
]

# Countries where Gemini is not offered at all (server-side lock regardless of IP quality).
BLOCKED_COUNTRIES = {
    "IR", "CN", "RU", "BY", "SY", "KP", "CU", "VE", "AF", "MM", "SD", "TM",
}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def check_one(item):
    idx, line = item
    line = line.strip()
    parsed = ct.parse_config_link(line)
    if not parsed:
        return dict(idx=idx, ok=False, why="parse_error", line=line)

    core = ct.XRAY_PATH if parsed["core"] == "xray" else ct.SINGBOX_PATH
    if not core or not os.path.isfile(core):
        return dict(idx=idx, ok=False, why="core_missing", line=line)

    port = ct.find_free_port()
    if parsed["core"] == "xray":
        cfg = ct.build_xray_config(port, parsed["outbound"])
        cmd = [core, "run", "-c", "stdin:"]
    else:
        cfg = ct.build_singbox_config(port, parsed["outbound"])
        cmd = [core, "run", "-c", "stdin"]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = dict(idx=idx, ok=False, line=line, proto=parsed["protocol"])
    try:
        try:
            proc.stdin.write(json.dumps(cfg).encode())
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            out["why"] = "core_stdin"
            return out

        if not ct.wait_for_port_ready(port):
            out["why"] = "port_not_ready"
            return out

        px = {"http": f"socks5h://127.0.0.1:{port}", "https": f"socks5h://127.0.0.1:{port}"}
        hdrs = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

        # 1) exit country
        country = None
        try:
            t = requests.get(COUNTRY_URL, proxies=px, headers=hdrs, timeout=8)
            m = re.search(r"^loc=([A-Z]{2})$", t.text, re.M)
            country = m.group(1) if m else None
        except Exception:
            pass
        out["country"] = country

        if country in BLOCKED_COUNTRIES:
            out["why"] = f"exit_country_{country}"
            return out

        # 2) real Gemini response
        t0 = time.perf_counter()
        r = requests.get(GEMINI_URL, proxies=px, headers=hdrs, timeout=10,
                         allow_redirects=True)
        out["latency"] = int((time.perf_counter() - t0) * 1000)
        out["status"] = r.status_code
        body = r.text or ""
        low = body.lower()

        hit = next((m for m in BAD_MARKERS if m in low), None)
        if hit:
            out["why"] = f"country_block:{hit[:40]}"
            out["body"] = body[:1200]
            return out

        # health checks: final host + app shell present
        if "gemini.google.com" not in r.url:
            out["why"] = f"wrong_host:{r.url[:60]}"
            return out
        if r.status_code != 200:
            out["why"] = f"status_{r.status_code}"
            return out

        # Positive signal: the real Gemini app shell, not an interstitial.
        if "af_initdatacallback" not in low:
            out["why"] = "no_app_shell"
            out["body"] = body[:1200]
            return out
        tm = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
        title = re.sub(r"\s+", " ", tm.group(1)).strip() if tm else ""
        out["title"] = title
        if "gemini" not in title.lower():
            out["why"] = f"bad_title:{title[:40] or 'none'}"
            out["body"] = body[:1200]
            return out
        if "before you continue" in low[:8000]:
            out["why"] = "consent_interstitial"
            return out

        out["body"] = body
        out["ok"] = True
        return out
    except requests.exceptions.Timeout:
        out["why"] = "timeout"
        return out
    except Exception as e:
        out["why"] = type(e).__name__
        return out
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=0.3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True)
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--dump-bad", type=int, default=0, help="save N blocked bodies for inspection")
    ap.add_argument("--dump-good", type=int, default=0, help="save N passing bodies for inspection")
    a = ap.parse_args()

    lines = [l.strip() for l in open(a.input, encoding="utf-8", errors="ignore") if l.strip()]
    items = list(enumerate(lines, 1))
    print(f"[*] {len(items)} configs, {a.threads} workers")

    res = []
    with ThreadPoolExecutor(max_workers=a.threads) as ex:
        futs = [ex.submit(check_one, it) for it in items]
        for f in as_completed(futs):
            r = f.result()
            res.append(r)
            tag = "OK  " if r["ok"] else "BAD "
            print(f"  [{tag}] #{r['idx']:03d} {r.get('proto','?'):11s} "
                  f"{r.get('country','--')} {str(r.get('latency',''))}ms {r.get('why','')}")

    ok = [r for r in res if r["ok"]]
    ok.sort(key=lambda r: r.get("latency", 10**9))
    with open(a.output, "w", encoding="utf-8") as f:
        f.write("\n".join(r["line"] for r in ok) + ("\n" if ok else ""))

    if a.dump_bad:
        bad = [r for r in res if not r["ok"] and r.get("body")]
        with open(os.path.join(BASE, "output", "blocked_bodies.json"), "w", encoding="utf-8") as f:
            json.dump(bad[:a.dump_bad], f, ensure_ascii=False, indent=1)

    if a.dump_good:
        good = [r for r in res if r["ok"] and r.get("body")]
        with open(os.path.join(BASE, "output", "good_bodies.json"), "w", encoding="utf-8") as f:
            json.dump(good[:a.dump_good], f, ensure_ascii=False, indent=1)

    from collections import Counter
    print(f"\n[✓] passed {len(ok)}/{len(items)}")
    print("    reasons:", dict(Counter(r.get("why", "ok") for r in res if not r["ok"])))
    print("    countries:", dict(Counter(r.get("country") for r in ok)))
    print("    ->", a.output)


if __name__ == "__main__":
    main()
