from app import db

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_salary = db.Column(db.Integer, nullable=False)
    paid_salary = db.Column(db.Integer, nullable=False)

    @property
    def remaining_salary(self):
        return self.total_salary - self.paid_salary