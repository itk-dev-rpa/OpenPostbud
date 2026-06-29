"""This module contains the 'send_post' page."""

from csv import DictReader
from collections import Counter
from collections.abc import Callable
from typing import Literal, NamedTuple
import asyncio

from nicegui import ui, APIRouter, app
from nicegui import run as nicegui_run
from nicegui.events import UploadEventArguments
from jinja2.exceptions import TemplateSyntaxError

from OpenPostbud import ui_components
from OpenPostbud.middleware import authentication
from OpenPostbud.database.digital_post import letters, shipments, templates, field_rules
from OpenPostbud.database.digital_post.letters import MemoFields
from OpenPostbud.database.common import PostType
from OpenPostbud.utils import docx_util


router = APIRouter()


class ValidationMessage(NamedTuple):
    """A message produced by csv validation, ready to be shown in a MessageArea."""
    text: str
    type_: Literal["positive", "warning", "negative"]


@router.page("/send_digital_post", name="Send Post")
def page():
    """Show the 'send_post page."""
    ui_components.header()
    ui.label("Ny Forsendelse").classes("text-4xl")
    ui.label("På denne side kan du oprette en ny forsendelse af Digital Post eller Fysisk Post.")

    SendPostPage()


class SendPostPage:
    """A class representing the 'send_post' page."""
    def __init__(self):
        with ui.stepper().props("vertical flat done-color=green") as stepper:
            with ui.step("Beskrivelse"):
                self.step1 = MetadataStep()
                _stepper_navigation(stepper, prev_button=False, validate_callback=self.step1.validate)
            with ui.step("Skabelon og data"):
                self.step2 = FileUploadStep(
                    on_csv_changed=self._on_csv_data_changed,
                    get_post_type=lambda: self.step1.post_type.value,
                )
                _stepper_navigation(stepper, validate_callback=self.step2.validate)
            with ui.step("Gennemgå eksempler"):
                self.step3 = ExamplesStep(merge_letter=self.step2.merge_letter)
                _stepper_navigation(stepper)
            with ui.step("Send post"):
                ui.button("Send Post", on_click=self._send_post)
                _stepper_navigation(stepper, next_button=False)

        # Re-run csv validation and refresh the field list when the post type
        # changes, since both the mandatory fields and which custom rules apply
        # depend on it.
        self.step1.post_type.on_value_change(self.step2.on_post_type_change)

    def _on_csv_data_changed(self, fields: list[str], rows: list[dict[str, str]] | None):
        """Forward csv changes from step 2 to step 3."""
        self.step3.set_data(fields, rows)

    def _send_post(self):
        """Add the shipment and letters to the database and navigate
        to the detail page of the shipment.
        """
        with ui.dialog(value=True) as dialog:
            dialog.props("persistent")
            ui.spinner(size="5em")

        try:
            template_id = templates.add_template(self.step2.template_name, self.step2.template_bytes)
            shipment_id = shipments.add_shipment(
                self.step1.shipment_name.value,
                self.step1.shipment_desc.value,
                authentication.get_current_user(),
                template_id,
                self.step1.post_type.value)
            letters.add_letters(shipment_id, self.step2.csv_data)
            ui.navigate.to(app.url_path_for("Shipment Detail", shipment_id=shipment_id))
        finally:
            dialog.close()


class MetadataStep:
    """A class representing the first step in the Send Post flow.
    Here the user enters a name and description for the shipment.
    """
    def __init__(self):
        ui.label("Angiv et navn og beskrivelse af forsendelsen, så den kan genkendes senere.")
        ui.label("Navn og beskrivelse påvirker ikke forsendelsens indhold.")
        self.shipment_name = ui.input(
            "Forsendelse navn",
            validation={"Maks 50 tegn": lambda v: len(v) <= 50, "Skal udfyldes": lambda v: len(v) != 0},
        ).classes("w-full")
        self.shipment_desc = ui.textarea(
            "Forsendelse beskrivelse",
            validation={"Maks 200 tegn": lambda v: len(v) <= 200, "Skal udfyldes": lambda v: len(v) != 0},
        ).classes("w-full")

        ui.label("Vælg hvordan forsendelsen skal sendes.")
        self.post_type = ui.radio({pt: pt.value for pt in PostType}, value=PostType.DIGITAL)
        physical_hint = ui.label(
            "Bemærk: Ved Fysisk Post skal modtagerens adresse fremgå af brevet, så den kan ses i kuvertens rude."
        ).classes("text-secondary")
        physical_hint.bind_visibility_from(self.post_type, "value", backward=lambda v: v != PostType.DIGITAL)

    def validate(self) -> bool:
        """Validator function for step 1."""
        name_ok = self.shipment_name.validate()
        desc_ok = self.shipment_desc.validate()
        if not (name_ok and desc_ok):
            ui.notify("Udfyld venligst alle felter", type='warning')
            return False
        return True


