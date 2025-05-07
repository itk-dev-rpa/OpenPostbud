"""This module contains the 'send_post' page."""

from csv import DictReader
from io import TextIOWrapper
from collections import Counter
from collections.abc import Callable
import asyncio

from nicegui import ui, APIRouter, app
from nicegui import run as nicegui_run
from nicegui.events import UploadEventArguments
from mailmerge import MailMerge

from OpenPostbud import ui_components
from OpenPostbud.middleware import authentication
from OpenPostbud.database.digital_post import letters, shipments, templates
from OpenPostbud.database.digital_post.letters import MemoFields


router = APIRouter()


@router.page("/send_post", name="Send Post")
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
        self.csv_data: list[dict[str, str]] = None
        self.csv_fields: list[str] = []
        self.template_fields: list[str] = []

        with ui.stepper().props("vertical flat done-color=green") as stepper:
            with ui.step("Beskrivelse"):
                self._step_1_metadata()
                _stepper_navigation(stepper, prev_button=False, validate_callback=self._validate_step_1)
            with ui.step("Skabelon og data"):
                self._step_2_file_upload()
                _stepper_navigation(stepper, validate_callback=self._validate_step_2)
            with ui.step("Gennemgå eksempler"):
                self._step_3_show_example()
                _stepper_navigation(stepper)
            with ui.step("Send post"):
                self._step_4_send()
                _stepper_navigation(stepper, next_button=False)

    def _on_template_upload(self, e: UploadEventArguments):
        """A callback for when a template file is uploaded.
        Read the merge fields from the template and display them
        in the ui.
        """
        self.docx_reset_button.enable()
        self.template_name = e.name
        self.template_bytes = e.content.read()

        with MailMerge(e.content) as document:
            fields = sorted(list(document.get_merge_fields()))

            self.template_fields = fields
            self._update_field_tables()

    def _on_csv_upload(self, e: UploadEventArguments):
        """A callback function for when a csv file is uploaded.
        Get the column names and display them in the ui.
        Display an error if 'Modtager' is not in the columns.
        """
        self.csv_reset_button.enable()

        dict_reader = DictReader(TextIOWrapper(e.content))
        self.csv_fields = sorted(list(dict_reader.fieldnames))
        self.csv_data = list(dict_reader)
        self._update_field_tables()
        self._update_example_table()

        # Check memo field patterns
        _verify_csv_data(self.csv_fields, self.csv_data, self.message_area)

    def _update_example_table(self):
        """Update the example table with the newest csv data."""
        columns = [{"name": n, "label": n, "field": n} for n in self.csv_fields]
        columns.append({"name": "example_button", "label": "", "field": "example_button"})
        self.example_table.columns = columns
        self.example_table.rows = self.csv_data

    def _update_field_tables(self):
        """Update the csv and merge field text areas.
        Color code merge fields according to whether they appear
        in the merge data.
        """
        self.template_fields_area.clear()
        with self.template_fields_area:
            for f in self.template_fields:
                with ui.row(align_items='center'):
                    if f in self.csv_fields:
                        ui.icon("check_circle", color='positive', size="1rem")
                        ui.label(f)
                    else:
                        ui.icon("cancel", color='negative', size="1rem")
                        ui.label(f)
                        self.message_area.add_message(f"'{f}' mangler i flettedata", type_="warning")
                ui.separator()

        self.csv_fields_area.clear()
        with self.csv_fields_area:
            for f in self.csv_fields:
                if any(f == mf.key for mf in MemoFields):
                    with ui.row(align_items='center'):
                        ui.icon("settings", color='secondary')
                        ui.label(str(f)).classes("text-secondary")
                else:
                    ui.label(str(f))
                ui.separator()

    def _step_1_metadata(self):
        """Define step 1 of the stepper ui."""
        ui.label("Angiv et navn og beskrivelse af forsendelsen, så den kan genkendes senere.")
        ui.label("Navn og beskrivelse påvirker ikke forsendelsens indhold.")
        self.shipment_name = ui.input("Forsendelse navn", validation={"Maks 50 tegn": lambda v: len(v) <= 50, "Skal udfyldes": lambda v: len(v) != 0}).classes("w-full")
        self.shipment_desc = ui.textarea("Forsendelse beskrivelse", validation={"Maks 200 tegn": lambda v: len(v) <= 200, "Skal udfyldes": lambda v: len(v) != 0}, ).classes("w-full")

    def _validate_step_1(self) -> bool:
        """Validator function for step 1."""
        if (not self.shipment_name.validate()) | (not self.shipment_desc.validate()):
            ui.notify("Udfyld venligst alle felter", type='warning')
            return False
        return True

    def _step_2_file_upload(self):
        """Define step 2 of the stepper ui."""
        with ui.grid(columns=2):
            ui.label("Upload skabelon (.docx)").classes("text-bold")
            ui.label("Upload flettedata (.csv)").classes("text-bold")

            docx_upload = ui.upload(on_upload=self._on_template_upload, max_files=1, auto_upload=True).props("accept=.docx")
            csv_upload = ui.upload(on_upload=self._on_csv_upload, max_files=1, auto_upload=True).props("accept=.csv")

            def remove_docx():
                docx_upload.reset()
                self.docx_reset_button.disable()
                self.template_fields = []
                self.template_bytes = None
                self._update_field_tables()

            def remove_csv():
                csv_upload.reset()
                self.csv_reset_button.disable()
                self.csv_fields = []
                self.csv_data = None
                self._update_field_tables()

            docx_upload.on("removed", remove_docx)
            csv_upload.on("removed", remove_csv)

            self.docx_reset_button = ui_components.DisableButton("Nulstil skabelon", on_click=remove_docx)
            self.docx_reset_button.disable()
            self.csv_reset_button = ui_components.DisableButton("Nulstil flettedata", on_click=remove_csv)
            self.csv_reset_button.disable()

            ui.label("Flettefelter i skabelon")
            ui.label("Datakolonner i csv")

            self.template_fields_area = ui.scroll_area().classes("border")
            self.csv_fields_area = ui.scroll_area().classes("border")

        self.message_area = ui_components.MessageArea().classes("border")

    def _validate_step_2(self):
        if not self.template_bytes:
            ui.notify("Skabelon mangler", type="warning")

        if not self.csv_data:
            ui.notify("Flettedata mangler", type="warning")

        return self.template_bytes and self.csv_data

    def _step_3_show_example(self):
        """Define step 3 of the stepper ui."""
        ui.label("Her kan du hente og gennemgå eksempler på breve med den givne data.")
        self.example_table = ui.table(rows=[], title="Breve", column_defaults={"align": "left"}, pagination=5)
        self.example_table.add_slot(
            "body-cell-example_button",
            r"""
                <q-td :props="props">
                    <q-btn icon="download" round color="primary" @click="$parent.$emit('example_button_click', props.row)"/>
                </q-td>
            """
        )

        async def example_button_click(event):
            with ui.dialog(value=True) as dialog:
                dialog.props("persistent")
                ui.spinner(size="5em")

            try:
                letter = await asyncio.wait_for(
                    nicegui_run.io_bound(lambda: _merge_letter(self.template_bytes, event.args)),
                    timeout=10
                )
                ui.download(letter, "Eksempel.pdf")
            except asyncio.TimeoutError:
                ui.notify("Download fejlede", type="warning")

            dialog.close()

        self.example_table.on("example_button_click", example_button_click)

    def _step_4_send(self):
        """Define step 4 of the stepper ui."""
        ui.button("Send Post", on_click=self._send_post)

    def _send_post(self):
        """Add the shipment and letters to the database and navigate
        to the detail page of the shipment.
        """
        with ui.dialog(value=True) as dialog:
            dialog.props("persistent")
            ui.spinner(size="5em")

        template_id = templates.add_template(self.template_name, self.template_bytes)
        shipment_id = shipments.add_shipment(
            self.shipment_name.value,
            self.shipment_desc.value,
            authentication.get_current_user(),
            template_id)
        letters.add_letters(shipment_id, self.csv_data)
        ui.navigate.to(app.url_path_for("Shipment Detail", shipment_id=shipment_id))



