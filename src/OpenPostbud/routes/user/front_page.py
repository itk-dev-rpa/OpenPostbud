"""This module contains the front page."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components

router = APIRouter()


@router.page("/forside", name="Front Page")
def front_page():
    """Show the front page."""
    ui_components.header()
    ui.label("Velkommen til OpenPostbud").classes("text-4xl")
    ui.label("OpenPostbud er en webapplikation til at masseforsende Digital Post og NemSMS.")
    ui.label("Tryk på en af knapperne herunder for at begynde.")

    with ui.row():
        ui.button("Digital Post", on_click=lambda: ui.navigate.to(app.url_path_for("Shipment Overview")))
        ui.button("NemSMS", on_click=lambda: ui.navigate.to(app.url_path_for("NemSMS Overview")))
        ui.button("Tjek Tilmelding", on_click=lambda: ui.navigate.to(app.url_path_for("Registration Overview")))
