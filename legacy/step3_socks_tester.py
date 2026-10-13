# step3_socks_tester.py
import sys
import socket
import socks

INPUT_FILE = "ip_port.txt"
OUTPUT_FILE = "working_proxies.txt"
TELEGRAM_IP = "149.154.167.91"
TELEGRAM_PORT = 443
TIMEOUT = 5

def test_socks5(proxy_ip, proxy_port):
    try:
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, proxy_ip, proxy_port)
        s.settimeout(TIMEOUT)
        s.connect((TELEGRAM_IP, TELEGRAM_PORT))
        s.close()
        return True
    except:
        return False

def main():
    try:
        with open(INPUT_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"ERROR: {INPUT_FILE} not found. Run step2 first.")
        sys.exit(1)

    if not lines:
        print("No IP:port entries found.")
        sys.exit(1)

    # clear output
    open(OUTPUT_FILE, "w").close()
    working_count = 0

    for line in lines:
        if ":" not in line:
            continue
        ip, port_str = line.split(":", 1)
        try:
            port = int(port_str)
        except:
            continue
        print(f"Testing {ip}:{port} ... ", end="")
        if test_socks5(ip, port):
            print("WORKING")
            with open(OUTPUT_FILE, "a") as f:
                f.write(f"{ip}:{port}\n")
            working_count += 1
        else:
            print("FAILED")

    print(f"\nDone. {working_count} working SOCKS5 proxies saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()