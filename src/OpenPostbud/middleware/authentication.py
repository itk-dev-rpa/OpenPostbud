from datetime import datetime, timedelta
from typing import Callable, Awaitable
import os

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


unrestricted_routes = {"/login"}

AUTH_LIFETIME = int(os.environ["auth_lifetime_seconds"])


def authenticate(username: str):
    expiry_time = (datetime.now() + timedelta(seconds=AUTH_LIFETIME))
    app.storage.user['authenticated'] = expiry_time.isoformat()
    app.storage.user['user_id'] = username


def is_authenticated() -> bool:
    if 'authenticated' not in app.storage.user:
        return False

    if datetime.fromisoformat(app.storage.user['authenticated']) < datetime.now():
        return False

    return True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if (request.url.path in unrestricted_routes or
                request.url.path.startswith("/_nicegui") or
                is_authenticated()):
            return await call_next(request)

        app.storage.user['referer_path'] = request.url.path

        return RedirectResponse("/login")
