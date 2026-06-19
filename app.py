# ============================================================
#  app.py  —  Flask Web Dashboard (MySQL version)
# ============================================================

from flask import Flask, render_template, jsonify, request
import mysql.connector
from datetime import datetime

from db_config import DB_CONFIG
from attendance import get_session_status

app = Flask(__name__)


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def load_today_attendance():
    today = datetime.now().date()
    conn  = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendance WHERE date = %s ORDER BY check_in", (today,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in records:
        for key in ["check_in", "check_out", "last_seen"]:
            if r.get(key) is not None:
                r[key] = str(r[key])
    return records


def load_all_attendance():
    conn  = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendance ORDER BY date DESC, check_in DESC")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in records:
        for key in ["check_in", "check_out", "last_seen"]:
            if r.get(key) is not None:
                r[key] = str(r[key])
        if r.get("date") is not None:
            r["date"] = str(r["date"])
    return records


def get_total_employees():
    conn  = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total


def get_stats(records):
    late    = sum(1 for r in records if r["status"] == "Late")
    present = len(records) - late
    total   = get_total_employees()
    absent  = max(0, total - len(records))
    return {"present": present, "late": late, "absent": absent, "total": total}


def enrich_with_status(records):
    enriched = []
    for r in records:
        status = get_session_status(r["employee_id"])
        r["online"]         = status["online"]
        r["mins_offline"]   = status["mins_offline"]
        r["last_seen_time"] = status["last_seen"] or r.get("last_seen", "")
        enriched.append(r)
    return enriched


# ── Page Routes ──────────────────────────────────────────

@app.route("/")
def index():
    records  = enrich_with_status(load_today_attendance())
    stats    = get_stats(records)
    today    = datetime.now().strftime("%A, %d %B %Y")
    now_time = datetime.now().strftime("%H:%M:%S")
    return render_template("index.html", records=records, stats=stats,
                           today=today, now_time=now_time)


@app.route("/history")
def history():
    return render_template("history.html", records=load_all_attendance())


@app.route("/employees")
def employees_page():
    return render_template("employees.html")


# ── API: Attendance ──────────────────────────────────────

@app.route("/api/attendance")
def api_attendance():
    records  = enrich_with_status(load_today_attendance())
    stats    = get_stats(records)
    now_time = datetime.now().strftime("%H:%M:%S")
    return jsonify({"records": records, "stats": stats, "time": now_time})


# ── API: Employees (Add / View / Delete) ─────────────────

@app.route("/api/employees", methods=["GET"])
def api_get_employees():
    conn  = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT employee_id, name, mac_address FROM employees ORDER BY id DESC")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"employees": employees})


@app.route("/api/employees", methods=["POST"])
def api_add_employee():
    data        = request.get_json()
    employee_id = (data.get("employee_id") or "").strip()
    name        = (data.get("name") or "").strip()
    mac_address = (data.get("mac_address") or "").strip().upper()

    if not employee_id or not name or not mac_address:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO employees (employee_id, name, mac_address) VALUES (%s, %s, %s)",
            (employee_id, name, mac_address)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Employee added"})
    except mysql.connector.IntegrityError as e:
        if "employee_id" in str(e):
            msg = f"Employee ID '{employee_id}' already exists"
        elif "mac_address" in str(e):
            msg = f"MAC address already registered to another employee"
        else:
            msg = str(e)
        return jsonify({"success": False, "message": msg}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/employees/<employee_id>", methods=["DELETE"])
def api_delete_employee(employee_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    conn.close()
    if deleted:
        return jsonify({"success": True, "message": "Employee removed"})
    return jsonify({"success": False, "message": "Employee not found"}), 404


if __name__ == "__main__":
    print("=" * 50)
    print("  WiFi Attendance Dashboard (MySQL)")
    print("  Open: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
