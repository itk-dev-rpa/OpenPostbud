"""This module is the main entry point for the web application."""

import asyncio

from nicegui import ui, app
from fastapi.responses import RedirectResponse

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post import shipments
from OpenPostbud.database.check_registration import registration_job
from OpenPostbud.routes.user.router import router as user_router
from OpenPostbud.routes.api.router import router as api_router
from OpenPostbud.routes.auth.router import router as auth_router
from OpenPostbud.routes.admin.router import router as admin_router
from OpenPostbud.middleware.audit_log import AuditMiddleware
from OpenPostbud.middleware.authentication import AuthMiddleware


@ui.page("/")
def page():
    """Redirect the base path to the login page."""
    return RedirectResponse(app.url_path_for("Login"))


def main():
    """Initialize and start the web application.

    Args:
        reload: Whether to reload the server on code changes. Defaults to True.
    """
    connection.create_tables()
    app.include_router(user_router)
    app.include_router(api_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(AuthMiddleware)

    app.on_startup(cleanup_loop)

    ui.run(
        title="OpenPostbud", favicon="📯",
        storage_secret=config.NICEGUI_STORAGE_SECRET,
        reload=config.APP_RELOAD,
        port=8000,
        fastapi_docs=True,
        show=False
    )


async def cleanup_loop():
    """This function runs once every day deleting old
    data from the database.
    """
    while True:
        shipments.delete_old_shipments()
        registration_job.delete_old_registration_jobs()
        await asyncio.sleep(60)


if __name__ in {'__main__', '__mp_main__'}:
    main()
