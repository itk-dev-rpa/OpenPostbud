"""This module defines the worker process that sends Digital Post.
It is spawned as a separate process next to the UI process.
"""

import os
import base64
from datetime import datetime
import logging
import time
import uuid
import json

from sqlalchemy import select, update
from python_serviceplatformen.authentication import KombitAccess
from python_serviceplatformen import digital_post
from python_serviceplatformen.models.message import Message, MessageHeader, MessageBody, MainDocument, Sender, Recipient, File

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter, LetterStatus, MemoFields


def start_process():
    """The entry point of the worker process.

    Raises:
        RuntimeError: If any exception is raised when handling a task.
    """
    if not os.path.isfile(config.KOMBIT_CERT_PATH):
        raise ValueError(f"Couldn't find certificate file: {config.KOMBIT_CERT_PATH}")
    kombit_access = KombitAccess(config.CVR, config.KOMBIT_CERT_PATH, test=config.KOMBIT_TEST_ENV)

    logging.info("Shipment worker started")

    while True:
        letter = get_waiting_letter()
        if letter:
            logging.info(f"Waiting letter found: {letter.id}")
            try:
                send_letter(letter, kombit_access)
            except Exception as e:  # pylint: disable=broad-exception-caught
                set_letter_status(letter, LetterStatus.FAILED, message="Systemfejl")
                logging.error(f"Sending letter {letter.id} failed: {e}")
        else:
            logging.info(f"Sleeping for {config.SHIPMENT_WORKER_SLEEP_TIME} seconds")
            time.sleep(config.SHIPMENT_WORKER_SLEEP_TIME)


def get_waiting_letter() -> Letter | None:
    """Get a waiting letter from the database
    and set its status to 'sending'.

    Returns:
        A waiting letter if any.
    """
    with connection.get_session() as session:
        sub_q = (
            select(Letter.id)
            .where(Letter.status == LetterStatus.WAITING)
            .limit(1)
            .scalar_subquery()
        )

        q = (
            update(Letter)
            .where(Letter.id == sub_q)
            .values(
                status=LetterStatus.SENDING,
                updated_at=datetime.now()
            )
            .returning(Letter)
        )

        letter = session.execute(q).scalar()
        if letter:
            session.commit()
            return letter

    return None


def send_letter(letter: Letter, kombit_access: KombitAccess):
    """Send a letter using Digital Post.
    First checks if the recipient is registered to receive Digital Post.
    """
    if not digital_post.is_registered(letter.recipient_id, 'digitalpost', kombit_access):
        set_letter_status(letter, LetterStatus.FAILED, message="Ikke tilmeldt Digital Post")
        logging.info(f"Letter not sent. The recipient is not registered for Digital Post. {letter.id}")
        return

    document = letter.merge_letter()
    b64_doc = base64.b64encode(document).decode()

    label = json.loads(letter.field_data)[MemoFields.MEMO_LABEL.key]

    message = Message(
        messageHeader=MessageHeader(
            messageType="DIGITALPOST",
            messageUUID=str(uuid.uuid4()),
            label=label,
            sender=Sender(
                senderID=config.CVR,
                idType="CVR",
                label=config.SENDER_LABEL,
            ),
            recipient=Recipient(
                recipientID=letter.recipient_id,
                idType="CPR"
            ),
        ),
        messageBody=MessageBody(
            createdDateTime=datetime.now(),
            mainDocument=MainDocument(
                files=[
                    File(
                        filename="Brev.pdf",
                        encodingFormat="application/pdf",
                        language="da",
                        content=b64_doc
                    )
                ]
            )
        )
    )

    logging.info(f"Sending letter {letter.id}")
    transaction_id = digital_post.send_message("Digital Post", message, kombit_access)
    set_letter_status(letter, LetterStatus.SENT, transaction_id)
    logging.info(f"Letter sent {letter.id}")


def set_letter_status(letter: Letter, status: LetterStatus, transaction_id: str | None = None, message: str | None = None):
    """Set the status of a letter in the database.
    Optionally also set the transaction id of a shipped letter.

    Args:
        letter: The letter to set the status on.
        status: The status to set on the letter.
        transaction_id: The transaction id from Digital Post. Defaults to None.
    """
    with connection.get_session() as session:
        q = (
            update(Letter)
            .where(Letter.id == letter.id)
            .values(
                status=status,
                updated_at=datetime.now(),
                transaction_id=transaction_id,
                message=message
            )
        )
        session.execute(q)
        session.commit()


if __name__ == '__main__':
    start_process()
