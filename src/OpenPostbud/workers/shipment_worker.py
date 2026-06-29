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
from python_serviceplatformen.models.physical_mail import create_physical_mail
from requests import Timeout, HTTPError

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter, MemoFields
from OpenPostbud.database.digital_post import shipments, field_rules
from OpenPostbud.database.common import ShipmentStatus, PostType


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
            except HTTPError as e:
                response_body = e.response.text if e.response is not None else ""
                letter.set_status(ShipmentStatus.FAILED, message=f"Systemfejl: {e.__class__.__name__}")
                logging.error(f"Sending letter {letter.id} failed: {e} - Response: {response_body!r}")
            except Exception as e:  # pylint: disable=broad-exception-caught
                letter.set_status(ShipmentStatus.FAILED, message=f"Systemfejl: {e.__class__.__name__}")
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
    """Send a letter according to its shipment's post type.

    Digital Post and Auto shipments first check if the recipient is registered
    for Digital Post. Digital shipments fail if the recipient isn't registered,
    while Auto shipments fall back to physical mail. Physical shipments are
    always sent as physical mail.
    """
    shipment = shipments.get_shipment(letter.shipment_id)

    if shipment.post_type == PostType.PHYSICAL:
        send_physical(letter, kombit_access)
        return

    is_registered = digital_post.is_registered(letter.recipient_id, 'digitalpost', kombit_access)

    if shipment.post_type == PostType.DIGITAL:
        if not is_registered:
            letter.set_status(ShipmentStatus.FAILED, message="Ikke tilmeldt Digital Post")
            logging.info(f"Letter not sent. The recipient is not registered for Digital Post. {letter.id}")
            return
        send_digital(letter, kombit_access)
    else:  # PostType.AUTO
        if is_registered:
            send_digital(letter, kombit_access)
        else:
            send_physical(letter, kombit_access)


def send_digital(letter: Letter, kombit_access: KombitAccess):
    """Send a letter as Digital Post."""
    field_data = json.loads(letter.field_data)

    error = field_rules.validate_field_data(field_data, PostType.DIGITAL)
    if error:
        letter.set_status(ShipmentStatus.FAILED, message=error)
        logging.info(f"Letter {letter.id} failed field rule: {error}")
        return

    document = letter.merge_letter()
    b64_doc = base64.b64encode(document).decode()

    label = field_data[MemoFields.MEMO_LABEL.key]

    message_uuid = str(uuid.uuid4())

    id_type = "CPR" if len(letter.recipient_id) == 10 else "CVR"

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
                idType=id_type
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
    letter.set_status(ShipmentStatus.SENT, message_uuid, sent_as=PostType.DIGITAL)
    logging.info(f"Letter sent {letter.id} - {message_uuid=} - {transaction_id=}")


def send_physical(letter: Letter, kombit_access: KombitAccess):
    """Send a letter as physical mail (Fysisk Post).

    The recipient address must be present in the letter itself so it shows
    through the window of the envelope. The recipient id is therefore not sent.
    """
    error = field_rules.validate_field_data(json.loads(letter.field_data), PostType.PHYSICAL)
    if error:
        letter.set_status(ShipmentStatus.FAILED, message=error)
        logging.info(f"Letter {letter.id} failed field rule: {error}")
        return

    document = letter.merge_letter()

    forsendelse = create_physical_mail(config.PHYSICAL_MAIL_FORSENDELSE_TYPE, document)

    logging.info(f"Sending physical letter {letter.id}")
    transaction_id = digital_post.send_physical_mail(forsendelse, kombit_access)
    letter.set_status(ShipmentStatus.SENT, forsendelse.afsendelse_identifikator.value, sent_as=PostType.PHYSICAL)
    logging.info(f"Physical letter sent {letter.id} - {transaction_id=} - afsendelse={forsendelse.afsendelse_identifikator.value}")


if __name__ == '__main__':
    start_process()
