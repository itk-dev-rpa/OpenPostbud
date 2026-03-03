"""This module defines the worker process that sends Digital Post.
It is spawned as a separate process next to the UI process.
"""

import base64
from datetime import datetime, timedelta
import logging
import time
import uuid
import json

from sqlalchemy import select, update
from python_serviceplatformen.authentication import KombitAccess
from python_serviceplatformen import digital_post
from python_serviceplatformen.models.message import Message, MessageHeader, MessageBody, MainDocument, Sender, Recipient, File
from requests.exceptions import Timeout

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter, MemoFields
from OpenPostbud.database.common import ShipmentStatus


def start_process():
    """The entry point of the worker process.

    Raises:
        ValueError: If the Kombit certificate file couldn't be found.
    """
    kombit_access = KombitAccess(config.CVR, config.KOMBIT_CERT_PATH, test=config.KOMBIT_TEST_ENV)

    logging.info("Shipment worker started")

    while True:
        letter = get_waiting_letter()
        if letter:
            logging.info(f"Waiting letter found: {letter.id}")
            try:
                send_letter(letter, kombit_access)
            except Timeout:
                letter.set_status(ShipmentStatus.WAITING, message="Timeout. Prøver igen.")
                logging.error(f"Sending letter {letter.id} timed out.")
            except Exception as e:  # pylint: disable=broad-exception-caught
                letter.set_status(ShipmentStatus.FAILED, message="Systemfejl: e.__class__.__name__")
                logging.error(f"Sending letter {letter.id} failed: {e}")
        else:
            logging.debug(f"Sleeping for {config.SHIPMENT_WORKER_SLEEP_TIME} seconds")
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
            .where(
                Letter.status == ShipmentStatus.WAITING,
                datetime.now() - timedelta(seconds=config.SHIPMENT_WORKER_DELAY) > Letter.updated_at
            )
            .limit(1)
            .scalar_subquery()
        )

        q = (
            update(Letter)
            .where(Letter.id == sub_q)
            .values(
                status=ShipmentStatus.SENDING,
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
        letter.set_status(ShipmentStatus.FAILED, message="Ikke tilmeldt Digital Post")
        logging.info(f"Letter not sent. The recipient is not registered for Digital Post. {letter.id}")
        return

    document = letter.merge_letter()
    b64_doc = base64.b64encode(document).decode()

    label = json.loads(letter.field_data)[MemoFields.MEMO_LABEL.key]

    message_uuid = str(uuid.uuid4())

    message = Message(
        messageHeader=MessageHeader(
            messageType="DIGITALPOST",
            messageUUID=message_uuid,
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
    letter.set_status(ShipmentStatus.SENT, message_uuid)
    logging.info(f"Letter sent {letter.id} - {message_uuid=} - {transaction_id=}")


if __name__ == '__main__':
    start_process()
