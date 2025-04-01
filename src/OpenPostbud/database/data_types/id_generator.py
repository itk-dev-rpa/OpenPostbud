"""This module contains functions for creating ids for use in ORM models."""

import secrets
from collections.abc import Callable


def create_id(prefix: str, length: int) -> Callable[[], str]:
    """Return a function that creates random ids with the given prefix and length.
    The total length is the prefix length + length.

    Args:
        prefix: The prefix for the created ids.
        length: The number of random characters to add.

    Returns:
        A function that creates random ids when called.
    """    """"""
    def func():
        characters = "abcdefghijklmnopqrstuvwxyz0123456789"
        return prefix + "".join(secrets.choice(characters) for _ in range(length))

    return func
