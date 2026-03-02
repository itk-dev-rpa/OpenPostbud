"""This module contains the pages for looking at registration jobs/tasks."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components
from OpenPostbud.database.nemsms import nemsms_shipments, nemsms_messages
from OpenPostbud.database import db_util
from OpenPostbud.middleware import authentication

SHIPMENT_COLUMNS = [
    {'name': "id",           'label': "ID",           'field': "id"},
    {'name': "name",         'label': "Navn",         'field': "name"},
    {'name': "created_at",   'label': "Oprettet",     'field': "created_at"},
    {'name': "created_by",   'label': "Oprettet af",  'field': "created_by"},
]

MESSAGE_COLUMNS = [
    {'name': "id",          'label': "ID",                'field': "id"},
    {'name': "recipient",   'label': "Modtager",          'field': "recipient"},
    {'name': "updated_at",  'label': "Status Opdateret",  'field': "updated_at"},
    {'name': "status",      'label': "Status",            'field': "status"},
    {'name': "message",     'label': "Besked",            'field': "message"}
]

COLUMN_DEFAULTS = {'align': 'left',  'sortable': True,  'style': 'padding-right: 5rem'}

router = APIRouter()


@router.page("/nemsms", name="NemSMS Overview")
def overview_page():
    """Show the overview page."""
    ui_components.header()
    OverviewPage()


@router.page("/nemsms/{shipment_id}", name="NemSMS Detail")
def detail_page(shipment_id: str):
    """Show the detail page."""
    ui_components.header()
    DetailPage(shipment_id)


class OverviewPage():
    """A class representing the overview page.
    Here all NemSMS shipments are shown.
    """
    def __init__(self):
        ui.label("NemSMS").classes("text-4xl")
        ui.label("Her kan du se tidligere oprettede NemSMS forsendelser eller oprette en ny.")
        ui.label("Klik på en forsendelse på listen for at se flere detaljer.")
        ui.button("Opret ny forsendelse", on_click=lambda: ui.navigate.to(app.url_path_for("Send NemSMS")))

        shipment_list = nemsms_shipments.get_shipments()
        rows = [shipment.to_row_dict() for shipment in shipment_list]
        table = ui.table(title="NemSMS Forsendelser", columns=SHIPMENT_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, pagination=50, row_key="id")
        table.on("rowClick", self.row_click)

    def row_click(self, event):
        """Callback for when a row is clicked.
        Navigate to the detail view for the clicked shipment.
        """
        row = event.args[1]
        ui.navigate.to(app.url_path_for("NemSMS Detail", shipment_id=row["id"]))  # pylint: disable=no-member


class DetailPage():
    """A class representing the detail page."""
    def __init__(self, shipment_id: str):
        ui.label(f"NemSMS forsendelse {shipment_id}").classes("text-4xl")

        self.shipment = nemsms_shipments.get_shipment(shipment_id)
        if not self.shipment:
            raise LookupError(f"Der findes ingen NemSMS forsendelse med id {shipment_id}")

        with ui.grid(columns="auto auto"):
            ui.label("Navn:").classes("text-bold")
            ui.label(self.shipment.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui_components.MultilineLabel(self.shipment.description)

            ui.label("Beskedtekst:").classes("text-bold")
            ui_components.MultilineLabel(self.shipment.message_text)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(self.shipment.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Slettes den:").classes("text-bold")
            ui.label(self.shipment.deletion_date.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(self.shipment.created_by)

        ui.label("Status:").classes("text-bold")
        self._show_shipment_status()

        ui.button("Afbryd forsendelse", color="negative", on_click=self._abort_shipment)

        self._show_messages_table()

    async def _abort_shipment(self):
        """Abort all waiting letters for the shipment."""
        if await ui_components.question_popup("Er du sikker på du vil afbryde forsendelsen?", "Afbryd forsendelse", "Annuller"):
            user = authentication.get_current_user()
            nemsms_messages.abort_messages(self.shipment.id, user)
            self._show_messages_table.refresh()
            self._show_shipment_status.refresh()

    @ui.refreshable
    def _show_messages_table(self):
        """Show the letters table."""
        messages = nemsms_messages.get_messages(self.shipment.id)
        rows = [m.to_row_dict() for m in messages]
        self.table = ui_components.SearchTable(title="Beskeder", columns=MESSAGE_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, pagination=50, search_field=True, download_button=True)
        ui_components.obscure_column_values(self.table, "recipient", 7, 4)

    @ui.refreshable
    def _show_shipment_status(self):
        """Show the status of the entire shipment."""
        rows = [{"name": s, "value": v} for s, v in db_util.calculate_nemsms_shipment_status(self.shipment.id)]
        ui.table(rows=rows).props("hide-header flat bordered separator=cell")
