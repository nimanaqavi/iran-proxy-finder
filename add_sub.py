#!/usr/bin/env python3
"""
Adds or updates subscription in v2rayN guiNDB.db
"""
import os
import sqlite3
import sys
import time

DB_PATH = r"D:\v2rayN-windows-64-desktop\v2rayN-windows-64\guiConfigs\guiNDB.db"

def add_subscription(sub_id: str, remarks: str, url: str):
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] v2rayN database not found at {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if subscription already exists by Remarks or Url
    cur.execute("SELECT Id FROM SubItem WHERE Remarks = ? OR Url = ?", (remarks, url))
    row = cur.fetchone()

    now_ts = int(time.time())

    if row:
        existing_id = row[0]
        cur.execute(
            "UPDATE SubItem SET Remarks = ?, Url = ?, Enabled = 1, UpdateTime = ? WHERE Id = ?",
            (remarks, url, now_ts, existing_id)
        )
        print(f"[✓] Updated existing subscription '{remarks}' (ID: {existing_id}) -> {url}")
    else:
        cur.execute(
            """INSERT INTO SubItem (
                Id, Remarks, Url, MoreUrl, Enabled, UserAgent, Sort, Filter,
                AutoUpdateInterval, UpdateTime, ConvertTarget, PrevProfile,
                NextProfile, PreSocksPort, Memo, RequestHeaders, CustomCoreType
            ) VALUES (?, ?, ?, '', 1, '', 0, '', 1440, ?, '', '', '', 0, '', '', 0)""",
            (sub_id, remarks, url, now_ts)
        )
        print(f"[✓] Added new subscription '{remarks}' (ID: {sub_id}) -> {url}")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    sub_url = sys.argv[1] if len(sys.argv) > 1 else "https://raw.githubusercontent.com/nimanaqavi/iran-proxy-finder/main/output/sub.txt"
    sub_name = sys.argv[2] if len(sys.argv) > 2 else "Iran Proxy Finder"
    sub_id = str(int(time.time() * 1000))[:19]
    add_subscription(sub_id, sub_name, sub_url)
