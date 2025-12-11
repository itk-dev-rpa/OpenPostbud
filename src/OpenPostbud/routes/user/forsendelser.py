"""This module contains the pages for looking at shipments/letters."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components
from OpenPostbud.database.digital_post import letters
from OpenPostbud.database.digital_post import shipments, templates
from OpenPostbud.database.digital_post import db_util

SHIPMENTS_COLUMNS = [
    {'name': "id",           'label': "ID",           'field': "id"},
    {'name': "name",         'label': "Navn",         'field': "name"},
    {'name': "description",  'label': "Beskrivelse",  'field': "description"},
    {'name': "created_at",   'label': "Oprettet",     'field': "created_at"},
    {'name': "created_by",   'label': "Oprettet af",  'field': "created_by"}
]

LETTERS_COLUMNS = [
    {'name': "id",          'label': "ID",                'field': "id"},
    {'name': "recipient",   'label': "Modtager",          'field': "recipient"},
    {'name': "status",      'label': "Status",            'field': "status"},
    {'name': "updated_at",  'label': "Status Opdateret",  'field': "updated_at"},
    {'name': "Message",     'label': "Besked",            'field': "message"}
]

COLUMN_DEFAULTS = {'align': 'left',  'sortable': True,  'style': 'padding-right: 5rem'}

router = APIRouter()


@router.page("/forsendelser", name="Shipment Overview")
def overview_page():
    """Display the overview page with all shipments."""
    ui_components.header()
    ShipmentOverviewPage()


@router.page("/forsendelser/{shipment_id}", name="Shipment Detail")
def detail_page(shipment_id: str):
    """Show the detail page of a single shipment."""
    ui_components.header()
    DetailPage(shipment_id)


class ShipmentOverviewPage():
    """A class representing the overview page."""
    def __init__(self) -> None:
        ui.label("Forsendelser").classes("text-4xl")
        ui.label("Her kan du se tidligere afsendte forsendelser.")
        ui.label("Klik på en forsendelse for at se detaljer og individuelle breve.")
        shipment_list = shipments.get_shipments()
        rows = [s.to_row_dict() for s in shipment_list]

        table = ui_components.SearchTable(title="Forsendelser", columns=SHIPMENTS_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, row_key="id", pagination=50, download_button=True, search_field=True)
        table.on("rowClick", self._row_click)

    def _row_click(self, event):
        """A callback function for when a row in the table is clicked.
        Navigates to the detail page of the clicked shipment.
        """
        row = event.args[1]
        ui.navigate.to(app.url_path_for("Shipment Detail", shipment_id=row["id"]))  # pylint: disable=no-member


class DetailPage():
    """A class representing the detail page."""
    def __init__(self, shipment_id: str) -> None:
        ui.label(f"Forsendelse {shipment_id}").classes("text-4xl")

        self.shipment = shipments.get_shipment(shipment_id)
        template_name = templates.get_template_name(self.shipment.template_id)
        letter_rows = [letter.to_row_dict() for letter in letters.get_letters(self.shipment.id)]

        with ui.grid(columns=2):
            ui.label("Navn:").classes("text-bold")
            ui.label(self.shipment.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui.label(self.shipment.description)

            ui.label("Skabelon:").classes("text-bold")
            ui.link(template_name).on("click", self._download_template)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(self.shipment.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(self.shipment.created_by)

            ui.label("Status:").classes("text-bold")
            with ui.grid(columns=2).classes("border gap-0"):
                for status in db_util.calculate_shipment_status(shipment_id):
                    ui.label(status[0]).classes("border p-1")
                    ui.label(status[1]).classes("border p-1")

        letter_table = ui_components.SearchTable(title="Breve", rows=letter_rows, columns=LETTERS_COLUMNS, column_defaults=COLUMN_DEFAULTS, pagination=50, download_button=True, search_field=True)
        ui_components.obscure_column_values(letter_table, "recipient", 7, 4)

    def _download_template(self):
        """A callback function for downloading a template file."""
        template = templates.get_template(self.shipment.template_id)
        ui.download(template.file_data, template.file_name)
