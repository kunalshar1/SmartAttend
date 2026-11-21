from datetime import datetime
from extensions import db


class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    subject_id = db.Column(
        db.Integer, db.ForeignKey("subject.id"), nullable=False
    )

    teacher_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )

    course = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)

    token = db.Column(db.String(100), unique=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    subject = db.relationship("Subject")
    teacher = db.relationship("User")


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("attendance_session.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id"), nullable=False
    )

    status = db.Column(db.String(20), default="Present")
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship(
        "AttendanceSession",
        backref=db.backref("attendance_records", lazy=True)
    )

    student = db.relationship("Student")

    __table_args__ = (
        db.UniqueConstraint(
            "session_id",
            "student_id",
            name="unique_student_attendance_per_session"
        ),
    )