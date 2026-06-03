"""This module contains the pages for looking at registration jobs/tasks."""

from nicegui import ui, APIRouter, app

from OpenPostbud import ui_components
from OpenPostbud.database.check_registration import registration_job, registration_task
from OpenPostbud.middleware import authentication

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


@router.page("/tjek_tilmelding", name="Registration Overview")
def overview_page():
    """Show the overview page."""
    ui_components.header()
    RegistrationOverviewPage()


@router.page("/tjek_tilmelding/{job_id}", name="Registration Detail")
def detail_page(job_id: str):
    """Show the detail page."""
    ui_components.header()
    DetailPage(job_id)


class RegistrationOverviewPage():
    """A class representing the overview page.
    Here all registration jobs are shown.
    """
    def __init__(self):
        ui.label("Tjek Tilmelding").classes("text-4xl")
        ui.label("Her kan du se tidligere oprettede tilmeldingjobs eller oprette et nyt.")
        ui.label("Klik på et job på listen for at se flere detaljer.")
        ui.button("Opret nyt job", on_click=lambda: ui.navigate.to(app.url_path_for("Create Registration")))

        jobs_list = registration_job.get_registration_jobs(groups=authentication.get_current_user_groups())
        rows = [job.to_row_dict() for job in jobs_list]
        table = ui.table(title="Tilmeldingsjobs", columns=JOB_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, pagination=50, row_key="id")
        table.on("rowClick", self.row_click)

    def row_click(self, event):
        """Callback for when a row is clicked.
        Navigate to the detail view for the clicked job.
        """
        row = event.args[1]
        ui.navigate.to(app.url_path_for("Registration Detail", job_id=row["id"]))  # pylint: disable=no-member


class DetailPage():
    """A class representing the detail page.
    Here all tasks for the given job is shown.
    """
    def __init__(self, job_id: int):
        ui.label(f"Tilmeldingsjob {job_id}").classes("text-4xl")

        job = registration_job.get_registration_job(job_id, groups=authentication.get_current_user_groups())
        if not job:
            raise LookupError(f"Der findes ingen registreringsjob med id {job_id}")

        with ui.grid(columns=2):
            ui.label("Navn:").classes("text-bold")
            ui.label(job.name)

            ui.label("Beskrivelse:").classes("text-bold")
            ui.label(job.description)

            ui.label("Type:").classes("text-bold")
            ui.label(job.job_type)

            ui.label("Oprettet den:").classes("text-bold")
            ui.label(job.created_at.strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Slettes den:").classes("text-bold")
            ui.label(job.get_deletion_date().strftime("%d/%m/%Y %H:%M:%S"))

            ui.label("Oprettet af:").classes("text-bold")
            ui.label(job.created_by)

        tasks = registration_task.get_registration_tasks(job_id)
        rows = [task.to_row_dict() for task in tasks]
        table = ui_components.SearchTable(title="Tilmeldinger", columns=TASK_COLUMNS, column_defaults=COLUMN_DEFAULTS, rows=rows, pagination=50, search_field=True, download_button=True)
        ui_components.obscure_id_column(table, "registrant")
