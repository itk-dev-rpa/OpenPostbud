"""This module handles storing and retrieving documents in
the document storage.
"""


from pathlib import Path
import shutil
from dataclasses import dataclass
from functools import lru_cache


STORAGE_FOLDER = Path("OpenPostbud_document_storage")
SHIPMENTS_FOLDER = STORAGE_FOLDER / "Shipments"
LETTER_SUFFIX = ".pdf"

# Supported file types per the SF1601 documentation
ATTACHMENT_FILE_TYPES = {
    '.pdf': 'application/pdf',
    '.html': 'text/html',
    '.txt': 'text/plain',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.rtf': 'application/msword',
    '.bmp': 'image/bmp',
    '.gif': 'image/gif',
    '.jpg': 'image/jpeg',
    '.png': 'image/png',
    '.tif': 'image/tiff',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.odt': "application/vnd.oasis.opendocument.text",
    '.ods': "application/vnd.oasis.opendocument.spreadsheet",
}


@dataclass
class Attachment:
    name: str
    data: bytes
    mime_type: str | None = None


def _get_shipment_folder(shipment_id: str) -> Path:
    """Get the folder associated with the given shipment id."""
    return SHIPMENTS_FOLDER / shipment_id


def delete_shipment_docs(shipment_id: str):
    """Delete all stored documents associated with the given shipment."""
    folder_path = _get_shipment_folder(shipment_id)
    if folder_path.is_dir():
        shutil.rmtree(folder_path)


def _get_letter_path(shipment_id: str, letter_id: str) -> Path:
    """Get the path to the letter's doc file."""
    folder_path = _get_shipment_folder(shipment_id)
    return (folder_path / letter_id).with_suffix(LETTER_SUFFIX)


def save_letter_doc(shipment_id: str, letter_id: str, doc_bytes: bytes):
    """Save a letter's document to the document storage.
    It's assumed the document is a pdf file.
    """
    letter_path = _get_letter_path(shipment_id, letter_id)
    letter_path.parent.mkdir(parents=True, exist_ok=True)
    letter_path.write_bytes(doc_bytes)


def get_letter_doc(shipment_id: str, letter_id: str) -> bytes | None:
    """Get a letter's document from the document storage
    if it exists.
    """
    letter_path = _get_letter_path(shipment_id, letter_id)

    try:
        return letter_path.read_bytes()
    except FileNotFoundError:
        return None


def _get_attachments_folder(shipment_id: str) -> Path:
    """Get the attachments folder for the given shipment."""
    return _get_shipment_folder(shipment_id) / "attachments"


@lru_cache(maxsize=1)
def get_attachments(shipment_id: str) -> list[Attachment]:
    """Get all attachments attached to the shipment.
    Must be called after add_attachments for the shipment.
    """
    folder = _get_attachments_folder(shipment_id)

    if not folder.is_dir():
        return []

    result = []

    for file in folder.rglob("*"):
        if file.is_file():
            mime_type = ATTACHMENT_FILE_TYPES[file.suffix]
            result.append(Attachment(file.name, file.read_bytes(), mime_type))

    return result


def add_attachments(shipment_id: str, attachments: list[Attachment]):
    """Add a list of attachments to the shipment.
    This should only ever be called once per shipment.
    Each attachment is stored in a numbered folder to avoid name
    collisions.
    """
    folder = _get_attachments_folder(shipment_id)
    for i, attachment in enumerate(attachments):
        attachment_path = folder / str(i) / attachment.name
        attachment_path.parent.mkdir(parents=True, exist_ok=True)
        attachment_path.write_bytes(attachment.data)
