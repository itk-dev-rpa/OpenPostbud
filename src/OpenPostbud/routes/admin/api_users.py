"""This module is responsible for the admin page for api users."""

from nicegui import app, ui, APIRouter
from nicegui.events import ClickEventArguments
from fastapi import HTTPException

from OpenPostbud import ui_components
from OpenPostbud.database import api_users
from OpenPostbud.database.digital_post import letters

router = APIRouter()

USER_COLUMNS = [
    {'name': "name",        'label': "Navn",        'field': "name"},
    {'name': "id",          'label': "ID",          'field': "id"},
    {'name': "active",      'label': "Status",      'field': "active"},
    {'name': "created_at",  'label': "Oprettet",    'field': "created_at"}
]

LETTERS_COLUMNS = [
    {'name': "id",          'label': "ID",                'field': "id"},
    {'name': "recipient",   'label': "Modtager",          'field': "recipient"},
    {'name': "status",      'label': "Status",            'field': "status"},
    {'name': "sent_as",     'label': "Sendt som",         'field': "sent_as"},
    {'name': "updated_at",  'label': "Status Opdateret",  'field': "updated_at"},
    {'name': "Message",     'label': "Besked",            'field': "message"}
]

COLUMN_DEFAULTS = {'align': 'left',  'sortable': True,  'style': 'padding-right: 5rem'}


@router.page("/api-users", name="API Users")
def api_users_page():
    """Show the api users page."""
    ui_components.header()
    ApiUsersPage()


class ApiUsersPage:
    """A class representing the api user page."""
    def __init__(self):
        ui.label("Velkommen til Api brugere!").classes("text-4xl")
        ui.button("Ny api bruger", on_click=self._add_api_user)

        self.table = ui.table(rows=[], columns=USER_COLUMNS, column_defaults=COLUMN_DEFAULTS)
        self.table.on("rowClick", self._row_click)
        self._update_table()

    def _update_table(self):
        """Update the api user table with the newest data from the database."""
        rows = [user.to_row_dict() for user in api_users.get_api_users()]
        self.table.rows = rows

    def _row_click(self, event):
        """Open a dialog for the clicked api user row."""
        ui.navigate.to(app.url_path_for("API User Detail", api_user_id=event.args[1]['id']))

    async def _add_api_user(self):
        """Show a popup prompt for a new api user name and create the user with the given name."""
        name = await ui_components.text_input_popup("Indtast navn på ny API bruger", "Navn")
        if not name:
            return
        api_key = api_users.create_api_user(name)
        self._update_table()

        def copy_button_click(event: ClickEventArguments):
            ui.clipboard.write(api_key)
            event.sender.props("icon=check_circle label=Kopieret")

        with ui.dialog(value=True).props('persistent') as dialog, ui.card():
            ui.label("Kopier nedenstående api-nøgle. Den kan ikke vises igen.").classes("text-bold")
            ui.label(api_key)
            with ui.row():
                ui.button("Kopier", on_click=copy_button_click)
                ui.button("Luk", on_click=dialog.close).props("flat")


@router.page("/api-users/{api_user_id}", name="API User Detail")
def api_user_detail_page(api_user_id: str):
    ui_components.header()
    ApiUserDetailPage(api_user_id)


class ApiUserDetailPage:
    def __init__(self, api_user_id: str):
        self.user = api_users.get_api_user(api_user_id)
        if not self.user:
            raise HTTPException(404, f"Ingen api bruger med id {api_user_id} fundet.")

        self._show_header()

        with ui.row():
            self.disable_button = ui_components.DisableButton("Deaktiver", on_click=self._deactivate_user)
            if not self.user.active:
                self.disable_button.disable()
            ui.button("Slet", on_click=self._delete_user)

        self._show_letters_table()

    def _show_letters_table(self):
        """Show the letters table."""
        letter_rows = [letter.to_row_dict() for letter in letters.get_letters_by_user(self.user.id)]
        self.letter_table = ui_components.SearchTable(title="Breve", rows=letter_rows, columns=LETTERS_COLUMNS, column_defaults=COLUMN_DEFAULTS, pagination=50, download_button=True, search_field=True)
        ui_components.obscure_id_column(self.letter_table, "recipient")

    async def _deactivate_user(self):
        """Show a confirmation popup and deactivate the user with the given id."""
        if not await ui_components.question_popup(f"Vil du deaktivere api bruger {self.user.id}?", "Ja", "Nej"):
            return

        api_users.deactivate_api_user(self.user.id)
        ui.notify(f"Api bruger deaktiveret: {self.user.id}", type='positive')
        self.disable_button.disable()
        self._show_header.refresh()

    async def _delete_user(self):
        """Show a confirmation popup and delete the user with the given id.
        An api user can only be deleted if it doesn't have any letters attached.
        """
        if letters.get_letters_by_user(self.user.id):
            await ui_components.info_popup("Du kan ikke slette en api bruger med eksisterende breve tilknyttet.")
            return

        if not await ui_components.question_popup(f"Vil du slette api bruger {self.user.id}?", "Ja", "Nej"):
            return

        api_users.delete_api_user(self.user.id)
        ui.navigate.to(app.url_path_for("API Users"))

    @ui.refreshable
    def _show_header(self):
        self.user = api_users.get_api_user(self.user.id)
        with ui.row():
            ui.label(f"Api bruger {self.user.name} - {self.user.id}").classes("text-4xl")
            if self.user.active:
                ui.chip("Aktiv", color="positive", text_color="white").classes("text-lg")
            else:
                ui.chip("Inaktiv", text_color="white").classes("text-lg")