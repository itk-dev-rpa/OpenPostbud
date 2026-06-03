"""This module contains the pages for looking at registration jobs/tasks."""

import re
from collections import Counter

from nicegui import ui, APIRouter, app
from nicegui.events import UploadEventArguments

from OpenPostbud import ui_components
from OpenPostbud.database.nemsms import nemsms_shipments, nemsms_messages
from OpenPostbud.middleware import authentication

router = APIRouter()


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
            self.message_input = ui.textarea("Beskedtekst", validation={"Maks 160 tegn": lambda v: len(v) <= 160}).classes("w-full")
            self.group_selector = ui_components.GroupSelector()
            ui.upload(label="Upload liste", on_upload=self._on_upload, max_files=1, auto_upload=True).props("accept=.txt,.csv")
            ui.button("Indsend", on_click=self._create_shipment)

    async def _on_upload(self, e: UploadEventArguments):
        """Callback function for when a file is uploaded.
        Checks that the uploaded file only contains valid cpr numbers.
        Also removes any dashes from the cpr numbers.
        """
        receiver_list = await e.file.text(encoding="utf-8-sig")
        receiver_list = receiver_list.splitlines()

        for i, reg in enumerate(receiver_list):
            if not re.match(r"^(\d{10})|(\d{6}-\d{4})$", reg):
                ui.notify(f"Input indeholder ugyldigt CPR-nummer på linje {i}: {reg}", type='negative')
                return

        ui.notify(f"{len(receiver_list)} CPR-numre uploadet", type='positive')
        self.receiver_list = [rec.replace("-", "") for rec in receiver_list]

        # Check for duplicates
        counter = Counter(self.receiver_list)
        for k, v in counter.items():
            if v > 1:
                ui.notify(f"Duplikeret CPR-nummer: {k}", type="warning", timeout=0, close_button="Luk")

    def _create_shipment(self):
        """Create a new NemSMS shipment based on the given UI inputs."""
        if not self._verify_inputs():
            return

        owner_group = self.group_selector.get_group()
        if owner_group is None:
            ui.notify("Du tilhører ingen gruppe og kan ikke oprette forsendelser.", type="warning")
            return

        shipment_id = nemsms_shipments.add_shipment(
            name=self.name_input.value,
            description=self.desc_input.value,
            message_text=self.message_input.value,
            created_by=authentication.get_current_user(),
            owner_group=owner_group
        )

        nemsms_messages.add_messages(shipment_id, self.receiver_list)
        ui.navigate.to(app.url_path_for("NemSMS Detail", shipment_id=shipment_id))  # pylint: disable=no-member

    def _verify_inputs(self) -> bool:
        """Verify all inputs."""
        if not self.name_input.value:
            ui.notify("Indtast venligst et navn på jobbet.", type="warning")
            return False

        if not self.message_input.validate():
            ui.notify("Udfyld venligst en beskedtekst.", type="warning")
            return False

        if not self.receiver_list:
            ui.notify("Upload venligst en liste med CPR-numre først.", type="warning")
            return False

        return True
