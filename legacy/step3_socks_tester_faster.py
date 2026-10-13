# step3_socks_tester_fast.py
import sys
import socks
from concurrent.futures import ThreadPoolExecutor, as_completed

TELEGRAM_IP = "149.154.167.91"
TELEGRAM_PORT = 443
TIMEOUT = 10
THREADS = 90   

def test_proxy(ip_port):
    """تست یک پراکسی به فرمت IP:port"""
    try:
        ip, port_str = ip_port.split(":", 1)
        port = int(port_str)
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, ip, port)
        s.settimeout(TIMEOUT)
        s.connect((TELEGRAM_IP, TELEGRAM_PORT))
        s.close()
        return ip_port
    except:
        return None

def main():
    input_file = "ip_port.txt"
    output_file = "working_proxies.txt"

    try:
        with open(input_file, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"ERROR: {input_file} not found.")
        return

    if not proxies:
        print("No proxies to test.")
        return

    print(f"Testing {len(proxies)} proxies using {THREADS} concurrent threads...")
    working = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(futures):
            result = future.result()
            if result:
                working.append(result)
                print(f"[+] {result} works")
            # می‌توانید خط زیر را برای نمایش پورت‌های خراب فعال کنید:
            else:
                print(f"[-] {futures[future]} failed")

    print("\n--- Final Result ---")
    if working:
        with open(output_file, "w") as f:
            for proxy in working:
                f.write(f"{proxy}\n")
        print(f"Found {len(working)} working proxies:")
        for proxy in working:
            print(f"  {proxy}")
        print(f"\nSaved to {output_file}")
    else:
        print("No working proxies found.")

if __name__ == "__main__":
    main()