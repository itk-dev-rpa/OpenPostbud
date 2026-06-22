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


class PostType(Enum):
    """An enum representing how a shipment should be sent.

    DIGITAL: Send as Digital Post only.
    PHYSICAL: Send as physical mail (Fysisk Post) only.
    AUTO: Send as Digital Post, falling back to physical mail if the
        recipient is not registered for Digital Post.
    """
    DIGITAL = "Digital Post"
    PHYSICAL = "Fysisk Post"
    AUTO = "Digital med fysisk fallback"
