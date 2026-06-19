# ============================================================
#  attendance.py  —  Attendance Logic (MySQL, no department)
# ============================================================
#
#  check_out stays EMPTY/NULL while person is still around.
#  It only gets filled when auto-checkout triggers:
#      - after office work_end time
#      - AND device not seen for auto_checkout_mins
# ============================================================

import mysql.connector
from datetime import datetime, timedelta

from db_config import DB_CONFIG
from config import OFFICE_SETTINGS
from register_employees import get_employee_by_mac

_active_sessions: dict = {}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def _already_recorded_today(employee_id: str) -> bool:
    today = datetime.now().date()
    conn  = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM attendance WHERE date = %s AND employee_id = %s",
        (today, employee_id)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None


def _insert_record(employee: dict, check_in: datetime, status: str):
    """Insert new check-in. check_out stays NULL (not checked out yet)."""
    today = check_in.date()
    conn  = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO attendance
           (date, employee_id, name, check_in, check_out, last_seen, duration_mins, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (today, employee["employee_id"], employee["name"],
         check_in.time(), None, check_in.time(), 0, status)
    )
    conn.commit()
    cursor.close()
    conn.close()


def _update_last_seen_only(employee_id: str, last_seen: datetime, duration: int):
    """Update ONLY last_seen + duration. check_out is NOT touched."""
    today = datetime.now().date()
    conn  = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE attendance
           SET last_seen = %s, duration_mins = %s
           WHERE date = %s AND employee_id = %s""",
        (last_seen.time(), duration, today, employee_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def _set_checkout(employee_id: str, check_out: datetime, duration: int):
    """Officially mark check_out — only called by auto-checkout."""
    today = datetime.now().date()
    conn  = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE attendance
           SET check_out = %s, duration_mins = %s
           WHERE date = %s AND employee_id = %s""",
        (check_out.time(), duration, today, employee_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def _determine_status(check_in_time: datetime) -> str:
    work_start = datetime.strptime(OFFICE_SETTINGS["work_start"], "%H:%M").replace(
        year=check_in_time.year, month=check_in_time.month, day=check_in_time.day)
    grace_end = work_start + timedelta(minutes=OFFICE_SETTINGS["grace_period_mins"])
    return "Present" if check_in_time <= grace_end else "Late"


def _check_auto_checkout():
    """
    Only after work_end time:
    If a device hasn't been seen for auto_checkout_mins, mark check_out.
    """
    now      = datetime.now()
    work_end = datetime.strptime(OFFICE_SETTINGS["work_end"], "%H:%M").replace(
        year=now.year, month=now.month, day=now.day)

    if now < work_end:
        return  # too early, don't checkout anyone yet

    to_remove = []
    for mac, session in _active_sessions.items():
        mins_missing = (now - session["last_seen"]).total_seconds() / 60
        if mins_missing >= OFFICE_SETTINGS["auto_checkout_mins"]:
            to_remove.append(mac)
            emp       = session["employee"]
            last_seen = session["last_seen"]
            duration  = int((last_seen - session["check_in"]).total_seconds() / 60)
            _set_checkout(emp["employee_id"], last_seen, duration)
            print(f"[AUTO CHECKOUT] {emp['name']} @ {last_seen.strftime('%H:%M:%S')} "
                  f"(missing {int(mins_missing)} mins after office hours)")

    for mac in to_remove:
        _active_sessions.pop(mac)


def process_scan_results(devices: list):
    now       = datetime.now()
    seen_macs = {d["mac"] for d in devices}

    for device in devices:
        mac      = device["mac"]
        employee = get_employee_by_mac(mac)
        if employee is None:
            continue

        if mac not in _active_sessions:
            _active_sessions[mac] = {"check_in": now, "last_seen": now, "employee": employee}
        else:
            _active_sessions[mac]["last_seen"] = now

        if not _already_recorded_today(employee["employee_id"]):
            status = _determine_status(now)
            _insert_record(employee, now, status)
            print(f"[CHECK-IN] {employee['name']} @ {now.strftime('%H:%M:%S')} — {status}")
        else:
            duration = int((now - _active_sessions[mac]["check_in"]).total_seconds() / 60)
            _update_last_seen_only(employee["employee_id"], now, duration)
            print(f"[SEEN] {employee['name']} @ {now.strftime('%H:%M:%S')}")

    # Check if anyone should be auto-checked-out (only matters after work_end)
    _check_auto_checkout()


def get_session_status(employee_id: str) -> dict:
    now          = datetime.now()
    offline_mins = OFFICE_SETTINGS["offline_alert_mins"]

    for mac, session in _active_sessions.items():
        if session["employee"]["employee_id"] == employee_id:
            mins_since = (now - session["last_seen"]).total_seconds() / 60
            return {
                "online"      : mins_since < offline_mins,
                "mins_offline": int(mins_since),
                "last_seen"   : session["last_seen"].strftime("%H:%M:%S"),
            }
    return {"online": False, "mins_offline": 999, "last_seen": ""}


def print_today_report():
    today = datetime.now().date()
    conn  = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendance WHERE date = %s", (today,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"\n{'='*60}\n  ATTENDANCE REPORT — {today}\n{'='*60}")
    if not records:
        print("  No attendance recorded today.")
    else:
        for r in records:
            print(f"{r['name']:<20} In:{str(r['check_in']):<10} "
                  f"Out:{r['check_out'] or 'Active':<10} {r['status']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print_today_report()