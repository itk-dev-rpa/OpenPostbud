"""This module defines the worker process that sends NemSMS.
It is spawned as a separate process next to the UI process.
"""

from datetime import datetime
import logging
import time
import uuid

from sqlalchemy import select, update
from python_serviceplatformen.authentication import KombitAccess
from python_serviceplatformen import digital_post
from python_serviceplatformen.models import message as kombit_message
from python_serviceplatformen.models.message import Sender, Recipient

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.nemsms.nemsms_messages import NemSMSMessage, MessageStatus
from OpenPostbud.database.nemsms import nemsms_shipments


def start_process():
    """The entry point of the worker process.

    Raises:
        ValueError: If the Kombit certificate file couldn't be found.
    """
    kombit_access = KombitAccess(config.CVR, config.KOMBIT_CERT_PATH, test=config.KOMBIT_TEST_ENV)

    logging.info("NemSMS worker started")

    while True:
        message = get_waiting_message()
        if message:
            logging.info(f"Waiting NemSMS message found: {message.id}")
            try:
                send_message(message, kombit_access)
            except Exception as e:  # pylint: disable=broad-exception-caught
                message.set_status(MessageStatus.FAILED, message="Systemfejl")
                logging.error(f"Sending NemSMS {message.id} failed: {e}")
        else:
            logging.info(f"Sleeping for {config.SHIPMENT_WORKER_SLEEP_TIME} seconds")
            time.sleep(config.SHIPMENT_WORKER_SLEEP_TIME)


def get_waiting_message() -> NemSMSMessage | None:
    """Get a waiting message from the database
    and set its status to 'sending'.

    Returns:
        A waiting message if any.
    """
    with connection.get_session() as session:
        sub_q = (
            select(NemSMSMessage.id)
            .where(NemSMSMessage.status == MessageStatus.WAITING)
            .limit(1)
            .scalar_subquery()
        )

        q = (
            update(NemSMSMessage)
            .where(NemSMSMessage.id == sub_q)
            .values(
                status=MessageStatus.SENDING,
                updated_at=datetime.now()
            )
            .returning(NemSMSMessage)
        )

        message = session.execute(q).scalar()
        if message:
            session.commit()
            return message

    return None


def send_message(nemsms_message: NemSMSMessage, kombit_access: KombitAccess):
    """Send a message using NemSMS.
    First checks if the recipient is registered to receive NemSMS.
    """
    if not digital_post.is_registered(nemsms_message.recipient_id, 'nemsms', kombit_access):
        nemsms_message.set_status(MessageStatus.FAILED, message="Ikke tilmeldt NemSMS")
        logging.info(f"Message not sent. The recipient is not registered for NemSMS. {nemsms_message.id}")
        return

    shipment = nemsms_shipments.get_shipment(nemsms_message.shipment_id)

    message_uuid = str(uuid.uuid4())

    message = kombit_message.create_nemsms(
        message_label="NemSMS",
        message_text=shipment.message_text,
        sender=Sender(
            senderID=config.CVR,
            idType="CVR",
            label=config.SENDER_LABEL,
        ),
        recipient=Recipient(
            recipientID=nemsms_message.recipient_id,
            idType="CPR"
        ),
    )

    logging.info(f"Sending NemSMS {nemsms_message.id}")
    transaction_id = digital_post.send_message("NemSMS", message, kombit_access)
    nemsms_message.set_status(MessageStatus.SENT, message_uuid)
    logging.info(f"NemSMS sent {nemsms_message.id} - {message_uuid=} - {transaction_id=}")


if __name__ == '__main__':
    start_process()
