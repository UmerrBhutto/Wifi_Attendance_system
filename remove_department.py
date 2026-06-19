# ============================================================
#  remove_department.py  —  Run ONCE to remove department column
# ============================================================
#
#  This safely removes the 'department' column from your
#  EXISTING database without losing any other data.
#
#  Run with: python remove_department.py
# ============================================================

import mysql.connector
from db_config import DB_CONFIG


def remove_department_column():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE employees DROP COLUMN department")
        print("[OK] Removed 'department' from employees table")
    except mysql.connector.Error as e:
        print(f"[INFO] employees.department: {e}")

    try:
        cursor.execute("ALTER TABLE attendance DROP COLUMN department")
        print("[OK] Removed 'department' from attendance table")
    except mysql.connector.Error as e:
        print(f"[INFO] attendance.department: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ Done! Department column removed from database.\n")


if __name__ == "__main__":
    remove_department_column()
