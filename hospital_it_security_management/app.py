from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB = Path(__file__).parent / "hospital_it.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT NOT NULL,
        department TEXT NOT NULL,
        device_type TEXT NOT NULL,
        os TEXT,
        security_status TEXT NOT NULL,
        status TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL
    )""")
    if conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0] == 0:
        devices = [
            ("PC-001","IT","Workstation","Windows 11","Protected","Active"),
            ("PC-002","Emergency","Workstation","Windows 10","Needs Update","Active"),
            ("PR-003","Administration","Printer","Embedded","Protected","Active"),
            ("PC-004","Radiology","Workstation","Windows 11","Protected","Maintenance"),
            ("PC-005","Cardiology","Workstation","Windows 11","At Risk","Active"),
            ("PC-006","Laboratory","Workstation","Windows 10","Needs Update","Active"),
        ]
        conn.executemany("""INSERT INTO devices
            (asset_name,department,device_type,os,security_status,status)
            VALUES (?,?,?,?,?,?)""", devices)
        tickets = [
            ("Printer connection issue","Administration","Medium","Open"),
            ("Workstation performance issue","Radiology","High","In Progress"),
            ("Security update required","Laboratory","High","Open"),
        ]
        conn.executemany("""INSERT INTO tickets
            (title,department,priority,status) VALUES (?,?,?,?)""", tickets)
    conn.commit()
    conn.close()
init_db()
@app.route("/")
def dashboard():
    conn = get_db()
    devices = conn.execute("SELECT * FROM devices ORDER BY id DESC").fetchall()
    tickets = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    stats = {
        "devices": conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0],
        "protected": conn.execute("SELECT COUNT(*) FROM devices WHERE security_status='Protected'").fetchone()[0],
        "attention": conn.execute("SELECT COUNT(*) FROM devices WHERE security_status!='Protected'").fetchone()[0],
        "open_tickets": conn.execute("SELECT COUNT(*) FROM tickets WHERE status!='Closed'").fetchone()[0],
    }
    conn.close()
    return render_template("dashboard.html", devices=devices, tickets=tickets, stats=stats)

@app.route("/add-device", methods=["POST"])
def add_device():
    data = [request.form.get(k, "").strip() for k in
            ("asset_name","department","device_type","os","security_status","status")]
    if data[0]:
        conn = get_db()
        conn.execute("""INSERT INTO devices
            (asset_name,department,device_type,os,security_status,status)
            VALUES (?,?,?,?,?,?)""", data)
        conn.commit()
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/add-ticket", methods=["POST"])
def add_ticket():
    data = [request.form.get(k, "").strip() for k in
            ("title","department","priority","status")]
    if data[0]:
        conn = get_db()
        conn.execute("INSERT INTO tickets (title,department,priority,status) VALUES (?,?,?,?)", data)
        conn.commit()
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/export")
def export():
    conn = get_db()
    rows = conn.execute("SELECT * FROM devices").fetchall()
    conn.close()
    lines = ["Asset,Department,Type,OS,Security Status,Status"]
    for r in rows:
        vals = [r["asset_name"],r["department"],r["device_type"],r["os"],r["security_status"],r["status"]]
        lines.append(",".join('"' + str(v).replace('"','""') + '"' for v in vals))
    from flask import Response
    return Response("\n".join(lines), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=devices.csv"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
