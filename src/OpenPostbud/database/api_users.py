"""This module handles the creation and verification of api users."""

from __future__ import annotations

from datetime import datetime
import secrets
import re

from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class ApiUser(Base):
    """An ORM class representing an api user."""
    __tablename__ = "ApiUsers"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    key_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    active: Mapped[bool] = mapped_column(default=True)

    def to_row_dict(self) -> dict[str, str]:
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "active": {True: "Aktiv", False: "Inaktiv"}[self.active]
        }


def get_api_users() -> tuple[ApiUser]:
    """Get all api users in the database."""
    with connection.get_session() as session:
        result = session.execute(select(ApiUser)).scalars()
        return tuple(result)


def create_api_user(name: str) -> str:
    """Add a new api user to the database with the given name.
    A random api key is generated for the new user.

    Args:
        name: The name of the new api user.

    Returns:
        The complete api key to be used in api calls.
    """
    id = secrets.token_urlsafe(8)
    key = secrets.token_urlsafe(32)

    user = ApiUser(
        id=id,
        name=name,
        key_hash=pbkdf2_sha256.hash(key)
    )

    with connection.get_session() as session:
        session.add(user)
        session.commit()

    return f"{id}.{key}"


def delete_api_user(user_id: str):
    """Delete the api user with the given id."""
    with connection.get_session() as session:
        user = session.get(ApiUser, user_id)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False


def verify_api_key(api_key: str) -> ApiUser | None:
    """Verify an api key against the database.

    Args:
        api_key: The api key to verify

    Returns:
        Returns the api user if the key is valid.
    """
    # The api key is assumed to be of the form "id.key"
    if not re.fullmatch(r"[\w-]+\.[\w-]+", api_key):
        return False

    id, key = api_key.split(".")

    with connection.get_session() as session:
        user = session.get(ApiUser, id)

    if user and user.active and pbkdf2_sha256.verify(key, user.key_hash):
        return user

    return None


if __name__ == "__main__":
    print(create_api_user("Test Api User"))
