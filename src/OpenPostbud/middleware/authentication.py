from datetime import datetime, timedelta
from typing import Callable, Awaitable
import os
import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


unrestricted_routes = {"/login", "/admin_login", "/auth/callback"}

AUTH_LIFETIME = int(os.environ["auth_lifetime_seconds"])


def authenticate(username: str, roles: list[str]):
    """Authenticate the current user session.
    Add the given username and roles to the session storage.
    """
    app.storage.user['authenticated'] = datetime.now().isoformat()
    app.storage.user['user_id'] = username
    app.storage.user["roles"] = roles


def is_authenticated() -> bool:
    """Check if the current user session is authenticated."""
    if 'authenticated' not in app.storage.user:
        return False

    if datetime.fromisoformat(app.storage.user['authenticated']) + timedelta(seconds=AUTH_LIFETIME) < datetime.now():
        return False

    return True


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
    """Get the admin token and delete the admin token file."""
    storage_path = _get_admin_token_path()

    if not storage_path.exists():
        return None

    with open(storage_path, 'r') as file:
        token = file.read()

    storage_path.unlink()

    return token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if (request.url.path in unrestricted_routes or
                request.url.path.startswith("/_nicegui") or
                is_authenticated()):
            return await call_next(request)

        app.storage.user['referer_path'] = request.url.path

        return RedirectResponse("/login")
