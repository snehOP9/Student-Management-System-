from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "secret"

users = {
    "admin1": {"password": generate_password_hash("adminpass"), "role": "admin"}
}
students = []
teachers = []

def add_user(username, password, role):
    users[username] = {"password": generate_password_hash(password), "role": role}
    if role == "teacher":
        teachers.append({"username": username})
    if role == "student":
        students.append({
            "username": username,
            "roll": "", "branch": "", "email": "", "phone": "",
            "dob": "", "guardian": "", "attendance": 0,
            "fees_paid": False,
            "subjects": {"Math": 0, "Physics": 0, "Chemistry": 0}
        })

def send_otp_to_email(recipient_email, otp_code):
    msg = MIMEText(f"Your OTP for Student Management System is: {otp_code}")
    msg["Subject"] = "Reset Password OTP"
    msg["From"] = "youremail@example.com"
    msg["To"] = recipient_email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("youremail@example.com", "your-app-password")
            server.send_message(msg)
    except:
        pass

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        if "admin1" in users and check_password_hash(users["admin1"]["password"], request.form["password"]):
            session["user"] = "admin1"
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials", "danger")
    return render_template("login_admin.html")

@app.route("/login/teacher", methods=["GET", "POST"])
def login_teacher():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in users and users[u]["role"] == "teacher" and check_password_hash(users[u]["password"], p):
            session["user"] = u
            session["role"] = "teacher"
            return redirect(url_for("teacher_dashboard"))
        flash("Invalid teacher credentials", "danger")
    return render_template("login_teacher.html")

@app.route("/login/student", methods=["GET", "POST"])
def login_student():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in users and users[u]["role"] == "student" and check_password_hash(users[u]["password"], p):
            session["user"] = u
            session["role"] = "student"
            return redirect(url_for("student_dashboard"))
        flash("Invalid student credentials", "danger")
    return render_template("login_student.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("home"))
    return render_template("admin_dashboard.html", students=students, teachers=teachers)

@app.route("/admin/add_student", methods=["GET", "POST"])
def admin_add_student():
    if session.get("role") != "admin":
        return redirect(url_for("home"))
    if request.method == "POST":
        un = request.form["username"]
        pw = request.form["password"]
        add_user(un, pw, "student")
        s = next(s for s in students if s["username"] == un)
        s.update({
            "roll": request.form.get("roll", ""),
            "branch": request.form.get("branch", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "dob": request.form.get("dob", ""),
            "guardian": request.form.get("guardian", "")
        })
        return redirect(url_for("admin_dashboard"))
    return render_template("add_student.html")

@app.route("/admin/add_teacher", methods=["GET", "POST"])
def admin_add_teacher():
    if session.get("role") != "admin":
        return redirect(url_for("home"))
    if request.method == "POST":
        add_user(request.form["username"], request.form["password"], "teacher")
        return redirect(url_for("admin_dashboard"))
    return render_template("add_teacher.html")

@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect(url_for("home"))
    return render_template("teacher_dashboard.html", students=students)

@app.route("/teacher/update/<username>", methods=["GET", "POST"])
def teacher_update(username):
    if session.get("role") not in ["teacher", "admin"]:
        return redirect(url_for("home"))
    st = next((s for s in students if s["username"] == username), None)
    if not st:
        return redirect(url_for("teacher_dashboard"))
    if request.method == "POST":
        st["subjects"]["Math"] = int(request.form.get("math", 0))
        st["subjects"]["Physics"] = int(request.form.get("physics", 0))
        st["subjects"]["Chemistry"] = int(request.form.get("chemistry", 0))
        st["attendance"] = int(request.form.get("attendance", 0))
        st["fees_paid"] = request.form.get("fees_paid") == "on"
        return redirect(url_for("teacher_dashboard"))
    return render_template("update_record.html", student=st)

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("home"))
    me = next(s for s in students if s["username"] == session["user"])
    return render_template("student_dashboard.html", student=me)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        session["reset_username"] = username
        otp = str(random.randint(100000, 999999))
        session["otp"] = otp
        send_otp_to_email(email, otp)
        return redirect(url_for("verify_otp"))
    return render_template("forgot_password.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        if request.form["otp_input"] == session.get("otp"):
            return redirect(url_for("reset_password"))
        flash("Invalid OTP", "danger")
    return render_template("verify_otp.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        user = session.get("reset_username")
        new_pw = request.form["new_password"]
        if user in users:
            users[user]["password"] = generate_password_hash(new_pw)
            flash("Password updated. Please login.", "success")
            return redirect(url_for("home"))
    return render_template("reset_password.html")

if __name__ == "__main__":
    app.run(debug=True)
