"""This module is the main entry point for the web application."""

import os

import dotenv
from nicegui import ui, app

from OpenPostbud.database import connection
from OpenPostbud.routes.user.router import router as user_router
from OpenPostbud.routes.api.router import router as api_router
from OpenPostbud.routes.auth.router import router as auth_router
from OpenPostbud.middleware.audit_log import AuditMiddleware
from OpenPostbud.middleware.authentication import AuthMiddleware


@ui.page("/")
def page():
    """Redirect the base path to the login page."""
    ui.navigate.to(app.url_path_for("Login"))


def main(reload: bool = True):
    """Initialize and start the web application.

    Args:
        reload: Whether to reload the server on code changes. Defaults to True.
    """
    dotenv.load_dotenv()
    connection.create_tables()
    app.include_router(user_router)
    app.include_router(api_router)
    app.include_router(auth_router)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(AuthMiddleware)

    options = {}
    if "ssl_certfile" in os.environ:
        options["ssl_certfile"] = os.environ["ssl_certfile"]
        options["ssl_keyfile"] = os.environ["ssl_keyfile"]

    ui.run(
        title="OpenPostbud", favicon="📯",
        storage_secret=os.environ["nicegui_storage_secret"],
        reload=reload,
        port=8000,
        fastapi_docs=True,
        show=False,
        **options
    )


if __name__ in {'__main__', '__mp_main__'}:
    main()
