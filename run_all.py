# ============================================================
#  run_all.py  —  Run Scanner + Web Server (MySQL version)
# ============================================================

import threading
import time
from datetime import datetime

from config import OFFICE_SETTINGS
from scanner import scan_network
from attendance import process_scan_results
from app import app


def run_scanner():
    interval = OFFICE_SETTINGS["scan_interval_secs"]
    print(f"[SCANNER] Started — scanning every {interval} seconds")
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning network...")
            devices = scan_network()
            process_scan_results(devices)
        except Exception as e:
            print(f"[SCANNER ERROR] {e}")
        time.sleep(interval)


if __name__ == "__main__":
    print("=" * 55)
    print("  WiFi Attendance System — MySQL Edition")
    print(f"  Office : {OFFICE_SETTINGS['office_name']}")
    print(f"  Hours  : {OFFICE_SETTINGS['work_start']} – {OFFICE_SETTINGS['work_end']}")
    print("=" * 55)
    print("\n  Dashboard : http://localhost:5000")
    print("\n  Press Ctrl+C to stop\n")

    scanner_thread = threading.Thread(target=run_scanner, daemon=True)
    scanner_thread.start()

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
