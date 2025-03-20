"""This module contains a type decorator class for use in ORM models."""

import hashlib

from sqlalchemy import Dialect, types


# pylint: disable=too-many-ancestors, abstract-method
class ObfuscatedId(types.TypeDecorator):
    """A type decorator used when defining sqlalchemy columns.
    This decorater automatically obfuscates incremental integer ids.
    """
    impl = types.INTEGER
    cache_ok = True

    def __init__(self, prefix: str):
        """Initialise a new Obfuscator.

        Args:
            prefix: The prefix and salt to use on obfuscated ids.
        """
        super().__init__()
        self.prefix = prefix

    # pylint: disable=unused-argument
    def process_bind_param(self, value: str, dialect: Dialect) -> int:
        """Convert to incremental int before sending to database."""
        s = value.replace(self.prefix, "", 1)
        n = int(s)
        cipher = _feistel_cipher(n, self.prefix)
        return cipher

    # pylint: disable=unused-argument
    def process_result_value(self, value: int, dialect: Dialect) -> str:
        """Convert to obfuscated string when fetching from database."""
        cipher = _feistel_cipher(value, self.prefix)
        return self.prefix + str(cipher)


def _feistel_cipher(number: int, salt: str) -> int:
    """A simplified Feistel cipher which uses the
    hash function as the rounds function.
    The cipher is its own inverse:
    E.g.: 2 -> 154782 -> 2

    Args:
        number: The number to cipher. Max 32 bits.
        salt: A string used to create different cipher sets.

    Returns:
        A 32 bit cipher of the input number.
    """
    left = (number >> 16) & 0xFFFF
    right = number & 0xFFFF

    for _ in range(2):
        new_right = left ^ _rounds_function(right, salt)
        left, right = right, new_right

    return (right << 16) | left


def _rounds_function(value: int, salt: str) -> int:
    """A rounds function used for the Feistel Cipher."""
    byte_string = (str(value)+salt).encode()
    hash_bytes = hashlib.sha1(byte_string, usedforsecurity=False).digest()
    return int.from_bytes(hash_bytes) % 0x10000
