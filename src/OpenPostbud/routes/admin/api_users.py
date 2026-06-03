"""This module is responsible for the admin page for api users."""

from nicegui import ui, APIRouter
from nicegui.events import ClickEventArguments

from OpenPostbud import ui_components
from OpenPostbud.database import api_users
from OpenPostbud.middleware import authentication

router = APIRouter()

USER_COLUMNS = [
    {'name': "name",        'label': "Navn",        'field': "name"},
    {'name': "id",          'label': "ID",          'field': "id"},
    {'name': "owner_group", 'label': "Gruppe",      'field': "owner_group"},
    {'name': "active",      'label': "Status",      'field': "active"},
    {'name': "created_at",  'label': "Oprettet",    'field': "created_at"}
]

COLUMN_DEFAULTS = {'align': 'left',  'sortable': True,  'style': 'padding-right: 5rem'}


@router.page("/api-users", name="API Users")
def api_users_page():
    """Show the api users page."""
    ui_components.header()
    ApiUserPage()


class ApiUserPage:
    """A class representing the api user page."""
    def __init__(self):
        ui.label("Velkommen til Api brugere!").classes("text-4xl")
        ui.button("Ny api bruger", on_click=self._add_api_user)

        self.table = ui.table(rows=[], columns=USER_COLUMNS, column_defaults=COLUMN_DEFAULTS)
        self.table.on("rowClick", self._row_click)
        self._update_table()

    def _update_table(self):
        """Update the api user table with the api users belonging to the admin's groups."""
        groups = authentication.get_current_user_groups()
        rows = [user.to_row_dict() for user in api_users.get_api_users(groups=groups)]
        self.table.rows = rows

    def _row_click(self, event):
        """Open a dialog for the clicked api user row."""
        with ui.dialog(value=True) as dialog, ui.card():
            row = event.args[1]
            ui.label(f"{row['name']} - {row['id']}").classes("text-xl")
            with ui.row():
                ui.button("Slet", on_click=lambda e: self._delete_user(row['id'], dialog))
                ui.button("Luk", on_click=dialog.close)

    async def _add_api_user(self):
        """Show a popup prompt for a new api user name and create the user with the given name."""
        groups = authentication.get_current_user_groups()
        if not groups:
            ui.notify("Du tilhører ingen gruppe og kan ikke oprette API brugere.", type="warning")
            return

        name = await ui_components.text_input_popup("Indtast navn på ny API bruger", "Navn")
        if not name:
            return
        owner_group = await ui_components.select_popup("Vælg gruppe for API brugeren", "Gruppe", groups)
        if not owner_group:
            return
        api_key = api_users.create_api_user(name, owner_group)
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

    async def _delete_user(self, user_id: str, dialog: ui.dialog):
        """Show a confirmation popup and delete the user with the given id."""
        if not await ui_components.question_popup(f"Vil du slette api bruger {user_id}?", "Ja", "Nej"):
            return

        if api_users.delete_api_user(user_id):
            ui.notify(f"Api bruger slettet: {user_id}", type='positive')
            self._update_table()
            dialog.close()
        else:
            ui.notify(f"Bruger ikke fundet: {user_id}", type='negative')
