import re

from nicegui import ui, app
from nicegui.events import UploadEventArguments

from OpenPostbud import ui_components
from OpenPostbud.database.check_registration import registration_job, registration_task


@ui.page("/opret_tilmelding")
def page():
    ui_components.header()
    ui.label("Tjek Tilmelding").classes("text-4xl")

    Page()


class Page():
    def __init__(self):
        with ui.column():
            self.name_input = ui.input("Job navn", validation={"Maks 50 tegn": lambda v: len(v) <= 50}).classes("w-full")
            self.desc_input = ui.textarea("Job beskrivelse", validation={"Maks 200 tegn": lambda v: len(v) <= 200}).classes("w-full")
            ui.label("Service:")
            self.type_radio = ui.radio(["Digital Post", "NemSMS"], value="Digital Post").props("inline")
            ui.upload(label="Upload liste", on_upload=self.on_upload, max_files=1, auto_upload=True).props("accept=.txt,.csv")
            ui.button("Indsend", on_click=self.create_job)

    def on_upload(self, e: UploadEventArguments):
        reg_list = e.content.read().decode().splitlines()

        for i, reg in enumerate(reg_list):
            if not re.match(r"^(\d{10})|(\d{6}-\d{4})$", reg):
                ui.notify(f"Input indeholder ugyldigt CPR-nummer på linje {i}: {reg}", type='negative')
                return

        ui.notify(f"{len(reg_list)} CPR-numre uploadet", type='positive')
        self.reg_list = [reg.replace("-", "") for reg in reg_list]

    def create_job(self):
        if self.type_radio.value == "Digital Post":
            job_type = registration_job.JobType.DIGITAL_POST
        else:
            job_type = registration_job.JobType.NEMSMS

        job_id = registration_job.add_registation_job(
            name=self.name_input.value,
            description=self.desc_input.value,
            job_type=job_type,
            created_by=app.storage.user['user_id']
        )

        registration_task.add_registration_tasks(job_id=job_id, registrant_list=self.reg_list)

        ui.navigate.to(f"tjek_tilmelding/{job_id}")
