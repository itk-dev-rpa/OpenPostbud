"""This module contains middleware for the audit log."""

from typing import Callable, Awaitable

from fastapi import Request
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from OpenPostbud.database import audit_log


class AuditMiddleware(BaseHTTPMiddleware):
    """This middleware adds a log every time a user tries to access a URL."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """The dispatch function fo the middleware.
        Add the request path and the logged in user (if any) to the audit log.
        """
        # Don't include internal resource paths
        if not request.url.path.startswith("/_nicegui"):
            audit_log.add_log(app.storage.user.get("user_id", "none"), request.url.path)

        return await call_next(request)
