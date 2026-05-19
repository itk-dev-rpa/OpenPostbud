"""This module contains the pages for looking at shipments/letters."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components
from OpenPostbud.middleware import authentication
from OpenPostbud.database.digital_post import letters
from OpenPostbud.database.digital_post import shipments, templates
from OpenPostbud.database import db_util

SHIPMENTS_COLUMNS = [
    {'name': "id",           'label': "ID",           'field': "id"},
    {'name': "name",         'label': "Navn",         'field': "name"},
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


@router.page("/digital_post", name="Shipment Overview")
def overview_page():
    """Display the overview page with all shipments."""
    ui_components.header()
    ShipmentOverviewPage()


@router.page("/digital_post/{shipment_id}", name="Shipment Detail")
def detail_page(shipment_id: str):
    """Show the detail page of a single shipment."""
    ui_components.header()
    DetailPage(shipment_id)


class ShipmentOverviewPage():
    """A class representing the overview page."""
    def __init__(self) -> None:
        ui.label("Digital Post").classes("text-4xl")
        ui.label("Her kan du se tidligere afsendte Digital Post forsendelser eller oprette en ny.")
        ui.label("Klik på en forsendelse for at se detaljer og individuelle breve.")
        ui.button("Opret ny forsendelse", on_click=lambda: ui.navigate.to(app.url_path_for("Send Post")))

        shipment_list = shipments.get_shipments()
        rows = [s.to_row_dict() for s in shipment_list]
        table = ui_components.SearchTable(title="Forsendelser", columns=SHIPMENTS_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, row_key="id", pagination=50, download_button=False, search_field=True)
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
        ui.label(f"Digital Post forsendelse {shipment_id}").classes("text-4xl")

        self.shipment = shipments.get_shipment(shipment_id)
        if not self.shipment:
            raise LookupError(f"Der findes ingen forsendelse med id {shipment_id}")

        template_name = templates.get_template_name(self.shipment.template_id)

        with ui.grid(columns="auto auto"):
            ui.label("Navn:").classes("text-bold")
            ui.label(self.shipment.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui_components.MultilineLabel(self.shipment.description)

            ui.label("Skabelon:").classes("text-bold")
            ui.link(template_name).on("click", self._download_template)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(self.shipment.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Slettes den:").classes("text-bold")
            ui.label(self.shipment.get_deletion_date().strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(self.shipment.created_by)

        ui.label("Status:").classes("text-bold")
        self._show_shipment_status()

        ui.button("Afbryd forsendelse", color="negative", on_click=self._abort_shipment)

        self._show_letters_table()

    def _download_template(self):
        """A callback function for downloading a template file."""
        template = templates.get_template(self.shipment.template_id)
        ui.download(template.file_data, template.file_name)

    async def _abort_shipment(self):
        """Abort all waiting letters for the shipment."""
        if await ui_components.question_popup("Er du sikker på du vil afbryde forsendelsen?", "Afbryd forsendelse", "Annuller"):
            user = authentication.get_current_user()
            letters.abort_letters(self.shipment.id, user)
            self._show_letters_table.refresh()
            self._show_shipment_status.refresh()

    @ui.refreshable
    def _show_letters_table(self):
        """Show the letters table."""
        letter_rows = [letter.to_row_dict() for letter in letters.get_letters(self.shipment.id)]
        self.letter_table = ui_components.SearchTable(title="Breve", rows=letter_rows, columns=LETTERS_COLUMNS, column_defaults=COLUMN_DEFAULTS, pagination=50, download_button=True, search_field=True)
        ui_components.obscure_id_column(self.letter_table, "recipient", 7, 4)

    @ui.refreshable
    def _show_shipment_status(self):
        """Show the status of the entire shipment."""
        rows = [{"name": s, "value": v} for s, v in db_util.calculate_shipment_status(self.shipment.id)]
        ui.table(rows=rows).props("hide-header flat bordered separator=cell")
