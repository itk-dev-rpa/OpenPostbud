"""This module contains the front page."""

from nicegui import ui, APIRouter

from OpenPostbud import ui_components

router = APIRouter()

@router.page("/forside", name="Front Page")
def front_page():
    """Show the front page."""
    ui_components.header()
    ui.label("Velkommen til OpenPostbud").classes("text-4xl")
