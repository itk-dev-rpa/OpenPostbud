"""This module contains the pages for looking at registration jobs/tasks."""

import re

from nicegui import ui, APIRouter, app
from nicegui.events import UploadEventArguments

from OpenPostbud import ui_components
from OpenPostbud.database.check_registration import registration_job, registration_task

JOB_COLUMNS = [
    {'name': "id",           'label': "ID",           'field': "id"},
    {'name': "name",         'label': "Navn",         'field': "name"},
    {'name': "job_type",     'label': "Type",         'field': "job_type"},
    {'name': "created_at",   'label': "Oprettet",     'field': "created_at"},
    {'name': "created_by",   'label': "Oprettet af",  'field': "created_by"},
]

TASK_COLUMNS = [
    {'name': "id",          'label': "ID",                'field': "id"},
    {'name': "registrant",  'label': "CPR-nummer",        'field': "registrant"},
    {'name': "updated_at",  'label': "Status Opdateret",  'field': "updated_at"},
    {'name': "status",      'label': "Status",            'field': "status"},
    {'name': "result",      'label': "Resultat",          'field': "result"}
]

COLUMN_DEFAULTS = {'align': 'left',  'sortable': True,  'style': 'padding-right: 5rem'}

router = APIRouter()


TEXT = """Hej
Du er en lille abe, og du skal betale din skat.
Hvis du ikke betaler, så får du ingen bananer.
Dette er besluttet af Borgmester Hans Hansen.
Aarhus Kommune"""


@router.page("/send_nemsms", name="Send NemSMS")
def overview_page():
    """Show the NemSMS page."""
    ui_components.header()
    SendNemSMSPage()


class SendNemSMSPage():
    """A class representing the page
    for creating new NemSMS shipments.
    """
    def __init__(self):
        self.receiver_list = None

        with ui.column().classes("w-96"):
            ui.label("Send NemSMS").classes("text-4xl")
            ui.label("Her kan du oprette en ny NemSMS forsendelse.")
            self.name_input = ui.input("Job navn", validation={"Maks 50 tegn": lambda v: len(v) <= 50}).classes("w-full")
            self.desc_input = ui.textarea("Job beskrivelse", validation={"Maks 200 tegn": lambda v: len(v) <= 200}).classes("w-full")
            ui.separator()
            self.text_area = ui.textarea("Beskedtekst", validation={"Maks 160 tegn": lambda v: len(v) <= 160}, value=TEXT).classes("w-full")
            ui.upload(label="Upload liste", on_upload=self._on_upload, max_files=1, auto_upload=True).props("accept=.txt,.csv")
            ui.button("Indsend", on_click=self._create_job)


    async def _on_upload(self, e: UploadEventArguments):
        """Callback function for when a file is uploaded.
        Checks that the uploaded file only contains valid cpr numbers.
        Also removes any dashes from the cpr numbers.
        """
        receiver_list = await e.file.text()
        receiver_list = receiver_list.splitlines()

        for i, reg in enumerate(receiver_list):
            if not re.match(r"^(\d{10})|(\d{6}-\d{4})$", reg):
                ui.notify(f"Input indeholder ugyldigt CPR-nummer på linje {i}: {reg}", type='negative')
                return

        ui.notify(f"{len(receiver_list)} CPR-numre uploadet", type='positive')
        self.receiver_list = [rec.replace("-", "") for rec in receiver_list]

    def _create_job(self):
        if not self._verify_inputs():
            return

    def _verify_inputs(self) -> bool:
        """Verify all inputs."""
        if not self.name_input.value:
            ui.notify("Indtast venligst et navn på jobbet.", type="warning")
            return False

        if not self.text_area.validate():
            ui.notify("Udfyld venligst en beskedtekst.", type="warning")
            return False

        if not self.receiver_list:
            ui.notify("Upload venligst en liste med CPR-numre først.", type="warning")
            return False

        return True