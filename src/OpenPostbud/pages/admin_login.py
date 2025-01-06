from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from nicegui import ui

from OpenPostbud.middleware import authentication


@ui.page("/admin_login")
def admin_login(token: str) -> RedirectResponse:

    if authentication.get_admin_token() == token:
        authentication.authenticate("ADMIN")
        return RedirectResponse("/")

    raise HTTPException(401, "Invalid admin token")
