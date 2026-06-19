# ============================================================
#  setup_database.py  —  Creates Database + Tables (Run ONCE)
# ============================================================

import mysql.connector
from mysql.connector import Error


def create_database_and_tables():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="YOUR_PASSWORD",   # ← CHANGE THIS
        )
        cursor = connection.cursor()
        print("[OK] Connected to MySQL server")

        cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_db")
        print("[OK] Database 'attendance_db' created/verified")
        cursor.execute("USE attendance_db")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                employee_id   VARCHAR(50) UNIQUE NOT NULL,
                name          VARCHAR(100) NOT NULL,
                mac_address   VARCHAR(20) UNIQUE NOT NULL,
                registered_on DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'employees' created/verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                date          DATE NOT NULL,
                employee_id   VARCHAR(50) NOT NULL,
                name          VARCHAR(100) NOT NULL,
                check_in      TIME,
                check_out     TIME,
                last_seen     TIME,
                duration_mins INT DEFAULT 0,
                status        VARCHAR(20) DEFAULT 'Present',
                UNIQUE KEY unique_daily (date, employee_id)
            )
        """)
        print("[OK] Table 'attendance' created/verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_logs (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                scan_time      DATETIME DEFAULT CURRENT_TIMESTAMP,
                devices_found  INT,
                network_range  VARCHAR(50)
            )
        """)
        print("[OK] Table 'scan_logs' created/verified")

        connection.commit()
        print("\n✅ Database setup complete! All tables ready.\n")

    except Error as e:
        print(f"[ERROR] {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    create_database_and_tables()
