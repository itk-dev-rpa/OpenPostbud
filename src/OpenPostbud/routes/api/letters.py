"""This module defines routes for the shipments api."""

from datetime import datetime
from typing import Annotated
import base64
import binascii
import json

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from OpenPostbud.database import connection, document_storage
from OpenPostbud.database.common import PostType
from OpenPostbud.database.digital_post import letters
from OpenPostbud.routes.api.dependencies import check_bearer_token


router = APIRouter()


class LetterDetail(BaseModel):
    """A model representing a letter response."""
    id: str
    shipment_id: str | None
    recipient_id: str
    status: str
    status_time: datetime
    sent_as: PostType | None
    letter_pdf: str | None = Field(description="Base64-encoded file contents.")


class SendLetterModel(BaseModel):
    """A model representing a shipment response."""
    recipient_id: str
    memo_label: str | None
    post_type: PostType
    letter_document: str = Field(description="Base64-encoded file contents.")


class SendLetterResponse(BaseModel):
    """A model describing a response from the send_letter endpoint."""
    id: str


@router.post("/send_letter", tags=["Letters"])
def send_letter(letter: SendLetterModel, token: Annotated[dict[str, str], Depends(check_bearer_token)]) -> SendLetterResponse:
    """Send a single letter without a shipment."""

    if letters.MemoFields.MEMO_LABEL.is_mandatory_for(letter.post_type) and letter.memo_label is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Memo label should be set on digital letters.")

    if letter.memo_label is not None and not letters.MemoFields.MEMO_LABEL.pattern.fullmatch(letter.memo_label):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Memo label doesn't match the required pattern: {letters.MemoFields.MEMO_LABEL.pattern.pattern}")

    if not letters.MemoFields.MEMO_MODTAGER.pattern.fullmatch(letter.recipient_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Recipient doesn't match the required pattern: {letters.MemoFields.MEMO_MODTAGER.pattern.pattern}")

    try:
        letter_document = base64.b64decode(letter.letter_document, validate=True)
    except binascii.Error as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Letter document isn't valid base64.") from exc

    new_letter = letters.Letter(
        id=letters.create_letter_id(),
        shipment_id=None,
        recipient_id=letter.recipient_id,
        field_data=json.dumps({letters.MemoFields.MEMO_LABEL.key: letter.memo_label}),
        post_type=letter.post_type,
        created_by=token["sub"]
    )

    document_storage.save_letter_doc(None, new_letter.id, letter_document)

    try:
        with connection.get_session() as session:
            session.add(new_letter)
            session.commit()
    except Exception:
        # Prevent orphan files
        document_storage.delete_single_letter_doc(new_letter.id)
        raise

    return SendLetterResponse(id=new_letter.id)


@router.get("/letter/{letter_id}", tags=["Letters"])
def get_letter(letter_id: str, get_pdf: bool = True) -> LetterDetail:
    """Get a letter by id. Merges and returns the final letter as a pdf
    in base 64."""
    with connection.get_session() as session:
        letter = session.get(letters.Letter, letter_id)

    if not letter:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No letter exists with the given id")

    if get_pdf:
        pdf = letter.merge_letter()
        pdf_64 = base64.b64encode(pdf).decode()
    else:
        pdf_64 = None

    return LetterDetail(
        id=letter.id,
        shipment_id=letter.shipment_id,
        recipient_id=letter.recipient_id,
        status=letter.status,
        status_time=letter.updated_at,
        letter_pdf=pdf_64,
        sent_as=letter.sent_as
    )
