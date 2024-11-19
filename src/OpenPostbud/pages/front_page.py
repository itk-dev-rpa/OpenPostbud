from nicegui import ui

from OpenPostbud import ui_components


@ui.page("/")
def main_page():
    ui_components.header()
    ui.label("Velkommen til OpenPostbud").classes("text-4xl")
