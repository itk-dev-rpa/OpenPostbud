"""This module contains functions for creating ids for use in ORM models."""

import secrets
from collections.abc import Callable


def create_id(prefix: str, length: int) -> Callable[[], str]:
    def func():
        CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
        return prefix + "".join(secrets.choice(CHARACTERS) for _ in range(length))

    return func
