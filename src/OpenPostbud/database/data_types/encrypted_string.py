"""This module contains a type decorator class for use in ORM models."""

import os

from sqlalchemy import Dialect, types
from cryptography.fernet import Fernet
import dotenv

dotenv.load_dotenv()

CIPHER = Fernet(os.environ['database_storage_secret'])


# pylint: disable=too-many-ancestors, abstract-method
class EncryptedString(types.TypeDecorator):
    """A type decorator used when defining sqlalchemy columns.
    This decorater automatically encrypts and decrypts data
    going to and from the database.
    """
    impl = types.BINARY
    cache_ok = False

    # pylint: disable=unused-argument
    def process_bind_param(self, value: str, dialect: Dialect) -> bytes:
        """Encrypt the value before writing to the database."""
        return CIPHER.encrypt(value.encode())

    # pylint: disable=unused-argument
    def process_result_value(self, value: bytes, dialect: Dialect) -> str:
        """Decrypt the value when retrieving from the database."""
        return CIPHER.decrypt(value).decode()
