"""This module is the main entry point for the web application."""

import os

import dotenv
from nicegui import ui, app

from OpenPostbud.database import connection
from OpenPostbud.middleware.authentication import AuthMiddleware
from OpenPostbud.middleware.audit_log import AuditMiddleware
from OpenPostbud.pages import front_page, login, admin_login  # noqa: F401  pylint: disable=unused-import
from OpenPostbud.pages.forsendelser import forsendelser, send_post  # noqa: F401  pylint: disable=unused-import
from OpenPostbud.pages.tilmeldinger import opret_tilmelding, tjek_tilmelding  # noqa: F401  pylint: disable=unused-import


def main(reload: bool = True):
    """Initialize and start the web application.

    Args:
        reload: Whether to reload the server on code changes. Defaults to True.
    """
    dotenv.load_dotenv()
    connection.create_tables()
    app.add_middleware(AuthMiddleware)
    app.add_middleware(AuditMiddleware)
    ui.run(
        title="OpenPostbud", favicon="📯",
        storage_secret=os.environ["nicegui_storage_secret"],
        reload=reload,
        port=8000,
        ssl_certfile=os.getenv("ssl_certfile"),
        ssl_keyfile=os.getenv("ssl_keyfile")
    )


if __name__ in {'__main__', '__mp_main__'}:
    main()
