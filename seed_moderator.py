import os
from getpass import getpass
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import Moderator

app = create_app()

with app.app_context():
    username = input("Moderator username: ").strip()
    password = getpass("Moderator password: ")

    if not username or not password:
        raise SystemExit("Username and password cannot be empty.")

    existing = Moderator.query.filter_by(username=username).first()
    if existing:
        raise SystemExit("A moderator with that username already exists.")

    moderator = Moderator(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(moderator)
    db.session.commit()
    print(f"Moderator '{username}' created successfully.")
