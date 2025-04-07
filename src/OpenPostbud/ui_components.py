"""This module contains reusable UI components."""

from nicegui import ui, app

from OpenPostbud.middleware import authentication

HORIZONTAL_RULE = '<hr style="width: 2px; height: 1.75rem; display: inline-block; background: white">'


def header():
    """Show a NiceGUI header with links to other pages."""
    theme()

    with ui.header():
        logo = ui.label("📯 OpenPostbud 📯").classes("text-3xl text-bold cursor-pointer")
        logo.on("click", lambda: ui.navigate.to(app.url_path_for("Front Page")))  # pylint: disable=no-member

        ui.link("Forside", app.url_path_for("Front Page")).classes(replace='text-lg text-white')
        ui.html(HORIZONTAL_RULE)
        ui.link("Ny Forsendelse", app.url_path_for("Send Post")).classes(replace='text-lg text-white')
        ui.html(HORIZONTAL_RULE)
        ui.link("Forsendelser", app.url_path_for("Shipment Overview")).classes(replace='text-lg text-white')
        ui.html(HORIZONTAL_RULE)
        ui.link("Tjek Tilmelding", app.url_path_for("Registration Overview")).classes(replace='text-lg text-white')

        ui.space()
        ui.label(authentication.get_current_user()).classes('text-lg text-white')
        ui.button("Log Ud", on_click=authentication.logout, color="white").classes("text-primary")


def theme():
    """Set the theme for the current page."""
    ui.colors(primary="#cc0000")
    ui.input.default_props("filled")
    ui.textarea.default_props("filled")


def obscure_column_values(table: ui.table, column_name: str, start_index: int, length: int):
    """Obscure part of a string value in a Nicegui table.
    Adds a 'show/hide' button next to the value in the table.

    Args:
        table: The table object.
        column_name: The name of the column to obscure.
        start_index: The start index of the substring to obscure.
        length: The length of the substring to obscure.
    """
    table.add_slot(f"body-cell-{column_name}", fr'''
        <q-td auto-width :props="props">
            <span v-if="props.expand" style="padding-right:5px">
                {{{{ props.value }}}}
            </span>
            <span v-else style="padding-right:5px">
                {{{{ props.value.substring(0, {start_index}) }}}}{"X"*length}{{{{ props.value.substring({start_index+length}) }}}}
            </span>
            <q-btn size="sm" round dense
                @click="props.expand = !props.expand"
                :icon="props.expand ? 'visibility' : 'visibility_off'" />
        </q-td>
    ''')


async def question_popup(question: str, option1: str, option2: str, color1: str = 'primary', color2: str = 'primary') -> bool:
    """Shows a popup with a question and two buttons with the given options.
    Example:
        result = await question_popup("Do you like candy", "YES!", "Not really")

    Args:
        question: The question to display.
        option1: The text on button 1.
        option2: The text on button 2.
        color1: The color of button 1.
        color2: The color of button 2.

    Returns:
        bool: True if button 1 is clicked, or False if button 2 is clicked.
    """
    with ui.dialog(value=True).props('persistent') as dialog, ui.card():
        ui.label(question).classes("text-lg")
        with ui.row():
            ui.button(option1, on_click=lambda e: dialog.submit(True), color=color1)
            ui.button(option2, on_click=lambda e: dialog.submit(False), color=color2)

        return await dialog


async def text_input_popup(prompt: str, input_label: str) -> bool:
    
    with ui.dialog(value=True).props('persistent') as dialog, ui.card():
        ui.label(prompt).classes("text-lg")
        input = ui.input(input_label)
        with ui.row():
            ui.button("OK", on_click=lambda e: dialog.submit(input.value))
            ui.button("Luk", on_click=lambda e: dialog.submit(""))

        return await dialog