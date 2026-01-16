"""This module contains the pages for looking at registration jobs/tasks."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components
from OpenPostbud.database.nemsms import nemsms_shipments, nemsms_messages
from OpenPostbud.database import db_util

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

        shipment = nemsms_shipments.get_shipment(shipment_id)
        if not shipment:
            raise LookupError(f"Der findes ingen NemSMS forsendelse med id {shipment_id}")

        with ui.grid(columns="auto auto"):
            ui.label("Navn:").classes("text-bold")
            ui.label(shipment.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui_components.MultilineLabel(shipment.description)

            ui.label("Beskedtekst:").classes("text-bold")
            ui_components.MultilineLabel(shipment.message_text)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(shipment.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Slettes den:").classes("text-bold")
            ui.label(shipment.deletion_date.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(shipment.created_by)

            ui.label("Status:").classes("text-bold")
            with ui.grid(columns=2).classes("border gap-0 w-fit"):
                for status in db_util.calculate_nemsms_shipment_status(shipment_id):
                    ui.label(status[0]).classes("border p-1")
                    ui.label(status[1]).classes("border p-1")

        messages = nemsms_messages.get_messages(shipment_id)
        rows = [m.to_row_dict() for m in messages]
        table = ui_components.SearchTable(title="Beskeder", columns=MESSAGE_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, pagination=50, search_field=True, download_button=True)
        ui_components.obscure_column_values(table, "recipient", 7, 4)
