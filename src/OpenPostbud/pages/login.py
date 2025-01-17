from typing import Optional

from fastapi.responses import RedirectResponse
from nicegui import app, ui

from OpenPostbud import ui_components
from OpenPostbud.middleware import authentication
from OpenPostbud.database import users


@ui.page("/login")
def login_page() -> Optional[RedirectResponse]:
    ui_components.theme()
    if authentication.is_authenticated():
        return RedirectResponse("/")

    with ui.card().classes('absolute-center'):
        ui.label("Login").classes("text-2xl")
        username = ui.input("Brugernavn")
        password = ui.input("Kodeord", password=True)

        def func(): try_login(username.value, password.value)
        ui.button("Log ind", on_click=func)
        username.on("keydown.enter", func)
        password.on("keydown.enter", func)

    return None


def try_login(username: str, password: str):
    if users.verify_user(username, password):
        authentication.authenticate(username)
        ui.navigate.to(app.storage.user.get('referer_path', "/"))
    else:
        ui.notify("Forkert brugernavn eller kodeord", color='negative')
