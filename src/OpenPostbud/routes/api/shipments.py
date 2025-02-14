"""This module defines routes for the shipments api."""

from datetime import datetime

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from OpenPostbud.database.digital_post import shipments as shipments_db


router = APIRouter()


class ShipmentOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    created_by: str
    status: str
    letter_ids: list[int]



@router.get("/shipments", tags=["Shipments"])
def get_shipments():
    shipments = shipments_db.get_shipments()

    return [s.to_row_dict() for s in shipments]


@router.get("/shipment/{shipment_id}", tags=["Shipments"])
def get_shipment(shipment_id: str):
    shipment = shipments_db.get_shipment(shipment_id)

    if not shipment:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No shipment exists with the given id")

    return shipment.to_row_dict()
