import sqlite3
import os

# On Render: set DB_PATH env var to a persistent disk location
# e.g. /var/data/startup_validator.db
# Locally: uses database/startup_validator.db
_default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'startup_validator.db')
DB_PATH = os.getenv("DB_PATH", _default_path)

def get_db():
    """
    Returns an open SQLite database connection with Row factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """
    Initializes the database using schema.sql.
    Creates the DB file and all tables if they don't exist.
    """
    # Ensure the directory for DB_PATH exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    conn = get_db()
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print(f"Database initialized at: {DB_PATH}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
