"""This module contains the front page."""

from nicegui import ui

from OpenPostbud import ui_components


@ui.page("/")
def front_page():
    """Show the front page."""
    ui_components.header()
    ui.label("Velkommen til OpenPostbud").classes("text-4xl")
