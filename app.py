from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
AUTHORIZED_EMAILS = [
    "manager1@gmail.com",
    "manager2@gmail.com"
]

ADMIN_EMAIL = "medo.emtir@gmail.com"
db = SQLAlchemy(app)

# 👇 لازم يكون هنا قبل أي route
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_salary = db.Column(db.Integer, nullable=False)
    paid_salary = db.Column(db.Integer, nullable=False)

    @property
    def remaining_salary(self):
        return self.total_salary - self.paid_salary
    

from flask import session

@app.before_request
def fake_login():
    session["email"] = "medo.emtir@gmail.com"

@app.route("/salaries")
def salaries():
    if session.get("email") not in AUTHORIZED_EMAILS and session.get("email") != ADMIN_EMAIL:
        return "Access Denied", 403

    employees = Employee.query.all()
    is_admin = session.get("email") == ADMIN_EMAIL

    return render_template(
        "salaries.html",
        employees=employees,
        is_admin=is_admin
    )
from flask import request, redirect, url_for, abort

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_salary(id):
    # حماية: التعديل لك إنت بس
    if session.get("email") != ADMIN_EMAIL:
        abort(403)

    employee = Employee.query.get_or_404(id)

    if request.method == "POST":
        # نحدّث القيم
        employee.total_salary = int(request.form["total_salary"])
        employee.paid_salary = int(request.form["paid_salary"])
        db.session.commit()

        return redirect(url_for("salaries"))

    return render_template("edit_salary.html", employee=employee)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)