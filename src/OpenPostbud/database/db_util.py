"""This module contains functions that require multiple ORM models.
The purpose of this module is to avoid circular imports.
"""

from sqlalchemy import select, func

from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter
from OpenPostbud.database.nemsms.nemsms_messages import NemSMSMessage


def calculate_shipment_status(shipment_id: str) -> list[tuple[str, int]]:
    """Get all the letter statuses of the letters in the shipment.

    Args:
        shipment_id: The id of the shipment.

    Returns:
        A list of tuples of (Status text, count). Sorted by status text.
    """
    with connection.get_session() as session:
        query = (
            select(Letter.status, func.count(Letter.status))  # pylint: disable=not-callable
            .where(Letter.shipment_id == shipment_id)
            .group_by(Letter.status)
        )
        result = session.execute(query)
        statuses = list((r[0].value, r[1]) for r in result)
        statuses.sort()
        return statuses


def calculate_nemsms_shipment_status(shipment_id: str) -> list[tuple[str, int]]:
    """Get all the message statuses of the messages in the shipment.

    Args:
        shipment_id: The id of the shipment.

    Returns:
        A list of tuples of (Status text, count). Sorted by status text.
    """
    with connection.get_session() as session:
        query = (
            select(NemSMSMessage.status, func.count(NemSMSMessage.status))  # pylint: disable=not-callable
            .where(NemSMSMessage.shipment_id == shipment_id)
            .group_by(NemSMSMessage.status)
        )
        result = session.execute(query)
        statuses = list((r[0].value, r[1]) for r in result)
        statuses.sort()
        return statuses