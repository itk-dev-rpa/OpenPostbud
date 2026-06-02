"""This module contains reusable UI components."""

from typing import Literal
import csv
from io import StringIO

from nicegui import ui, app

from OpenPostbud.middleware import authentication
from OpenPostbud import config


def header():
    """Show a NiceGUI header with links to other pages."""
    theme()

    with ui.header():
        logo = ui.label("📯 OpenPostbud 📯").classes("text-3xl text-bold cursor-pointer")
        logo.on("click", lambda: ui.navigate.to(app.url_path_for("Front Page")))  # pylint: disable=no-member

        ui.link("Forside", app.url_path_for("Front Page")).classes(replace='text-lg text-white')
        ui.separator().props("vertical color=white size=2px")
        ui.link("Digital Post", app.url_path_for("Shipment Overview")).classes(replace='text-lg text-white')
        ui.separator().props("vertical color=white size=2px")
        ui.link("NemSMS", app.url_path_for("NemSMS Overview")).classes(replace='text-lg text-white')
        ui.separator().props("vertical color=white size=2px")
        ui.link("Tjek Tilmelding", app.url_path_for("Registration Overview")).classes(replace='text-lg text-white')

        if authentication.is_admin():
            ui.separator().props("vertical color=white size=2px")
            ui.link("API Brugere", app.url_path_for("API Users")).classes(replace='text-lg text-white')

        ui.space()
        ui.label(authentication.get_current_user()).classes('text-lg text-white')
        ui.label(str(authentication.get_current_user_roles())).classes('text-lg text-white')
        ui.separator().props("vertical color=white size=2px")
        ui.label(config.OPENPOSTBUD_VERSION).classes('text-lg text-white')
        ui.button("Log Ud", on_click=authentication.logout, color="white").classes("text-primary")


def theme():
    """Set the theme for the current page."""
    ui.colors(primary="#cc0000")
    ui.input.default_props("filled")
    ui.textarea.default_props("filled")


def obscure_id_column(table: ui.table, column_name: str):
    """Obscure the last 4 digits of a CPR or CVR value in a Nicegui table.
    Adds a 'show/hide' button next to the value in the table.

    A 10-digit value (CPR) is shown as dddddd-XXXX; an 8-digit value (CVR)
    is shown as ddddXXXX. Other lengths are shown unchanged.

    Args:
        table: The table object.
        column_name: The name of the column to obscure.
    """
    table.add_slot(f"body-cell-{column_name}", r'''
        <q-td auto-width :props="props">
            <span style="padding-right:5px" v-if="props.value.length === 10">
                {{ props.value.substring(0, 6) }}-{{ props.expand ? props.value.substring(6) : 'XXXX' }}
            </span>
            <span style="padding-right:5px" v-else-if="props.value.length === 8">
                {{ props.value.substring(0, 4) }}{{ props.expand ? props.value.substring(4) : 'XXXX' }}
            </span>
            <span style="padding-right:5px" v-else>
                {{ props.value }}
            </span>
            <q-btn size="sm" round dense
                @click="props.expand = !props.expand"
                :icon="props.expand ? 'visibility' : 'visibility_off'" />
        </q-td>
    ''')


async def question_popup(question: str, option1: str, option2: str, color1: str = 'primary', color2: str = 'primary') -> bool:
    """Show an awaitable popup with a question and two buttons with the given options.
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


async def text_input_popup(prompt: str, input_label: str) -> str:
    """Show an awaitable popup that asks for a single text input.

    Args:
        prompt: The text to show on the dialog.
        input_label: The label text on the input element.

    Returns:
        The text from the text input or an empty string if the dialog is closed.
    """
    with ui.dialog(value=True).props('persistent') as dialog, ui.card():
        ui.label(prompt).classes("text-lg")
        text_input = ui.input(input_label)
        with ui.row():
            ui.button("OK", on_click=lambda e: dialog.submit(text_input.value))
            ui.button("Luk", on_click=lambda e: dialog.submit(""))

        return await dialog


class DisableButton(ui.button):
    """An extension of ui.button that turns grey when disabled."""
    def _handle_enabled_change(self, enabled: bool) -> None:
        """Called when the element is enabled or disabled.

        :param enabled: The new state.
        """
        if enabled:
            self.props("color=primary")
        else:
            self.props("color=grey")
        self._props['disable'] = not enabled
        self.update()


class MessageArea(ui.scroll_area):
    """A ui component for displaying messages in line with other content."""
    def add_message(self, text: str, type_: Literal["positive", "warning", "negative"]):
        """Add a new message to the message area.

        Args:
            text: The text of the message.
            type_: The type of the message which determines the color and icon.
        """
        with self, ui.card() as card:
            with ui.row(align_items="center"):
                match(type_):
                    case "positive":
                        card.classes("w-full bg-positive")
                        ui.icon("check_circle", color="white", size="1.8em")
                        ui.label(text).classes("text-white")
                    case "warning":
                        card.classes("w-full bg-warning")
                        ui.icon("priority_high", color="black", size="1.8em")
                        ui.label(text)
                    case "negative":
                        card.classes("w-full bg-negative")
                        ui.icon("warning", color="white", size="1.8em")
                        ui.label(text).classes("text-white")
        self.update()


class SearchTable(ui.table):
    """An extension of ui.table that has a search field in the top slot."""
    def __init__(self, *, rows, columns=None, column_defaults=None, row_key='id', title=None, selection=None, pagination=None, on_select=None, on_pagination_change=None,   # pylint: disable=too-many-arguments
                 search_field: bool, download_button: bool):
        super().__init__(rows=rows, columns=columns, column_defaults=column_defaults, row_key=row_key, selection=selection, pagination=pagination, on_select=on_select, on_pagination_change=on_pagination_change)
        with self.add_slot("top"):
            ui.label(title).classes("q-table__title")
            ui.space()
            if download_button:
                ui.button("Download liste", on_click=self._download_list).classes("mr-5")
            if search_field:
                search_input = ui.input("Søg").props("clearable")
                self.bind_filter_from(search_input, "value")

    def _download_list(self):
        """A callback function for downloading the table data as a csv file."""
        field_names = [col["field"] for col in self.columns]
        field_labels = {col["field"]: col["label"] for col in self.columns}

        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writerow(field_labels)
        writer.writerows(self.rows)

        ui.download(f.getvalue().encode(), "Liste.csv")


class MultilineLabel():
    """A utility class for creating multiple labels
    for multiline text."""
    labels: list[ui.label]

    def __init__(self, text: str):
        self.labels = []

        with ui.column().style("gap: 0;"):
            for line in text.splitlines():
                self.labels.append(ui.label(line))