# pylint: disable-next=too-many-instance-attributes
class FileUploadStep:
    """A class representing the second step in the Send Post flow.
    Here the user uploads a template and merge data.
    """
    def __init__(self, on_csv_changed: Callable[[list[str], list[dict[str, str]] | None], None], get_post_type: Callable[[], PostType]):
        self._on_csv_changed = on_csv_changed
        self._get_post_type = get_post_type
        self.template_name: str | None = None
        self.template_bytes: bytes | None = None
        self.template_fields: list[str] = []
        self.csv_data: list[dict[str, str]] | None = None
        self.csv_fields: list[str] = []

        # All custom admin field rules, used to mark fields in the csv field
        # list that have a rule applicable to the selected post type.
        self._rules = field_rules.get_field_rules()

        with ui.grid(columns=2):
            ui.label("Upload skabelon (.docx, .pdf)").classes("text-bold")
            ui.label("Upload flettedata (.csv)").classes("text-bold")

            self._template_upload = ui.upload(on_upload=self._on_template_upload, max_files=1, auto_upload=True).props("accept=.docx,.pdf")
            self._csv_upload = ui.upload(on_upload=self._on_csv_upload, max_files=1, auto_upload=True).props("accept=.csv")
            self._template_upload.on("removed", self._remove_template)
            self._csv_upload.on("removed", self._remove_csv)

            self.template_reset_button = ui_components.DisableButton("Nulstil skabelon", on_click=self._remove_template)
            self.template_reset_button.disable()
            self.csv_reset_button = ui_components.DisableButton("Nulstil flettedata", on_click=self._remove_csv)
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
        return bool(self.template_bytes and self.csv_data)

    def merge_letter(self, merge_data: dict[str, str]) -> bytes:
        """Use the template and merge data to create an example letter."""
        if self.template_name.endswith(".docx"):
            word_file = docx_util.merge_word_file(self.template_bytes, merge_data)
            return docx_util.convert_word_to_pdf(word_file)
        return self.template_bytes

    async def _on_template_upload(self, e: UploadEventArguments):
        """Read the merge fields from the uploaded template and refresh the field list."""
        self.template_reset_button.enable()
        self.template_name = e.file.name
        self.template_bytes = await e.file.read()

        if self.template_name.endswith(".docx"):
            try:
                self.template_fields = docx_util.get_merge_fields(self.template_bytes)
            except TemplateSyntaxError as error:
                ui.notify(f"Syntaksfejl i skabelon: {error}", type="negative", timeout=0, actions=[{"label": "Luk", "color": "white"}])
                self._remove_template()
                raise
        else:
            self.template_fields = []

        self._update_field_tables()
        self.refresh_messages()

    async def _on_csv_upload(self, e: UploadEventArguments):
        """Read the columns from the uploaded csv, refresh the field list,
        push the data to step 3, and run validation.
        """
        self.csv_reset_button.enable()
        file_content = await e.file.text(encoding="utf-8-sig")

        dict_reader = DictReader(file_content.splitlines())
        self.csv_fields = sorted(list(dict_reader.fieldnames))
        self.csv_data = list(dict_reader)
        self._update_field_tables()
        self._on_csv_changed(self.csv_fields, self.csv_data)
        self.refresh_messages()

    def _remove_template(self):
        self._template_upload.reset()
        self.template_reset_button.disable()
        self.template_fields = []
        self.template_bytes = None
        self._update_field_tables()
        self.refresh_messages()

    def _remove_csv(self):
        self._csv_upload.reset()
        self.csv_reset_button.disable()
        self.csv_fields = []
        self.csv_data = None
        self._update_field_tables()
        self._on_csv_changed(self.csv_fields, self.csv_data)
        self.refresh_messages()

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
                    else:
                        ui.icon("cancel", color='negative', size="1rem")
                    ui.label(f)
                ui.separator()

        # Only mark fields whose rules apply to the selected post type.
        post_type = self._get_post_type()
        rule_fields: dict[str, list[str]] = {}
        for rule in self._rules:
            if rule.applies_to(post_type):
                rule_fields.setdefault(rule.field_name, []).append(f"{rule.rule_type.value}: {rule.value}")

        self.csv_fields_area.clear()
        with self.csv_fields_area:
            for f in self.csv_fields:
                if any(f == mf.key for mf in MemoFields):
                    with ui.row(align_items='center'):
                        ui.icon("settings", color='secondary')
                        ui.label(str(f)).classes("text-secondary")
                elif f in rule_fields:
                    with ui.row(align_items='center'):
                        ui.icon("rule", color='secondary')
                        ui.label(str(f)).classes("text-secondary")
                        ui.tooltip(" / ".join(rule_fields[f]))
                else:
                    ui.label(str(f))
                ui.separator()

    def on_post_type_change(self):
        """Refresh the field list and messages when the post type changes.

        Both the mandatory fields and which custom rules apply depend on the
        selected post type.
        """
        self._update_field_tables()
        self.refresh_messages()

    def refresh_messages(self):
        """Rebuild the message area from current template + csv state.

        Collects template- and csv-level messages together, then shows the
        "all good" message only when data has been uploaded and no other
        messages were produced.
        """
        self.message_area.clear()
        messages: list[ValidationMessage] = []

        for f in self.template_fields:
            if f not in self.csv_fields:
                messages.append(ValidationMessage(f"'{f}' mangler i flettedata", "warning"))

        if self.csv_data is not None:
            messages.extend(_verify_csv_data(self.csv_fields, self.csv_data, self._get_post_type()))

        if not messages and self.template_bytes and self.csv_data:
            messages.append(ValidationMessage("Alles gut", "positive"))

        for msg in messages:
            self.message_area.add_message(msg.text, type_=msg.type_)


