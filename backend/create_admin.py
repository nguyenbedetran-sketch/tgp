#!/usr/bin/env python3
"""
Create (or reset the password of) an admin account for the management
dashboard. Run this interactively - the password is never stored in .env
or in source control.

Usage:
    cd backend
    python create_admin.py
"""
import getpass
import re
import sys

from app import create_app
from app.models.db import get_db
from app.services.security import hash_password

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def main():
    app = create_app()
    with app.app_context():
        username = input("Ten dang nhap admin: ").strip()
        if not username:
            print("Ten dang nhap khong duoc de trong.")
            sys.exit(1)

        email = input("Email: ").strip()
        if not EMAIL_RE.match(email):
            print("Email khong hop le.")
            sys.exit(1)

        full_name = input("Ho ten hien thi: ").strip()

        password = getpass.getpass("Mat khau (toi thieu 8 ky tu): ")
        if len(password) < 8:
            print("Mat khau qua ngan (toi thieu 8 ky tu).")
            sys.exit(1)
        confirm = getpass.getpass("Nhap lai mat khau: ")
        if password != confirm:
            print("Mat khau nhap lai khong khop.")
            sys.exit(1)

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
        ).fetchone()

        password_hash, salt = hash_password(password)

        if existing:
            db.execute(
                "UPDATE users SET password_hash = ?, password_salt = ?, full_name = ?, is_active = 1 WHERE id = ?",
                (password_hash, salt, full_name, existing["id"]),
            )
            db.commit()
            print(f"Da cap nhat mat khau cho tai khoan '{username}'.")
        else:
            db.execute(
                """INSERT INTO users (username, email, password_hash, password_salt, full_name, role)
                   VALUES (?, ?, ?, ?, ?, 'admin')""",
                (username, email, password_hash, salt, full_name),
            )
            db.commit()
            print(f"Da tao tai khoan admin moi: '{username}'.")


if __name__ == "__main__":
    main()
