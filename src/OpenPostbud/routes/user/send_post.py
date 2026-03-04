"""This module contains the 'send_post' page."""

from csv import DictReader
from io import BytesIO
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


@router.page("/send_digital_post", name="Send Post")
def page():
    """Show the 'send_post page."""
    ui_components.header()
    ui.label("Ny Forsendelse").classes("text-4xl")
    ui.label("På denne side kan du oprette en ny forsendelse af Digital Post.")

    SendPostPage()


class SendPostPage():
    """A class representing the 'send_post' page."""
    def __init__(self):
        with ui.stepper().props("vertical flat done-color=green") as stepper:
            with ui.step("Beskrivelse"):
                self.step1 = Step_1_Metadata()
                _stepper_navigation(stepper, prev_button=False, validate_callback=self.step1.validate)
            with ui.step("Skabelon og data"):
                self.step2 = Step_2_File_Upload(parent=self)
                _stepper_navigation(stepper, validate_callback=self.step2.validate)
            with ui.step("Gennemgå eksempler"):
                self.step3 = Step_3_Examples(parent=self)
                _stepper_navigation(stepper)
            with ui.step("Send post"):
                ui.button("Send Post", on_click=self._send_post)
                _stepper_navigation(stepper, next_button=False)

    def update_step_3_example_table(self):
        """Update the example table with the newest csv data."""
        columns = [{"name": n, "label": n, "field": n} for n in self.step2.csv_fields]
        columns.append({"name": "example_button", "label": "", "field": "example_button"})
        self.step3.example_table.columns = columns
        self.step3.example_table.rows = self.step2.csv_data

    def _send_post(self):
        """Add the shipment and letters to the database and navigate
        to the detail page of the shipment.
        """
        with ui.dialog(value=True) as dialog:
            dialog.props("persistent")
            ui.spinner(size="5em")

        template_id = templates.add_template(self.step2.template_name, self.step2.template_bytes)
        shipment_id = shipments.add_shipment(
            self.step1.shipment_name.value,
            self.step1.shipment_desc.value,
            authentication.get_current_user(),
            template_id)
        letters.add_letters(shipment_id, self.step2.csv_data)
        ui.navigate.to(app.url_path_for("Shipment Detail", shipment_id=shipment_id))

    def merge_letter(self, merge_data: dict[str, str]) -> bytes:
        """Use the template and merge data to create an example letter."""
        if self.step2.template_name.endswith(".docx"):
            word_file = letters.merge_word_file(self.step2.template_bytes, merge_data)
            merged_letter = letters.convert_word_to_pdf(word_file)
            return merged_letter

        return self.step2.template_bytes


# pylint: disable-next=invalid-name
class Step_1_Metadata():
    """A class representing the first step in the Send Post flow.
    Here the user enters a name and description for the shipment.
    """
    def __init__(self):
        ui.label("Angiv et navn og beskrivelse af forsendelsen, så den kan genkendes senere.")
        ui.label("Navn og beskrivelse påvirker ikke forsendelsens indhold.")
        self.shipment_name = ui.input("Forsendelse navn", validation={"Maks 50 tegn": lambda v: len(v) <= 50, "Skal udfyldes": lambda v: len(v) != 0}).classes("w-full")
        self.shipment_desc = ui.textarea("Forsendelse beskrivelse", validation={"Maks 200 tegn": lambda v: len(v) <= 200, "Skal udfyldes": lambda v: len(v) != 0}, ).classes("w-full")

    def validate(self) -> bool:
        """Validator function for step 1."""
        if (not self.shipment_name.validate()) | (not self.shipment_desc.validate()):
            ui.notify("Udfyld venligst alle felter", type='warning')
            return False
        return True


