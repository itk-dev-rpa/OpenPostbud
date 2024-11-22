from nicegui import ui

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


@ui.page("/forsendelser")
def overview_page():
    ui_components.header()
    OverviewPage()


@ui.page("/forsendelser/{id}")
def detail_page(id: int):
    ui_components.header()
    DetailPage(id)


class OverviewPage():
    def __init__(self) -> None:
        ui.label("Forsendelser").classes("text-4xl")
        ui.label("Her kan du se tidligere afsendte forsendelser.")
        ui.label("Klik på en forsendelse for at se detaljer og individuelle breve.")
        shipment_list = shipments.get_shipments()
        rows = [s.to_row_dict() for s in shipment_list]

        table = ui.table(title="Forsendelser", columns=SHIPMENTS_COLUMNS, rows=rows, row_key="id", pagination=50).classes("w-full")
        table.on("rowClick", self.row_click)

    def row_click(self, event):
        row = event.args[1]
        ui.navigate.to(f"/forsendelser/{row["id"]}")


class DetailPage():
    def __init__(self, shipment_id: int) -> None:
        ui.label(f"Forsendelse {shipment_id}").classes("text-4xl")

        self.shipment = shipments.get_shipment(shipment_id)
        template_name = templates.get_template_name(self.shipment.template_id)
        letter_rows = [l.to_row_dict() for l in letters.get_letters(self.shipment.id)]

        with ui.grid(columns=2):
            ui.label("Navn:").classes("text-bold")
            ui.label(self.shipment.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui.label(self.shipment.description)

            ui.label("Skabelon:").classes("text-bold")
            ui.link(template_name).on("click", self.download_template)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(self.shipment.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(self.shipment.created_by)

            ui.label("Status:").classes("text-bold")
            ui.label(self.shipment.status)

        ui.table(title="Breve", rows=letter_rows, columns=LETTERS_COLUMNS, pagination=50).classes("w-full")

    def download_template(self):
        template = templates.get_template(self.shipment.template_id)
        ui.download(template.file_data, template.file_name)
