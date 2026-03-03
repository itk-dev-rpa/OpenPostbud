"""This module defines the worker process that fetches message from Kombit's Beskedfordeler.
It is spawned as a separate process next to the UI process.
"""

from xml.etree import ElementTree
import base64
from datetime import datetime
import logging
import time
import uuid
from pathlib import Path

from sqlalchemy import select
from python_serviceplatformen.authentication import KombitAccess
from python_serviceplatformen import message_broker

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter
from OpenPostbud.database.common import ShipmentStatus
from OpenPostbud.database.nemsms.nemsms_messages import NemSMSMessage


# Silence pika's DEBUG and INFO messages
logging.getLogger("pika").setLevel(logging.WARNING)


# Sender uuids from the Beskedfordeler docs
SENDERS = {
    "96514e13-afdd-44d6-95a8-adc2ca19b127": "Digital Post",
    "afd21f3d-11c7-4f51-b2a6-f31d6480a9fb": "Strålfors",
    "ae5b9a93-c923-40d7-a41a-1eec18374e27": "Edora",
    "6b12182a-4268-4130-bd3e-159f8862c0a1": "KMD Charlie Tango"
}

# Physical letter event uuids from the Beskedfordeler docs
EVENTS_PHYSICAL = {
    "db5a6025-caa3-45c3-8e02-4e6fa8142ade": "Afsendt",
    "dd98e71c-41ac-4305-a47b-8f86b00e639b": "Modtaget Fjern-print",
    "e225a75c-4b63-46c4-9423-77f5c8762445": "Fejlet",
    "e2b30d57-504a-4e2e-ae2d-a1394a9cb0b8": "Klar",
    "e3c0a021-2070-40d4-b7b7-754aeba762e9": "Afleveret til print og kuvertering",
    "e94a0a8b-60a0-42ad-8b83-52c9e15d0fb3": "Modtaget Post Danmark",
    "f03904aa-df6e-417f-bd74-6a01a61adbcf": "Tilbagekaldt",
    "f4e6eb11-0261-4198-8b5d-be92a9b1a35d": "Opdatering fra Post Danmark"
}

# Digital letter events uuids from the Beskedfordeler docs
EVENTS_DIGITAL = {
    "e225a75c-4b63-46c4-9423-77f5c8762445": "Fejlet",
    "f7161a89-5068-4023-bc80-d7f4daad2a2e": "Afleveret Digital Post",
    "eb866ca2-b871-4387-b501-12cde577bd58": "Modtaget Digital Post"
}

# Mapping from Beskedfordeler events to OpenPostbud letter statuses
EVENT_MAP = {
    # Common
    "Fejlet": ShipmentStatus.FAILED,

    # Digital
    "Afleveret Digital Post": ShipmentStatus.DELIVERED,
    "Modtaget Digital Post": ShipmentStatus.DELIVERED,

    # Physical
    "Afsendt": ShipmentStatus.SENT,
    "Modtaget Fjern-print": ShipmentStatus.SENT,
    "Klar": ShipmentStatus.SENT,
    "Afleveret til print og kuvertering": ShipmentStatus.SENT,
    "Modtaget Post Danmark": ShipmentStatus.SENT,
    "Tilbagekaldt": ShipmentStatus.SENT,
    "Opdatering fra Post Danmark": ShipmentStatus.SENT
}

ENVELOPE_NAMESPACES = {
    "default": "urn:oio:sagdok:3.0.0",
    "kuvert": "urn:oio:besked:kuvert:1.0",
    "besked": "urn:besked:kuvert:1.0"
}

MESSAGE_NAMESPACES = {
    "default": "http://serviceplatformen.dk/xml/print/PKO_PostStatus/1/types"
}


def start_process():
    """The entry point of the worker process.

    Raises:
        ValueError: If the Kombit certificate file couldn't be found.
    """
    kombit_access = KombitAccess(config.CVR, config.KOMBIT_CERT_PATH, test=config.KOMBIT_TEST_ENV)

    logging.info("Message broker worker started")

    while True:
        logging.info("Checking queue for new messages")
        for message in message_broker.iterate_queue_messages(config.MESSAGE_BROKER_QUEUE_ID, kombit_access, True):
            message = message.decode()
            try:
                handle_message(message)
            except AttributeError:
                save_failed_message(message)

        logging.info(f"Sleeping for {config.MESSAGE_BROKER_WORKER_SLEEP_TIME} seconds")
        time.sleep(config.MESSAGE_BROKER_WORKER_SLEEP_TIME)


