"""Helpers for building database rows that satisfy foreign-key constraints.

A Letter requires an existing Shipment, and a Shipment requires an existing
Template, so tests need a quick way to set up that chain.
"""

from OpenPostbud.database.digital_post import letters, shipments, templates
from OpenPostbud.database.digital_post.letters import MemoFields


def insert_template(file_name: str = "template.txt", file_data: bytes = b"data") -> int:
    """Create a template and return its id.

    A non-".docx" file name is used so that ``add_template`` skips the
    docx merge-field extraction (which needs external tooling).
    """
    return templates.add_template(file_name=file_name, file_data=file_data)


def make_shipment(
    name: str = "Test Shipment",
    description: str = "A test shipment",
    created_by: str = "tester",
    owner_group: str = "GroupA",
    template_id: int | None = None,
) -> str:
    """Create a shipment (and a backing template if needed) and return its id."""
    if template_id is None:
        template_id = insert_template()
    return shipments.add_shipment(
        name=name,
        description=description,
        created_by=created_by,
        template_id=template_id,
        owner_group=owner_group,
    )


def make_letters(shipment_id: str, rows: list[dict[str, str]]):
    """Add letters to a shipment from csv-style merge-data rows.

    Each row must contain the recipient under ``MemoFields.MEMO_MODTAGER.key``.
    """
    letters.add_letters(shipment_id, rows)


def letter_row(recipient: str = "1234567890", **fields: str) -> dict[str, str]:
    """Build a single csv-style row with the mandatory recipient field."""
    return {MemoFields.MEMO_MODTAGER.key: recipient, **fields}
