from flask import Flask, request, jsonify, send_from_directory
import sqlite3, os, smtplib
from email.message import EmailMessage

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'enquiries.db')

# Email Configuration
ADMIN_KEY = "admin123"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "vechanarendra3@gmail.com"
SMTP_PASS = "abcd efgh ijkl mnop"  # Replace with your real 16-character app password
CONTACT_TO = "vechanarendra3@gmail.com"

app = Flask(__name__, static_folder=BASE, static_url_path='')

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS enquiries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        service TEXT,
        message TEXT,
        status TEXT DEFAULT "Pending",
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def send_email(to_address, subject, body):
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_USER
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Email Error:", e)
        return False

@app.route("/")
def home():
    return send_from_directory(BASE, "index.html")

@app.route("/status")
def status_page():
    return send_from_directory(BASE, "status.html")

@app.route("/api/submit", methods=["POST"])
def submit():
    d = request.get_json()

    name = d.get("name","")
    email = d.get("email","")
    phone = d.get("phone","")
    service = d.get("service","")
    message = d.get("message","")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO enquiries(name,email,phone,service,message) VALUES(?,?,?,?,?)",
              (name,email,phone,service,message))
    conn.commit()
    new_id = c.lastrowid
    conn.close()

    # Email to Admin
    send_email(CONTACT_TO, f"New Enquiry #{new_id}",
               f"New enquiry received.\nID: {new_id}\nName: {name}\nPhone: {phone}\nMessage:\n{message}")

    # Email to Customer
    if email:
        send_email(email, "SDVVL — Enquiry Received",
                   f"Hi {name},\nYour enquiry was received.\nTracking ID: {new_id}")

    return jsonify({"ok":True,"id":new_id})

@app.route("/api/enquiries")
def all_entries():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute("SELECT id,name,email,phone,service,message,status,created FROM enquiries ORDER BY id DESC").fetchall()
    conn.close()

    data=[]
    for r in rows:
        data.append({
            "id":r[0],"name":r[1],"email":r[2],"phone":r[3],
            "service":r[4],"message":r[5],"status":r[6],"created":r[7]
        })
    return jsonify(data)

@app.route("/api/enquiry/<int:id>")
def track(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    r = c.execute("SELECT status,message FROM enquiries WHERE id=?",(id,)).fetchone()
    conn.close()

    if not r: return jsonify({"error":"Not found"}),404
    return jsonify({"status":r[0],"message":r[1]})

@app.route("/api/update-status", methods=["POST"])
def update_status():
    d = request.get_json()

    if d.get("key") != ADMIN_KEY:
        return jsonify({"error":"Invalid admin key"}),401

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE enquiries SET status=? WHERE id=?",(d["status"],d["id"]))
    conn.commit()
    conn.close()

    return jsonify({"ok":True})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
