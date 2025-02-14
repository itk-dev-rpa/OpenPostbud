from __future__ import annotations

from datetime import datetime
import secrets
import re

from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class ApiUser(Base):
    __tablename__ = "ApiUsers"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    key_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    active: Mapped[bool] = mapped_column(default=True)


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


def verify_api_key(api_key: str) -> bool:
    """Verify an api key against the database.

    Args:
        api_key: The api key to verify

    Returns:
        True if the key is valid and the user is still active.
    """
    # The api key is assumed to be of the form "id.key"
    if not re.fullmatch(r"[\w-]+\.[\w-]+", api_key):
        return False

    id, key = api_key.split(".")

    with connection.get_session() as session:
        user = session.get(ApiUser, id)

    if not user:
        return False

    if not user.active:
        return False

    if pbkdf2_sha256.verify(key, user.key_hash):
        return True

    return False


if __name__ == "__main__":
    print(create_api_user("Test Api User"))
