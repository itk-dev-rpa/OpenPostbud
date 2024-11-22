from __future__ import annotations

from datetime import datetime

from passlib.hash import pbkdf2_sha256 as hasher
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class User(Base):
    __tablename__ = "Users"

    username: Mapped[str] = mapped_column(primary_key=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    active: Mapped[bool] = mapped_column(default=True)


def add_user(username: str, password: str):
    """Add a new user to the database with the given username and password.

    Args:
        username: The username of the new user.
        password: The password of the new user.
    """
    user = User(
        username=username,
        password_hash=hasher.hash(password)
    )

    with connection.get_session() as session:
        session.add(user)
        session.commit()


def verify_user(username: str, password: str) -> bool:
    """Verify a username and password against active users in the database.

    Args:
        username: The username to verify.
        password: The password to verify.

    Returns:
        True if the username and password match and the user is still active.
    """
    with connection.get_session() as session:
        user = session.get(User, username)

    if not user:
        return False

    if not user.active:
        return False

    if hasher.verify(password, user.password_hash):
        return True

    return False


if __name__ == "__main__":
    add_user("User2", "Pass")
