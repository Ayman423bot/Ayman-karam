from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ATEF1112233")
DB = "elite.db"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS lessons(
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        grade TEXT NOT NULL, unit TEXT, content TEXT DEFAULT '',
        live_url TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS announcements(
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        body TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        grade TEXT NOT NULL, progress INTEGER DEFAULT 0)""")
    c.commit(); c.close()

def admin_required(f):
    @wraps(f)
    def w(*a, **kw):
        if not session.get("admin"): return redirect(url_for("admin_login"))
        return f(*a, **kw)
    return w

@app.route("/")
def home():
    c=db()
    lessons=c.execute("SELECT * FROM lessons ORDER BY id DESC").fetchall()
    anns=c.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    c.close()
    return render_template("index.html", lessons=lessons, announcements=anns)

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    error=""
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD:
            session["admin"]=True
            return redirect(url_for("admin"))
        error="كلمة المرور غير صحيحة"
    return render_template("login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.clear(); return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin():
    c=db()
    lessons=c.execute("SELECT * FROM lessons ORDER BY id DESC").fetchall()
    students=c.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    anns=c.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    c.close()
    return render_template("admin.html", lessons=lessons, students=students, announcements=anns)

@app.post("/admin/lesson")
@admin_required
def add_lesson():
    c=db(); c.execute("INSERT INTO lessons(title,grade,unit,content,live_url) VALUES(?,?,?,?,?)",
        (request.form["title"],request.form["grade"],request.form.get("unit",""),
         request.form.get("content",""),request.form.get("live_url","")))
    c.commit(); c.close(); return redirect(url_for("admin"))

@app.post("/admin/announcement")
@admin_required
def add_announcement():
    c=db(); c.execute("INSERT INTO announcements(title,body) VALUES(?,?)",
        (request.form["title"],request.form["body"])); c.commit(); c.close()
    return redirect(url_for("admin"))

@app.post("/admin/student")
@admin_required
def add_student():
    c=db(); c.execute("INSERT INTO students(name,grade,progress) VALUES(?,?,?)",
        (request.form["name"],request.form["grade"],int(request.form.get("progress",0))))
    c.commit(); c.close(); return redirect(url_for("admin"))

@app.post("/admin/delete/lesson/<int:i>")
@admin_required
def delete_lesson(i):
    c=db(); c.execute("DELETE FROM lessons WHERE id=?", (i,)); c.commit(); c.close()
    return redirect(url_for("admin"))

@app.post("/admin/delete/announcement/<int:i>")
@admin_required
def delete_announcement(i):
    c=db(); c.execute("DELETE FROM announcements WHERE id=?", (i,)); c.commit(); c.close()
    return redirect(url_for("admin"))

@app.post("/api/ai")
def ai():
    q=request.json.get("question","").strip()
    if not q: return jsonify(answer="اكتب سؤالك أولًا.")
    return jsonify(answer="مساعد ELITE AI التجريبي: أستطيع شرح القاعدة أو الكلمة خطوة بخطوة. في النسخة الإنتاجية اربطني بواجهة AI API حقيقية من إعدادات السيرفر.")

if __name__=="__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
