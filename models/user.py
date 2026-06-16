from flask_login import UserMixin
from database.db import get_db

class User(UserMixin):
    def __init__(self, id, username, email, password_hash=None, google_id=None, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.google_id = google_id
        self.created_at = created_at

    @staticmethod
    def get(user_id):
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    google_id=row['google_id'],
                    created_at=row['created_at']
                )
            return None
        except Exception as e:
            print(f"Error fetching user by ID {user_id}: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    google_id=row['google_id'],
                    created_at=row['created_at']
                )
            return None
        except Exception as e:
            print(f"Error fetching user by email {email}: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_google_id(google_id):
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    google_id=row['google_id'],
                    created_at=row['created_at']
                )
            return None
        except Exception as e:
            print(f"Error fetching user by Google ID {google_id}: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def create(username, email, password_hash=None, google_id=None):
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, google_id) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, google_id)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return User.get(user_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
