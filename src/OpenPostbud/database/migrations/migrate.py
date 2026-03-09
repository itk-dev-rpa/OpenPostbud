
import os
import hashlib
from pathlib import Path
import shutil

from OpenPostbud.database import connection


MIGRATIONS_FOLDER = Path("src/OpenPostbud/database/migrations/sql")


def perform_step(file_path: Path):
    """Perform the actions of one sql migration."""
    with connection.get_connection_engine().begin() as conn:
        sql = file_path.read_text()
        name = file_path.stem
        checksum = hashlib.sha1(sql.encode()).hexdigest()

        row = conn.exec_driver_sql("SELECT checksum FROM schema_migrations WHERE name=:n", {"n": name}).fetchone()
        if row:
            if row[0] != checksum:
                raise RuntimeError(f"Checksum has changed for step '{name}'")
            print(f"Skipping step '{name}'.")
            return

        for statement in sql.split("\n\n\n"):
            conn.exec_driver_sql(statement)

        conn.exec_driver_sql("INSERT INTO schema_migrations (name, checksum) VALUES (:n, :c)", {"n": name, "c": checksum})
        print(f"Applied step '{name}'")


def create_migrations_table():
    """Create a table in the database to track migrations."""
    with connection.get_connection_engine().begin() as conn:
        conn.exec_driver_sql(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            );"""
        )


def perform_migrations():
    """Perform all sql migrations in the migrations folder."""
    if Path(connection.DATABASE_PATH).exists():
        backup_path = Path(connection.DATABASE_PATH).with_suffix(".backup")
        shutil.copyfile(connection.DATABASE_PATH, backup_path)

    create_migrations_table()

    for file in sorted(MIGRATIONS_FOLDER.iterdir()):
        perform_step(file)
