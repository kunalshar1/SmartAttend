
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
import secrets

from extensions import db
from models.subject import Subject
from models.student import Student
from models.enrollment import Enrollment
from models.attendance import Attendance, AttendanceSession
from models.course import Course
from services.qr_generator import generate_qr_code


qr_attendance_bp = Blueprint(
    "qr_attendance",
    __name__,
    url_prefix="/teacher/attendance"
)


# Teacher - Start Attendance Session
@qr_attendance_bp.route("/start", methods=["GET", "POST"])
@login_required
def start_attendance():

    if current_user.role != "teacher":
        return "Access Denied", 403

    subjects = Subject.query.filter_by(
        teacher_id=current_user.id
    ).all()

    # Get all courses from Course Management
    courses = Course.query.order_by(
        Course.course_name
    ).all()

    # Available semesters
    semesters = [
        "1st", "2nd", "3rd", "4th",
        "5th", "6th", "7th", "8th"
    ]

    if request.method == "POST":

        subject_id = request.form.get("subject_id", type=int)
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()
        duration = request.form.get("duration", 10, type=int)

        # Validate assigned subject
        subject = Subject.query.filter_by(
            id=subject_id,
            teacher_id=current_user.id
        ).first()

        if not subject:
            flash("Please select a valid assigned subject.", "error")
            return redirect(url_for("qr_attendance.start_attendance"))

        # Validate course and semester against selected subject
        if subject.course != course or subject.semester != semester:
            flash(
                "Selected course and semester do not match this subject.",
                "error"
            )
            return redirect(url_for("qr_attendance.start_attendance"))

        # Validate selected course
        valid_course = Course.query.filter_by(
            course_name=course
        ).first()

        if not valid_course:
            flash("Please select a valid course.", "error")
            return redirect(url_for("qr_attendance.start_attendance"))

        # Validate semester
        if semester not in semesters:
            flash("Please select a valid semester.", "error")
            return redirect(url_for("qr_attendance.start_attendance"))

        # Validate QR duration
        if duration < 1 or duration > 60:
            flash("Duration must be between 1 and 60 minutes.", "error")
            return redirect(url_for("qr_attendance.start_attendance"))

        # Count eligible enrolled students
        eligible_students = (
            Enrollment.query
            .join(Student)
            .filter(
                Enrollment.subject_id == subject.id,
                Student.course == course,
                Student.semester == semester
            )
            .count()
        )

        if eligible_students == 0:
            flash(
                "No enrolled students found for this course and semester.",
                "error"
            )
            return redirect(url_for("qr_attendance.start_attendance"))

        # Generate secure attendance token
        token = secrets.token_urlsafe(32)

        # Store expiry as naive UTC for SQLite compatibility
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        attendance_session = AttendanceSession(
            subject_id=subject.id,
            teacher_id=current_user.id,
            course=course,
            semester=semester,
            token=token,
            expires_at=now_utc + timedelta(minutes=duration)
        )

        db.session.add(attendance_session)
        db.session.commit()

        # Generate attendance URL
        attendance_url = (
            request.host_url.rstrip("/")
            + url_for("qr_attendance.mark_attendance", token=token)
        )

        # Generate QR code image
        qr_path = generate_qr_code(attendance_url)

        # Convert expiry time from UTC to IST
        ist_expiry = attendance_session.expires_at.replace(
            tzinfo=timezone.utc
        ).astimezone(
            timezone(timedelta(hours=5, minutes=30))
        )

        # Calculate countdown
        remaining_seconds = max(
            0,
            int(
                (
                    attendance_session.expires_at
                    - datetime.now(timezone.utc).replace(tzinfo=None)
                ).total_seconds()
            )
        )

        return render_template(
            "attendance_session.html",
            session=attendance_session,
            subject=subject,
            qr_path=qr_path,
            eligible_students=eligible_students,
            ist_expiry=ist_expiry,
            remaining_seconds=remaining_seconds
        )

    return render_template(
        "start_attendance.html",
        subjects=subjects,
        courses=courses,
        semesters=semesters
    )


# Student - Scan QR and Mark Attendance
@qr_attendance_bp.route("/scan/<token>", methods=["GET", "POST"])
@login_required
def mark_attendance(token):

    if current_user.role != "student":
        return "Only students can mark attendance.", 403

    # Find attendance session
    attendance_session = AttendanceSession.query.filter_by(
        token=token
    ).first()

    if not attendance_session:
        return "Invalid QR code.", 404

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # Check session expiry
    if (
        not attendance_session.is_active
        or now_utc > attendance_session.expires_at
    ):
        return "This attendance session has expired.", 400

    # Find logged-in student's profile
    student = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if not student:
        return "Student profile not linked. Contact the administrator.", 403

    # Verify subject enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        subject_id=attendance_session.subject_id
    ).first()

    if not enrollment:
        return "You are not enrolled in this subject.", 403

    # Verify course and semester
    if (
        student.course != attendance_session.course
        or student.semester != attendance_session.semester
    ):
        return "This session is not for your course and semester.", 403

    # Check duplicate attendance
    existing = Attendance.query.filter_by(
        session_id=attendance_session.id,
        student_id=student.id
    ).first()

    if existing:
        return "Your attendance is already marked.", 400

    # Mark attendance
    if request.method == "POST":

        attendance = Attendance(
            session_id=attendance_session.id,
            student_id=student.id,
            status="Present"
        )

        db.session.add(attendance)

        try:
            db.session.commit()

            return render_template(
                "attendance_success.html",
                student=student,
                attendance_session=attendance_session
            )

        except IntegrityError:
            db.session.rollback()
            return "Your attendance is already marked.", 400

    return render_template(
        "scan_attendance.html",
        student=student,
        attendance_session=attendance_session
    )
