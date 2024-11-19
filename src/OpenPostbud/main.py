import os

import dotenv
from nicegui import ui, app

from OpenPostbud.database import connection
from OpenPostbud.middleware.authentication import AuthMiddleware
from OpenPostbud.middleware.audit_log import AuditMiddleware
from OpenPostbud.pages import front_page, login, send_post, forsendelser
from OpenPostbud.pages.tilmeldinger import opret_tilmelding, tjek_tilmelding


def main():
    dotenv.load_dotenv()
    connection.create_tables()
    app.add_middleware(AuthMiddleware)
    app.add_middleware(AuditMiddleware)
    ui.run(storage_secret=os.environ["nicegui_storage_secret"], title="OpenPostbud", favicon="📯")


if __name__ in {'__main__', '__mp_main__'}:
    main()
