import os

from sqlalchemy import Dialect, types
from cryptography.fernet import Fernet
import dotenv

dotenv.load_dotenv()


class EncryptedString(types.TypeDecorator):
    """A type decorator used when defining sqlalchemy columns.
    This decorater automatically encrypts and decrypts data
    going to and from the database.
    """
    impl = types.BINARY
    cache_ok = False
    cipher = Fernet(os.environ['database_storage_secret'])

    def process_bind_param(self, value: str, dialect: Dialect) -> bytes:
        return self.cipher.encrypt(value.encode())

    def process_result_value(self, value: bytes, dialect: Dialect) -> str:
        return self.cipher.decrypt(value).decode()
