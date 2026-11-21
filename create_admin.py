
from app import app
from extensions import db
from models.user import User
from getpass import getpass

with app.app_context():

    name = input("Enter admin name: ")
    email = input("Enter admin email: ").strip().lower()
    password = getpass("Enter admin password: ")

    existing = User.query.filter_by(email=email).first()

    if existing:
        print("This email is already registered.")
    elif len(password) < 8:
        print("Password must contain at least 8 characters.")
    else:
        admin = User(
            name=name,
            email=email,
            role="admin"
        )

        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print("Admin account created successfully!")