def _stepper_navigation(stepper: ui.stepper, prev_button: bool = True, next_button: bool = True, validate_callback: Callable[[], bool] = None):
    """Add 'previous' and 'next' buttons to the stepper.

    Args:
        stepper: The stepper object to add buttons to.
        prev_button: Whether to add a 'previous' button. Defaults to True.
        next_button: Whether to add a 'next' button. Defaults to True.
        validate_callback: A function to do validation before going to the next step. Defaults to None.
    """
    with ui.stepper_navigation():
        if prev_button:
            ui.button("Forrige", on_click=stepper.previous).props("flat")
        if next_button:
            if validate_callback:
                def next_function():
                    if validate_callback():
                        stepper.next()
                ui.button("Næste", on_click=next_function)
            else:
                ui.button("Næste", on_click=stepper.next)


def _verify_csv_data(fields: list[str], csv_list: list[dict], message_area: ui_components.MessageArea) -> None:
    """Verify the input against these rules:
        - Are there any duplicate receivers?
        - Are all mandatory fields present?
        - Does field pattern match for all lines?

    Show adds message to the message area if any rules are broken.

    Args:
        fields: The column names in the csv.
        csv_list: The input list as a csv dictionary from DictReader.
        message_area: The message area to add message to on errors.
    """
    message_area.clear()
    error = False

    # Check for duplicate receivers
    if MemoFields.MEMO_MODTAGER.key in fields:
        c = Counter((line[MemoFields.MEMO_MODTAGER.key] for line in csv_list))
        l = [f"{k}: {v}" for k, v in c.items() if v > 1]
        if l:
            message_area.add_message(f"Duplikater fundet i '{MemoFields.MEMO_MODTAGER.key}': " + " - ".join(l), type_='warning')
            error = True

    # Check for mandatory fields
    for mf in MemoFields:
        if mf.mandatory and mf.key not in fields:
            message_area.add_message(f"'{mf.key}' ikke fundet i data", type_="negative")
            error = True

    # Check for pattern mismatches (show 3 errors max)
    error_count = 0
    for i, row in enumerate(csv_list):
        for mf in MemoFields:
            if mf.key in row:
                if not mf.pattern.fullmatch(row[mf.key]):
                    message_area.add_message(f"Fejl på linje {i}: Kolonne: '{mf.key}' - Mønster: '{mf.pattern.pattern}'", type_='negative')
                    error_count += 1
                    error = True
                    if error_count >= 3:
                        return

    if not error:
        message_area.add_message("Alles gut", type_="positive")


def _merge_letter(template: bytes, merge_data: dict[str, str]) -> bytes:
    """Use the template and merge data to create an example letter."""
    word_file = letters.merge_word_file(template, merge_data)
    merged_letter = letters.convert_word_to_pdf(word_file)
    return merged_letter
