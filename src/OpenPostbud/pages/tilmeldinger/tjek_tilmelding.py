"""This module contains the pages for looking at registration jobs/tasks."""

from nicegui import ui

from OpenPostbud import ui_components
from OpenPostbud.database.check_registration import registration_job, registration_task

JOB_COLUMNS = [
    {'name': "id", 'label': "ID", 'field': "id", 'align': 'left', 'sortable': True},
    {'name': "name", 'label': "Navn", 'field': "name", 'align': 'left', 'sortable': True},
    {'name': "description", 'label': "Beskrivelse", 'field': "description", 'align': 'left', 'sortable': True},
    {'name': "job_type", 'label': "Type", 'field': "job_type", 'align': 'left', 'sortable': True},
    {'name': "created_at", 'label': "Oprettet", 'field': "created_at", 'align': 'left', 'sortable': True},
    {'name': "created_by", 'label': "Oprettet af", 'field': "created_by", 'align': 'left', 'sortable': True},
]

TASK_COLUMNS = [
    {'name': "id", 'label': "ID", 'field': "id", 'align': 'left', 'sortable': True},
    {'name': "registrant", 'label': "CPR-nummer", 'field': "registrant", 'align': 'left', 'sortable': True},
    {'name': "updated_at", 'label': "Status Opdateret", 'field': "updated_at", 'align': 'left', 'sortable': True},
    {'name': "status", 'label': "Status", 'field': "status", 'align': 'left', 'sortable': True},
    {'name': "result", 'label': "Resultat", 'field': "result", 'align': 'left', 'sortable': True}
]


@ui.page("/tjek_tilmelding")
def overview_page():
    """Show the overview page."""
    ui_components.header()
    OverviewPage()


@ui.page("/tjek_tilmelding/{job_id}")
def detail_page(job_id: int):
    """Show the detail page."""
    ui_components.header()
    DetailPage(job_id)


class OverviewPage():
    """A class representing the overview page.
    Here all registration jobs are shown.
    """
    def __init__(self):
        ui.label("Tjek Tilmelding").classes("text-4xl")
        ui.label("Her kan du se tidligere oprettede tilmeldingjobs eller oprette et nyt.")
        ui.label("Klik på et job på listen for at se flere detaljer.")
        ui.button("Opret nyt job", on_click=lambda: ui.navigate.to("/opret_tilmelding"))

        jobs_list = registration_job.get_registration_jobs()
        rows = [job.to_row_dict() for job in jobs_list]
        table = ui.table(title="Tilmeldingsjobs", columns=JOB_COLUMNS, rows=rows, pagination=50, row_key="id").classes("w-full")
        table.on("rowClick", self.row_click)

    def row_click(self, event):
        """Callback for when a row is clicked.
        Navigate to the detail view for the clicked job.
        """
        row = event.args[1]
        ui.navigate.to(f"/tjek_tilmelding/{row["id"]}")


class DetailPage():
    """A class representing the detail page.
    Here all tasks for the given job is shown.
    """
    def __init__(self, job_id: int):
        ui.label(f"Tilmeldingsjob {job_id}").classes("text-4xl")

        job = registration_job.get_registration_job(job_id)

        with ui.grid(columns=2):
            ui.label("Navn:").classes("text-bold")
            ui.label(job.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui.label(job.description)

            ui.label("Type:").classes("text-bold")
            ui.label(job.job_type)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(job.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(job.created_by)

        tasks = registration_task.get_registration_tasks(job_id)
        rows = [task.to_row_dict() for task in tasks]
        table = ui.table(title="Tilmeldinger", columns=TASK_COLUMNS, rows=rows, pagination=50).classes("w-full")
        ui_components.obscure_column_values(table, "registrant", 7, 4)
