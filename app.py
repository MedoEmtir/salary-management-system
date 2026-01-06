from flask import Flask, render_template, session, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
import os

# =====================
# App config
# =====================
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

if not SECRET_KEY or not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("Missing environment variables")

app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =====================
# Database
# =====================
db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_salary = db.Column(db.Integer, nullable=False)
    paid_salary = db.Column(db.Integer, nullable=False)

    @property
    def remaining_salary(self):
        return self.total_salary - self.paid_salary

# =====================
# Permissions
# =====================
AUTHORIZED_EMAILS = [
    "manager1@gmail.com",
    "manager2@gmail.com"
]

ADMIN_EMAIL = "medo.emtir@gmail.com"

# =====================
# Google OAuth (FIXED ✅)
# =====================
google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["email", "profile"],   # ✅ لا openid
    redirect_url="/dashboard"
)

app.register_blueprint(google_bp, url_prefix="/login")

# =====================
# Routes
# =====================

@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v3/userinfo")
    if not resp.ok:
        return f"Google userinfo error: {resp.text}", 400

    email = resp.json().get("email")
    if not email:
        return "Email not returned from Google", 400

    session["email"] = email

    if email not in AUTHORIZED_EMAILS and email != ADMIN_EMAIL:
        return "Access Denied", 403

    return render_template("dashboard.html")

@app.route("/salaries")
def salaries():
    if session.get("email") not in AUTHORIZED_EMAILS and session.get("email") != ADMIN_EMAIL:
        abort(403)

    employees = Employee.query.all()
    is_admin = session.get("email") == ADMIN_EMAIL

    return render_template(
        "salaries.html",
        employees=employees,
        is_admin=is_admin
    )
@app.route("/add-employee", methods=["GET", "POST"])
def add_employee():
    # حماية: المدير فقط
    if session.get("email") != ADMIN_EMAIL:
        abort(403)

    if request.method == "POST":
        name = request.form["name"]
        total_salary = int(request.form["total_salary"])
        paid_salary = int(request.form["paid_salary"])

        employee = Employee(
            name=name,
            total_salary=total_salary,
            paid_salary=paid_salary
        )

        db.session.add(employee)
        db.session.commit()

        return redirect(url_for("salaries"))

    return render_template("add_employee.html")
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_salary(id):
    if session.get("email") != ADMIN_EMAIL:
        abort(403)

    employee = Employee.query.get_or_404(id)

    if request.method == "POST":
        employee.total_salary = int(request.form["total_salary"])
        employee.paid_salary = int(request.form["paid_salary"])
        db.session.commit()
        return redirect(url_for("salaries"))

    return render_template("edit_salary.html", employee=employee)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =====================
# Init DB
# =====================
with app.app_context():
    db.create_all()

# =====================
# Run
# =====================
if __name__ == "__main__":
    app.run(debug=True)

