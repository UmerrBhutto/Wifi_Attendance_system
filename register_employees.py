# ============================================================
#  register_employees.py  —  Employee Management (MySQL)
# ============================================================

import mysql.connector
from db_config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def _normalize_mac(mac: str) -> str:
    return mac.strip().upper()


def add_employee(emp_id: str, name: str, mac: str):
    mac = _normalize_mac(mac)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO employees (employee_id, name, mac_address) VALUES (%s, %s, %s)",
            (emp_id, name, mac)
        )
        conn.commit()
        print(f"[OK] Employee '{name}' registered successfully.")
    except mysql.connector.IntegrityError as e:
        if "employee_id" in str(e):
            print(f"[ERROR] Employee ID '{emp_id}' already exists.")
        elif "mac_address" in str(e):
            print(f"[ERROR] MAC address '{mac}' already registered.")
        else:
            print(f"[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()


def remove_employee(emp_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE employee_id = %s", (emp_id,))
    conn.commit()
    if cursor.rowcount > 0:
        print(f"[OK] Employee '{emp_id}' removed.")
    else:
        print(f"[ERROR] Employee ID '{emp_id}' not found.")
    cursor.close()
    conn.close()


def view_employees():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees ORDER BY id")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()

    if not employees:
        print("[INFO] No employees registered yet.")
        return

    print("\n" + "=" * 60)
    print(f"{'ID':<12} {'Name':<25} {'MAC Address':<20}")
    print("=" * 60)
    for e in employees:
        print(f"{e['employee_id']:<12} {e['name']:<25} {e['mac_address']:<20}")
    print("=" * 60)
    print(f"Total employees: {len(employees)}\n")


def get_employee_by_mac(mac: str):
    mac = _normalize_mac(mac)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE mac_address = %s", (mac,))
    employee = cursor.fetchone()
    cursor.close()
    conn.close()
    return employee


def menu():
    while True:
        print("\n===== Employee Registration Menu =====")
        print("1. Add Employee")
        print("2. View All Employees")
        print("3. Remove Employee")
        print("4. Exit")
        choice = input("Choose option: ").strip()

        if choice == "1":
            emp_id = input("Employee ID (e.g. EMP001): ").strip()
            name   = input("Full Name              : ").strip()
            mac    = input("MAC Address            : ").strip()
            add_employee(emp_id, name, mac)
        elif choice == "2":
            view_employees()
        elif choice == "3":
            emp_id = input("Employee ID to remove: ").strip()
            remove_employee(emp_id)
        elif choice == "4":
            print("Exiting registration system.")
            break
        else:
            print("[ERROR] Invalid option.")


if __name__ == "__main__":
    menu()
