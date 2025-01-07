from datetime import datetime, timedelta
from typing import Callable, Awaitable

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from OpenPostbud.database import audit_log


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not request.url.path.startswith("/_nicegui"):
            audit_log.add_log(app.storage.user.get("user_id", "none"), request.url.path)

        return await call_next(request)