# pylint: disable-next=invalid-name, too-many-instance-attributes
class Step_2_File_Upload:
    """A class representing the second step in the Send Post flow.
    Here the user uploads a template and merge data.
    """
    def __init__(self, parent: SendPostPage):
        self.parent = parent
        self.template_name: str = None
        self.template_bytes: bytes = None
        self.template_fields: list[str] = []
        self.csv_data: list[dict[str, str]] = None
        self.csv_fields: list[str] = []

        with ui.grid(columns=2):
            ui.label("Upload skabelon (.docx, .pdf)").classes("text-bold")
            ui.label("Upload flettedata (.csv)").classes("text-bold")

            template_upload = ui.upload(on_upload=self._on_template_upload, max_files=1, auto_upload=True).props("accept=.docx,.pdf")
            csv_upload = ui.upload(on_upload=self._on_csv_upload, max_files=1, auto_upload=True).props("accept=.csv")

            def remove_template():
                template_upload.reset()
                self.template_reset_button.disable()
                self.template_fields = []
                self.template_bytes = None
                self._update_field_tables()

            def remove_csv():
                csv_upload.reset()
                self.csv_reset_button.disable()
                self.csv_fields = []
                self.csv_data = None
                self._update_field_tables()
                self.parent.update_step_3_example_table()

            template_upload.on("removed", remove_template)
            csv_upload.on("removed", remove_csv)

            self.template_reset_button = ui_components.DisableButton("Nulstil skabelon", on_click=remove_template)
            self.template_reset_button.disable()
            self.csv_reset_button = ui_components.DisableButton("Nulstil flettedata", on_click=remove_csv)
            self.csv_reset_button.disable()

            ui.label("Flettefelter i skabelon")
            ui.label("Datakolonner i csv")

            self.template_fields_area = ui.scroll_area().classes("border border-gray-300")
            self.csv_fields_area = ui.scroll_area().classes("border border-gray-300")

        self.message_area = ui_components.MessageArea().classes("border border-gray-300")

    def validate(self) -> bool:
        """Validate that both template and merge data has been uploaded."""
        if not self.template_bytes:
            ui.notify("Skabelon mangler", type="warning")

        if not self.csv_data:
            ui.notify("Flettedata mangler", type="warning")

        return self.template_bytes and self.csv_data

    async def _on_csv_upload(self, e: UploadEventArguments):
        """A callback function for when a csv file is uploaded.
        Get the column names and display them in the ui.
        Display an error if 'Modtager' is not in the columns.
        """
        self.csv_reset_button.enable()
        file_content = await e.file.text()

        dict_reader = DictReader(file_content.splitlines())
        self.csv_fields = sorted(list(dict_reader.fieldnames))
        self.csv_data = list(dict_reader)
        self._update_field_tables()
        self.parent.update_step_3_example_table()

        # Check memo field patterns
        _verify_csv_data(self.csv_fields, self.csv_data, self.message_area)

    async def _on_template_upload(self, e: UploadEventArguments):
        """A callback for when a template file is uploaded.
        Read the merge fields from the template and display them
        in the ui.
        """
        self.template_reset_button.enable()
        self.template_name = e.file.name
        self.template_bytes = await e.file.read()

        if self.template_name.endswith(".docx"):
            with MailMerge(BytesIO(self.template_bytes)) as document:
                fields = sorted(list(document.get_merge_fields()))
                self.template_fields = fields
        else:
            self.template_fields = []

        self._update_field_tables()

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


# pylint: disable-next=invalid-name
class Step_3_Examples:
    """A class representing the third step in the Send Post flow.
    Here the user can verify the uploaded data and download sample letters.
    """
    def __init__(self, parent: SendPostPage):
        self.parent = parent
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
                    nicegui_run.io_bound(lambda: parent.merge_letter(event.args)),
                    timeout=10
                )
                ui.download(letter, "Eksempel.pdf")
            except asyncio.TimeoutError:
                ui.notify("Download fejlede", type="warning")

            dialog.close()

        self.example_table.on("example_button_click", example_button_click)


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
        counter = Counter((line[MemoFields.MEMO_MODTAGER.key] for line in csv_list))
        duplicates = [f"{k}: {v}" for k, v in counter.items() if v > 1]
        if duplicates:
            message_area.add_message(f"Duplikater fundet i '{MemoFields.MEMO_MODTAGER.key}': " + " - ".join(duplicates), type_='warning')
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
