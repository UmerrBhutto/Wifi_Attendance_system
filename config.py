# ============================================================
#  config.py  —  WiFi Attendance System Settings
# ============================================================

OFFICE_SETTINGS = {
    "office_name"           : "My Office",
    "work_start"            : "09:00",
    "work_end"              : "18:00",
    "grace_period_mins"     : 15,
    "min_stay_mins"         : 30,
    "scan_interval_secs"    : 60,
    "auto_checkout_mins"    : 60,
    "offline_alert_mins"    : 2,     # Show red indicator after 2 mins offline
}

# ── Add ALL your WiFi networks here ────────────────────────
NETWORK_RANGES = [
    "192.168.100.0/24",   # WiFi Network 1 (BCI-2)
    # "192.168.1.0/24",   # WiFi Network 2 (uncomment and add your 2nd network)
]

# File paths
EMPLOYEE_FILE   = "data/employees.csv"
ATTENDANCE_FILE = "data/attendance.csv"
LOG_FILE        = "data/scan_log.csv"
