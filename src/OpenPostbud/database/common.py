"""This module contains classes used across the ORM."""

from enum import Enum

class ShipmentStatus(Enum):
    """An enum representing a shipment's status."""
    WAITING = "Afventer"
    SENDING = "Behandles"
    SENT = "Afsendt"
    DELIVERED = "Leveret"
    FAILED = "Fejlet"
    ABORTED = "Afbrudt"
