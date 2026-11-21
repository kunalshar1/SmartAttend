import os
from flask import Flask, abort, redirect, url_for, render_template
from flask_login import (
    LoginManager,
    login_required,
    current_user
)
from functools import wraps
from routes.enrollment import enrollment_bp
from extensions import db
from models.user import User
from routes.auth import auth_bp
from models.student import Student
from routes.student import student_bp
from routes.teacher import teacher_bp
from models.subject import Subject
from routes.subject import subject_bp
from models.enrollment import Enrollment
from models.course import Course
from routes.course import course_bp
from routes.admin_reports import admin_reports_bp
from models.attendance import Attendance, AttendanceSession
app = Flask(__name__)
from routes.qr_attendance import qr_attendance_bp
from routes.admin_reports import admin_reports_bp
# Flask configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.register_blueprint(subject_bp)
app.register_blueprint(enrollment_bp)
app.register_blueprint(qr_attendance_bp)
app.register_blueprint(course_bp)
app.register_blueprint(admin_reports_bp)
# Role-based access control
def role_required(required_role):

    def decorator(function):

        @wraps(function)
        @login_required
        def wrapper(*args, **kwargs):

            if current_user.role != required_role:
                abort(403)

            return function(*args, **kwargs)

        return wrapper

    return decorator


# Initialize database
db.init_app(app)


# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Register authentication routes
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(teacher_bp)

# Home page
@app.route("/")
def home():

    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    return redirect(url_for("dashboard"))


# Dashboard redirection
@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    elif current_user.role == "teacher":
        return redirect(url_for("teacher_dashboard"))

    elif current_user.role == "student":
        return redirect(url_for("student_dashboard"))

    abort(403)


# Admin dashboard
@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


# Teacher dashboard
@app.route("/teacher/dashboard")
@role_required("teacher")
def teacher_dashboard():
    return render_template("teacher_dashboard.html")


# Student dashboard
@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():

    student = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if not student:
        return "Student profile not linked to this login account.", 404

    attendance_records = (
        Attendance.query
        .join(AttendanceSession)
        .filter(Attendance.student_id == student.id)
        .order_by(Attendance.marked_at.desc())
        .all()
    )

    total_classes = len(attendance_records)

    present = sum(
        1 for record in attendance_records
        if record.status == "Present"
    )

    absent = total_classes - present

    percentage = (
        round((present / total_classes) * 100, 2)
        if total_classes > 0 else 0
    )

    return render_template(
        "student_dashboard.html",
        student=student,
        attendance_records=attendance_records,
        total_classes=total_classes,
        present=present,
        absent=absent,
        percentage=percentage
    )


# Health check
@app.route("/health")
def health():
    return {
        "status": "success",
        "message": "SmartAttend AI backend is running!"
    }


# Create database tables
with app.app_context():
    db.create_all()
        # Add default courses if they do not exist
    default_courses = [
        "B.Tech CSE",
        "B.Tech IT",
        "B.Tech ECE",
        "B.Tech Mechanical",
        "BCA",
        "MCA"
    ]

    for course_name in default_courses:

        existing_course = Course.query.filter_by(
            course_name=course_name
        ).first()

        if not existing_course:
            db.session.add(
                Course(course_name=course_name)
            )

    db.session.commit()

    print("Default courses added successfully!")

    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)

    student_columns = [
        column["name"]
        for column in inspector.get_columns("student")
    ]

    if "user_id" not in student_columns:
        with db.engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE student ADD COLUMN user_id INTEGER")
            )

        print("Student user_id column added successfully!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)