def handle_message(message: str):
    """Decode an incoming message from the message broker.
    Compare the sender id and event id to the known list of ids.
    If the sender id or event id are not recognized log an error
    and ignore the message.

    Args:
        message: The XML message as a string.
    """
    # Decode envelope
    envelope_tree = ElementTree.fromstring(message)

    sender_uuid = envelope_tree.find("kuvert:Beskedkuvert/kuvert:Filtreringsdata/kuvert:BeskedAnsvarligAktoer/default:UUIDIdentifikator", ENVELOPE_NAMESPACES).text
    sender_name = SENDERS.get(sender_uuid)

    event_uuid = envelope_tree.find("kuvert:Beskedkuvert/kuvert:Filtreringsdata/kuvert:ObjektRegistrering/kuvert:ObjektHandling/default:UUIDIdentifikator", ENVELOPE_NAMESPACES).text
    event_name = EVENTS_DIGITAL.get(event_uuid) or EVENTS_PHYSICAL.get(event_uuid)

    message_time = envelope_tree.find("kuvert:Beskedkuvert/kuvert:Leveranceinformation/kuvert:Dannelsestidspunkt/default:TidsstempelDatoTid", ENVELOPE_NAMESPACES).text
    message_time = datetime.fromisoformat(message_time)

    if not sender_name or not event_name:
        logging.error(f"Unknown message received. Sender: {sender_name or sender_uuid} - Event: {event_name or event_uuid} - Message time: {message_time}")
        save_failed_message(message)
        return

    logging.info(f"Message received: {message_time} - {sender_name=} - {event_name=}")

    message_data = envelope_tree.find("kuvert:Beskeddata/besked:Base64", ENVELOPE_NAMESPACES).text
    message_data = base64.b64decode(message_data).decode()

    if event_uuid in EVENTS_DIGITAL:
        handle_digital_post_message(
            message_time=message_time,
            sender_name=sender_name,
            event_name=event_name,
            message_data=message_data)
    else:
        handle_physical_mail_message()


def handle_digital_post_message(message_time: str, sender_name: str, event_name: str, message_data: str):
    """Handle a message from the Digital Post sender.

    Args:
        message_time: The message time from the message.
        sender_name: The sender name from the message.
        event_name: The event name from the message.
        message_data: The decoded base64 message data.
    """
    # Decode message
    message_tree = ElementTree.fromstring(message_data)
    message_uuid = message_tree.find("default:MessageUUID", MESSAGE_NAMESPACES).text
    error_message = message_tree.find("default:FejlDetaljer/default:FejlTekst", MESSAGE_NAMESPACES)
    if error_message is not None:
        error_message = error_message.text

    logging.info(f"Message received: {message_time} - {sender_name=} - {event_name=} - {message_uuid=} - {error_message=}")

    update_letter_status(message_uuid, event_name, error_message)


def handle_physical_mail_message():
    """Handle a message from the a physical mail sender."""
    # We currently don't support physical mail.
    # We don't know how to handle them properly.
    logging.error("Physical mail messages are not currently supported.")


def update_letter_status(transaction_id: str, event_name: str, error: str | None):
    """Update the status of a letter in the database that matches the given transaction id.

    Args:
        transaction_id: The transaction id from the message broker message.
        event_name: The name of the message event as defined in the event dicts.
        error_message: The error from the message if any.
    """
    letter_or_message = get_letter_or_nemsms_message(transaction_id)

    if not letter_or_message:
        logging.error(f"No letter or message with transaction id {transaction_id} found in database.")
        return

    status = EVENT_MAP[event_name]

    if status == ShipmentStatus.DELIVERED:
        letter_or_message.set_status(ShipmentStatus.DELIVERED)
    elif status == ShipmentStatus.FAILED:
        letter_or_message.set_status(ShipmentStatus.FAILED, message=error)
    elif status == ShipmentStatus.SENT:
        letter_or_message.set_status(ShipmentStatus.SENT, message=event_name)

    logging.info(f"Status updated on letter or message {letter_or_message.id}")


def get_letter_or_nemsms_message(transaction_id: str) -> Letter | NemSMSMessage | None:
    """Get a letter or nemsms message with the given transaction id.

    Args:
        transaction_id: The transaction id to look for.

    Returns:
        The letter or NemSMS message with the given transaction id if any.
    """
    with connection.get_session() as session:
        q = select(Letter).where(Letter.transaction_id == transaction_id)
        letter = session.execute(q).scalar_one_or_none()
        if letter:
            return letter

        q = select(NemSMSMessage).where(NemSMSMessage.transaction_id == transaction_id)
        message = session.execute(q).scalar_one_or_none()
        if message:
            return message

    return None


def save_failed_message(message: str):
    """Save the given message to a file in the folder 'failed_messages'.

    Args:
        message: The message to save to a file.
    """
    folder = Path("failed_messages")
    folder.mkdir(exist_ok=True)

    file_path = folder / Path(str(uuid.uuid4())).with_suffix(".xml")
    file_path.write_text(message)

    logging.error(f"Error while reading message. Message saved to {file_path}")


if __name__ == '__main__':
    start_process()
