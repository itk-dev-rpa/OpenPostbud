"""This module contains the pages for looking at shipments/letters."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components
from OpenPostbud.database.digital_post import letters
from OpenPostbud.database.digital_post import shipments, templates

SHIPMENTS_COLUMNS = [
    {'name': "id", 'label': "ID", 'field': "id", 'align': 'left', 'sortable': True},
    {'name': "name", 'label': "Navn", 'field': "name", 'align': 'left', 'sortable': True},
    {'name': "description", 'label': "Beskrivelse", 'field': "description", 'align': 'left', 'sortable': True},
    {'name': "created_at", 'label': "Oprettet", 'field': "created_at", 'align': 'left', 'sortable': True},
    {'name': "created_by", 'label': "Oprettet af", 'field': "created_by", 'align': 'left', 'sortable': True},
    {'name': "status", 'label': "Status", 'field': "status", 'align': 'left', 'sortable': True}
]

LETTERS_COLUMNS = [
    {'name': "id", 'label': "ID", 'field': "id", 'align': 'left', 'sortable': True},
    {'name': "recipient", 'label': "Modtager", 'field': "recipient", 'align': 'left', 'sortable': True},
    {'name': "updated_at", 'label': "Status Opdateret", 'field': "updated_at", 'align': 'left', 'sortable': True},
    {'name': "status", 'label': "Status", 'field': "status", 'align': 'left', 'sortable': True}
]

router = APIRouter()

@router.page("/forsendelser", name="Shipment Overview")
def overview_page():
    """Display the overview page with all shipments."""
    ui_components.header()
    OverviewPage()


@router.page("/forsendelser/{shipment_id}", name="Shipment Detail")
def detail_page(shipment_id: str):
    """Show the detail page of a single shipment."""
    ui_components.header()
    DetailPage(shipment_id)


class OverviewPage():
    """A class representing the overview page."""
    def __init__(self) -> None:
        ui.label("Forsendelser").classes("text-4xl")
        ui.label("Her kan du se tidligere afsendte forsendelser.")
        ui.label("Klik på en forsendelse for at se detaljer og individuelle breve.")
        shipment_list = shipments.get_shipments()
        rows = [s.to_row_dict() for s in shipment_list]

        table = ui.table(title="Forsendelser", columns=SHIPMENTS_COLUMNS, rows=rows, row_key="id", pagination=50).classes("w-full")
        table.on("rowClick", self._row_click)

    def _row_click(self, event):
        """A callback function for when a row in the table is clicked.
        Navigates to the detail page of the clicked shipment.
        """
        row = event.args[1]
        ui.navigate.to(app.url_path_for("Shipment Detail", shipment_id=row["id"]))


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
            ui.label(self.shipment.status)

        letter_table = ui.table(title="Breve", rows=letter_rows, columns=LETTERS_COLUMNS, pagination=50).classes("w-full")
        ui_components.obscure_column_values(letter_table, "recipient", 7, 4)

    def _download_template(self):
        """A callback function for downloading a template file."""
        template = templates.get_template(self.shipment.template_id)
        ui.download(template.file_data, template.file_name)