class ExamplesStep:
    """A class representing the third step in the Send Post flow.
    Here the user can verify the uploaded data and download sample letters.
    """
    def __init__(self, merge_letter: Callable[[dict[str, str]], bytes]):
        self._merge_letter = merge_letter
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
        self.example_table.on("example_button_click", self._on_example_click)

    def set_data(self, fields: list[str], rows: list[dict[str, str]] | None):
        """Update the example table columns and rows."""
        columns = [{"name": n, "label": n, "field": n} for n in fields]
        columns.append({"name": "example_button", "label": "", "field": "example_button"})
        self.example_table.columns = columns
        self.example_table.rows = rows

    async def _on_example_click(self, event):
        with ui.dialog(value=True) as dialog:
            dialog.props("persistent")
            ui.spinner(size="5em")

        try:
            letter = await asyncio.wait_for(
                nicegui_run.io_bound(lambda: self._merge_letter(event.args)),
                timeout=10,
            )
            ui.download(letter, "Eksempel.pdf")
        except asyncio.TimeoutError:
            ui.notify("Download fejlede", type="warning")
        finally:
            dialog.close()


def _stepper_navigation(stepper: ui.stepper, prev_button: bool = True, next_button: bool = True, validate_callback: Callable[[], bool] | None = None):
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
            def go_next():
                if validate_callback is None or validate_callback():
                    stepper.next()
            ui.button("Næste", on_click=go_next)


def _verify_csv_data(fields: list[str], csv_list: list[dict], post_type: PostType) -> list[ValidationMessage]:
    """Verify the input against these rules:
        - Does the data contain any rows?
        - Are there any duplicate receivers?
        - Are all mandatory fields present? (depends on the post type)
        - Does field pattern match for all lines? (max 3 reported)

    Args:
        fields: The column names in the csv.
        csv_list: The input list as a csv dictionary from DictReader.
        post_type: The post type the shipment will be sent as, which
            determines which fields are mandatory.

    Returns:
        A list of validation messages, empty if no problems are found.
    """
    messages: list[ValidationMessage] = []

    # Check that there is any data at all
    if not csv_list:
        messages.append(ValidationMessage("Flettedata indeholder ingen rækker", "negative"))
        return messages

    # Check for duplicate receivers
    if MemoFields.MEMO_MODTAGER.key in fields:
        counter = Counter(line[MemoFields.MEMO_MODTAGER.key] for line in csv_list)
        duplicates = [f"{k}: {v}" for k, v in counter.items() if v > 1]
        if duplicates:
            messages.append(ValidationMessage(
                f"Duplikater fundet i '{MemoFields.MEMO_MODTAGER.key}': " + " - ".join(duplicates),
                "warning",
            ))

    # Check for mandatory fields
    for mf in MemoFields:
        if mf.is_mandatory_for(post_type) and mf.key not in fields:
            messages.append(ValidationMessage(f"'{mf.key}' ikke fundet i data", "negative"))

    # Check for pattern mismatches (show 3 errors max)
    pattern_errors = 0
    for i, row in enumerate(csv_list):
        for mf in MemoFields:
            if mf.key in row and not mf.pattern.fullmatch(row[mf.key]):
                messages.append(ValidationMessage(
                    f"Fejl på linje {i}: Kolonne: '{mf.key}' - Mønster: '{mf.pattern.pattern}'",
                    "negative",
                ))
                pattern_errors += 1
                if pattern_errors >= 3:
                    return messages

    return messages
