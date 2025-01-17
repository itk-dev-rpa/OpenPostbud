"""This module handles authentication of users and contains middleware to check authentication."""

from datetime import datetime, timedelta
from typing import Callable, Awaitable
import os
import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


unrestricted_routes = {"/login", "/admin_login"}

AUTH_LIFETIME = int(os.environ["auth_lifetime_seconds"])
AUTH_EXPIRY_KEY = 'auth_expiery_time'
AUTH_USER_KEY = 'user_id'


def authenticate(username: str):
    """Authenticate the current user session.
    Add the given username to the session storage.
    """
    expiry_time = (datetime.now() + timedelta(seconds=AUTH_LIFETIME))
    app.storage.user[AUTH_EXPIRY_KEY] = expiry_time.isoformat()
    app.storage.user[AUTH_USER_KEY] = username


def is_authenticated() -> bool:
    """Check if the current user session is authenticated by
    checking the expiry time of authentication if any.
    """
    if AUTH_EXPIRY_KEY not in app.storage.user:
        return False

    if datetime.fromisoformat(app.storage.user[AUTH_EXPIRY_KEY]) < datetime.now():
        return False

    return True


def logout():
    """Logout the current user and navigate to the login screen."""
    app.storage.user.clear()
    ui.navigate.to("/login")


def get_current_user() -> str:
    """Get the current logged in user."""
    return app.storage.user[AUTH_USER_KEY]


def grant_admin_access():
    """Generate a new admin token and present it in the console."""
    token = str(uuid.uuid4())
    set_admin_token(token)
    print(f"Go to /admin_login?token={token}")


def _get_admin_token_path() -> Path:
    """Get the path to the admin token file."""
    return Path(os.environ.get('NICEGUI_STORAGE_PATH', '.nicegui')).resolve() / Path("admin_token")


def set_admin_token(token: str):
    """Write a token to the admin token file."""
    storage_path = _get_admin_token_path()

    with open(storage_path, 'w') as file:
        file.write(token)


def get_admin_token() -> str | None:
    """Get the admin token and delete the admin token file.
    The file is deleted to prevent reuse or brute force attacks.
    """
    storage_path = _get_admin_token_path()

    if not storage_path.exists():
        return None

    with open(storage_path, 'r') as file:
        token = file.read()

    storage_path.unlink()

    return token


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware checks for authentication whenever a user tries to access a URL."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """The dispatch function fo the middleware.
        Check if the request URL needs authentication and if the user is authenticated.
        Redirect to the login page if the user is not authenticated for the URL.
        """
        if (request.url.path in unrestricted_routes or
                request.url.path.startswith("/_nicegui") or
                is_authenticated()):
            return await call_next(request)

        # Store the request path for later redirection
        app.storage.user['referer_path'] = request.url.path

        return RedirectResponse("/login")
