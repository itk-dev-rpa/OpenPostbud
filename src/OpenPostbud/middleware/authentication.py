"""This module handles authentication of users and contains middleware to check authentication."""

from datetime import datetime, timedelta
from typing import Callable, Awaitable
import uuid
from pathlib import Path

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from OpenPostbud import config

AUTH_EXPIRY_KEY = 'auth_expiery_time'
AUTH_USER_KEY = 'user_id'
ROLES_KEY = 'roles'


def authenticate(username: str, roles: list[str]):
    """Authenticate the current user session.
    Add the given username and roles to the session storage.
    """
    expiry_time = (datetime.now() + timedelta(seconds=config.AUTH_LIFETIME_SECONDS))
    app.storage.user[AUTH_EXPIRY_KEY] = expiry_time.isoformat()
    app.storage.user[AUTH_USER_KEY] = username
    app.storage.user[ROLES_KEY] = roles


def is_authenticated() -> bool:
    """Check if the current user session is authenticated by
    checking the expiry time of authentication if any.
    """
    if AUTH_EXPIRY_KEY not in app.storage.user:
        return False

    if datetime.fromisoformat(app.storage.user[AUTH_EXPIRY_KEY]) < datetime.now():
        return False

    return True


def is_admin() -> bool:
    """Check if the logged in user has the admin role."""
    if not is_authenticated():
        return False

    if config.ADMIN_ROLE_NAME not in get_current_user_roles():
        return False

    return True


def logout():
    """Logout the current user and navigate to the login screen."""
    app.storage.user.clear()
    ui.navigate.to(app.url_path_for("Login"))  # pylint: disable=no-member


def get_current_user() -> str:
    """Get the current logged in user."""
    return app.storage.user[AUTH_USER_KEY]


def get_current_user_roles() -> list[str]:
    """Get the roles of the current logged in user."""
    return app.storage.user[ROLES_KEY]


def grant_admin_access():
    """Generate a new admin token and present it in the console."""
    token = str(uuid.uuid4())
    set_admin_token(token)
    print(f"Go to /auth/admin-login?token={token}")


def _get_admin_token_path() -> Path:
    """Get the path to the admin token file."""
    return Path("admin_token").resolve()


def set_admin_token(token: str):
    """Write a token to the admin token file."""
    storage_path = _get_admin_token_path()

    with open(storage_path, 'w', encoding="utf-8") as file:
        file.write(token)


def get_admin_token() -> str | None:
    """Get the admin token and delete the admin token file.
    The file is deleted to prevent reuse and brute force attacks.
    """
    storage_path = _get_admin_token_path()

    if not storage_path.exists():
        return None

    with open(storage_path, 'r', encoding="utf-8") as file:
        token = file.read()

    storage_path.unlink()

    return token


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware checks for authentication whenever a user
    tries to access a URL."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """The dispatch function fo the middleware.
        Check if the request URL needs user authentication and if the user is authenticated.
        Redirect to the login page if the user is not authenticated for the URL.
        """
        # Import here to avoid circular imports
        # pylint: disable=import-outside-toplevel,cyclic-import
        from OpenPostbud.routes.user.router import router as user_router
        from OpenPostbud.routes.admin.router import router as admin_router

        if request.url.path.startswith(user_router.prefix) and not is_authenticated():
            # Store the request path for later redirection
            app.storage.user['referer_path'] = request.url.path
            return RedirectResponse(app.url_path_for("Login"))

        if request.url.path.startswith(admin_router.prefix) and not is_admin():
            raise HTTPException(401, "Admin access denied.")

        return await call_next(request)
