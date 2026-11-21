
from extensions import db


class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    course_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    def __repr__(self):
        return f"<Course {self.course_name}>"
