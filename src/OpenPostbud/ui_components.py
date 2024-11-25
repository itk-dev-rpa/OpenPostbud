
from nicegui import ui, app

from OpenPostbud.pages import login

HORIZONTAL_RULE = '<hr style="width: 2px; height: 1.75rem; display: inline-block; background: white">'


def header():
    theme()

    with ui.header():
        logo = ui.label("📯 OpenPostbud 📯").classes("text-3xl text-bold cursor-pointer")
        logo.on("click", lambda: ui.navigate.to("/"))

        ui.link("Forside", "/").classes(replace='text-lg text-white')
        ui.html(HORIZONTAL_RULE)
        ui.link("Ny Forsendelse", "/send_post").classes(replace='text-lg text-white')
        ui.html(HORIZONTAL_RULE)
        ui.link("Forsendelser", "/forsendelser").classes(replace='text-lg text-white')
        ui.html(HORIZONTAL_RULE)
        ui.link("Tjek Tilmelding", "/tjek_tilmelding").classes(replace='text-lg text-white')

        ui.space()
        ui.label(app.storage.user['user_id']).classes('text-lg text-white')
        ui.button("Log Ud", on_click=login.logout, color="white").classes("text-primary")


def theme():
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
