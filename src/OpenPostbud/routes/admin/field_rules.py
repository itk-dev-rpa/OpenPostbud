"""This module is responsible for the admin page for merge field rules."""

from nicegui import ui, APIRouter

from OpenPostbud import ui_components
from OpenPostbud.database.digital_post import field_rules
from OpenPostbud.database.digital_post.field_rules import RuleType

router = APIRouter()

RULE_COLUMNS = [
    {'name': "field_name",      'label': "Felt",            'field': "field_name"},
    {'name': "rule_type",       'label': "Regel",           'field': "rule_type"},
    {'name': "value",           'label': "Værdi",           'field': "value"},
    {'name': "apply_digital",   'label': "Digital Post",    'field': "apply_digital"},
    {'name': "apply_physical",  'label': "Fysisk Post",     'field': "apply_physical"},
]

COLUMN_DEFAULTS = {'align': 'left', 'sortable': True, 'style': 'padding-right: 5rem'}


@router.page("/field-rules", name="Field Rules")
def field_rules_page():
    """Show the field rules page."""
    ui_components.header()
    FieldRulePage()


class FieldRulePage:
    """A class representing the field rules page."""
    def __init__(self):
        ui.label("Feltregler").classes("text-4xl")
        ui.label(
            "Her kan du oprette ekstra regler for flettefelter. "
            "Reglerne tjekkes når posten afsendes."
        )
        ui.button("Ny regel", on_click=self._add_rule)

        self.table = ui.table(rows=[], columns=RULE_COLUMNS, column_defaults=COLUMN_DEFAULTS)
        self.table.on("rowClick", self._row_click)
        self._update_table()

    def _update_table(self):
        """Update the rules table with the newest data from the database."""
        rows = [rule.to_row_dict() for rule in field_rules.get_field_rules()]
        self.table.rows = rows

    def _row_click(self, event):
        """Open a dialog for the clicked rule row."""
        with ui.dialog(value=True) as dialog, ui.card():
            row = event.args[1]
            ui.label(f"{row['field_name']} - {row['rule_type']}").classes("text-xl")
            ui.label(f"Værdi: {row['value']}")
            with ui.row():
                ui.button("Slet", on_click=lambda e: self._delete_rule(row['id'], dialog))
                ui.button("Luk", on_click=dialog.close)

    async def _add_rule(self):
        """Show a popup to create a new field rule."""
        with ui.dialog(value=True).props('persistent') as dialog, ui.card():
            ui.label("Ny feltregel").classes("text-lg")
            field_name = ui.input("Feltnavn").classes("w-full")
            rule_type = ui.select({rt: rt.value for rt in RuleType}, label="Regel", value=RuleType.NOT_CONTAINS).classes("w-full")
            value = ui.input("Værdi").classes("w-full")
            apply_digital = ui.checkbox("Digital Post", value=True)
            apply_physical = ui.checkbox("Fysisk Post", value=True)
            with ui.row():
                ui.button("Gem", on_click=lambda e: dialog.submit(True))
                ui.button("Luk", on_click=lambda e: dialog.submit(False)).props("flat")

            if not await dialog:
                return

        if not field_name.value or not value.value:
            ui.notify("Udfyld både feltnavn og værdi", type="warning")
            return

        field_rules.create_field_rule(
            field_name.value,
            rule_type.value,
            value.value,
            apply_digital.value,
            apply_physical.value,
        )
        ui.notify("Regel oprettet", type="positive")
        self._update_table()

    async def _delete_rule(self, rule_id: int, dialog: ui.dialog):
        """Show a confirmation popup and delete the rule with the given id."""
        if not await ui_components.question_popup("Vil du slette denne regel?", "Ja", "Nej"):
            return

        if field_rules.delete_field_rule(rule_id):
            ui.notify("Regel slettet", type='positive')
            self._update_table()
            dialog.close()
        else:
            ui.notify("Regel ikke fundet", type='negative')
