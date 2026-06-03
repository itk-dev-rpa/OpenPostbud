"""This module defines routes for the shipments api."""

from datetime import datetime
from typing import Annotated
import base64

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from OpenPostbud.database import connection
from OpenPostbud.database.digital_post import shipments as shipments_db
from OpenPostbud.database.digital_post import letters as letters_db
from OpenPostbud.routes.api.dependencies import check_bearer_token, TokenData


router = APIRouter()


class ShipmentModel(BaseModel):
    """A pydantic model representing a shipment response."""
    id: str
    name: str
    created_at: datetime
    created_by: str


class ShipmentDetail(ShipmentModel):
    """A pydantic model representing a shipment response
    including a list of letter ids and description.
    """
    description: str
    letter_ids: list[str]


class LetterDetail(BaseModel):
    """A pydantic model representing a letter response."""
    id: str
    shipment_id: str
    recipient_id: str
    status: str
    letter_pdf: str


@router.get("/shipments", tags=["Shipments"])
def get_shipments(token: Annotated[TokenData, Depends(check_bearer_token)]) -> list[ShipmentModel]:
    """Get all shipments owned by the token's group and return as a list."""
    shipments = shipments_db.get_shipments(groups=[token.group])

    return [
        ShipmentModel(
            id=s.id,
            name=s.name,
            created_at=s.created_at,
            created_by=s.created_by
        )
        for s in shipments
    ]


@router.get("/shipment/{shipment_id}", tags=["Shipments"], response_model=ShipmentDetail)
def get_shipment(shipment_id: str, token: Annotated[TokenData, Depends(check_bearer_token)]) -> ShipmentDetail:
    """Get a shipment by id."""

    shipment = shipments_db.get_shipment(shipment_id, groups=[token.group])

    if not shipment:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No shipment exists with the given id")

    letters = letters_db.get_letters(shipment.id)
    letter_ids = [letter.id for letter in letters]

    return ShipmentDetail(
        id=shipment.id,
        name=shipment.name,
        description=shipment.description,
        created_at=shipment.created_at,
        created_by=shipment.created_by,
        letter_ids=letter_ids
    )


@router.get("/letter/{letter_id}", tags=["Letters"])
def get_letter(letter_id: str, token: Annotated[TokenData, Depends(check_bearer_token)]) -> LetterDetail:
    """Get a letter by id. Merges and returns the final letter as a pdf
    in base 64."""
    with connection.get_session() as session:
        letter = session.get(letters_db.Letter, letter_id)

    if not letter:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No letter exists with the given id")

    # Verify the letter's shipment is owned by the token's group.
    if not shipments_db.get_shipment(letter.shipment_id, groups=[token.group]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No letter exists with the given id")

    pdf = letter.merge_letter()
    pdf_64 = base64.b64encode(pdf).decode()

    return LetterDetail(
        id=letter.id,
        shipment_id=letter.shipment_id,
        recipient_id=letter.recipient_id,
        status=letter.status,
        letter_pdf=pdf_64
    )
