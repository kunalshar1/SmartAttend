
from extensions import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    course = db.Column(db.String(100))
    semester = db.Column(db.String(20))

    # Connect student profile with login account
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=True
    )

    user = db.relationship("User", backref="student_profile", uselist=False)

    def __repr__(self):
        return f"<Student {self.roll_number}>"
