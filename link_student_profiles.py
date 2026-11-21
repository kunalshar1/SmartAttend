
from app import app
from extensions import db
from models.user import User
from models.student import Student
from sqlalchemy import func

with app.app_context():

    students = Student.query.filter(
        Student.user_id.is_(None)
    ).all()

    linked = 0

    for student in students:

        user = User.query.filter(
            func.lower(User.email) == student.email.lower(),
            User.role == "student"
        ).first()

        if user:
            student.user_id = user.id
            linked += 1
            print(f"Linked: {student.name} - {student.email}")

    db.session.commit()

    print(f"\nSuccessfully linked {linked} student profiles.")
