"""This module contains the 'send_post' page."""

from csv import DictReader
from io import TextIOWrapper, BytesIO

from nicegui import ui
from nicegui.events import UploadEventArguments
from mailmerge import MailMerge

from OpenPostbud import ui_components
from OpenPostbud.database.digital_post import letters
from OpenPostbud.database.digital_post import shipments, templates


@ui.page("/send_post")
def page():
    """Show the 'send_post page."""
    ui_components.header()
    ui.label("Ny Forsendelse").classes("text-4xl")
    ui.label("På denne side kan du oprette en ny forsendelse af Digital Post.")

    Page()


class Page():
    """A class representing the 'send_post' page."""
    def __init__(self):
        self.template_name: str = None
        self.template_bytes: bytes = None
        self.csv_bytes: bytes = None

        with ui.stepper().props("vertical flat") as stepper:
            with ui.step("Beskrivelse"):
                self._step_1()
                self._stepper_navigation(stepper, prev_button=False)
            with ui.step("Skabelon og data"):
                self._step_2()
                self._stepper_navigation(stepper)
            with ui.step("Gennemgå eksempler"):
                self._step_3()
                self._stepper_navigation(stepper)
            with ui.step("Send post"):
                self._step_4()
                self._stepper_navigation(stepper, next_button=False)

    def _on_template_upload(self, e: UploadEventArguments):
        """A callback for when a template file is uploaded.
        Read the merge fields from the template and display them
        in the ui.
        """
        self.template_name = e.name
        self.template_bytes = e.content.read()

        with MailMerge(e.content) as document:
            fields = sorted(list(document.get_merge_fields()))

            self.template_fields.clear()
            with self.template_fields:
                for f in fields:
                    ui.label(str(f))

    def _on_csv_upload(self, e: UploadEventArguments):
        """A callback function for when a csv file is uploaded.
        Get the column names and display them in the ui.
        Display an error if 'Modtager' is not in the columns.
        """
        self.csv_bytes = e.content.read()
        e.content.seek(0)
        content = TextIOWrapper(e.content)
        reader = DictReader(content)
        fields = sorted(list(reader.fieldnames))

        self.csv_fields.clear()
        with self.csv_fields:
            for f in fields:
                ui.label(str(f))

        if "Modtager" not in fields:
            ui.notify("'Modtager' ikke fundet i data", type="warning", close_button="Luk")

    def _step_1(self):
        """Define step 1 of the stepper ui."""
        ui.label("Angiv et navn og beskrivelse af forsendelsen, så den kan genkendes senere.")
        ui.label("Navn og beskrivelse påvirker ikke forsendelsens indhold.")
        self.shipment_name = ui.input("Forsendelse navn", validation={"Maks 50 tegn": lambda v: len(v) <= 50}).classes("w-full")
        self.shipment_desc = ui.textarea("Forsendelse beskrivelse", validation={"Maks 200 tegn": lambda v: len(v) <= 200}).classes("w-full")

    def _step_2(self):
        """Define step 2 of the stepper ui."""
        with ui.grid(columns=2):
            ui.label("Upload skabelon (.docx)").classes("text-bold")
            ui.label("Upload flettedata (.csv)").classes("text-bold")

            docx_upload = ui.upload(label="Upload skabelon (.docx)", on_upload=self._on_template_upload, max_files=1, auto_upload=True).props("accept=.docx")
            csv_upload = ui.upload(on_upload=self._on_csv_upload, max_files=1, auto_upload=True).props("accept=.csv")

            ui.button("Fjern fil", on_click=docx_upload.reset)
            ui.button("Fjern fil", on_click=csv_upload.reset)

            ui.label("Flettefelter i skabelon")
            ui.label("Datakolonner i csv")

            self.template_fields = ui.scroll_area().classes("border")
            self.csv_fields = ui.scroll_area().classes("border")

    def _step_3(self):
        """Define step 3 of the stepper ui."""
        ui.label("Her kan du hente og gennemgå eksempler på breve med den givne data.")
        with ui.row():
            ui.button("Vis eksempel", on_click=self._show_example)

    def _step_4(self):
        """Define step 4 of the stepper ui."""
        ui.button("Send Post", on_click=self._send_post)

    def _stepper_navigation(self, stepper: ui.stepper, prev_button: bool = True, next_button: bool = True):
        """Add 'previous' and 'next' buttons to the stepper.

        Args:
            stepper: The stepper object to add buttons to.
            prev_button: Whether to add a 'previous' button. Defaults to True.
            next_button: Whether to add a 'next' button. Defaults to True.
        """
        with ui.stepper_navigation():
            if prev_button:
                ui.button("Forrige", on_click=stepper.previous).props("flat")
            if next_button:
                ui.button("Næste", on_click=stepper.next)

    def _show_example(self):
        """Use the template and merge data to create and download an example letter."""
        reader = DictReader(TextIOWrapper(BytesIO(self.csv_bytes)))

        with MailMerge(BytesIO(self.template_bytes)) as document:
            row = next(reader)

            document.merge(**row)

            file = BytesIO()
            document.write(file=file)

        file.seek(0)
        ui.download(file.read(), "Eksempel.docx")

    def _send_post(self):
        """Add the shipment and letters to the database and navigate
        to the detail page of the shipment.
        """
        template_id = templates.add_template(self.template_name, self.template_bytes)
        shipment_id = shipments.add_shipment(self.shipment_name.value, self.shipment_desc.value, "Me!", template_id)
        letters.add_letters(shipment_id, self.csv_bytes)
        ui.navigate.to(f"/forsendelser/{shipment_id}")
