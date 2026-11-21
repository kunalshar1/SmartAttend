
from extensions import db


class Subject(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    subject_name = db.Column(
        db.String(100),
        nullable=False
    )

    subject_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    course = db.Column(db.String(100))

    semester = db.Column(db.String(20))

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    teacher = db.relationship(
        "User",
        backref="assigned_subjects"
    )

    def __repr__(self):
        return f"<Subject {self.subject_code}>"
