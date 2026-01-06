from flask import Flask, render_template, session, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
import os

# =====================
# App config
# =====================
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

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
# Google OAuth
# =====================
google_bp = make_google_blueprint(
    scope=["profile", "email"],
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

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info", 400

    email = resp.json().get("email")
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
# Run app
# =====================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
