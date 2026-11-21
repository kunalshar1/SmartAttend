
from extensions import db


class Enrollment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    student = db.relationship("Student", backref="enrollments")

    subject = db.relationship("Subject", backref="enrollments")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "subject_id",
            name="unique_student_subject"
        ),
    )

    def __repr__(self):
        return f"<Enrollment Student:{self.student_id} Subject:{self.subject_id}>"
