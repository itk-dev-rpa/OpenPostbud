"""This module handles storing and retrieving documents in
the document storage.
"""


from pathlib import Path
import shutil
from dataclasses import dataclass


STORAGE_FOLDER = Path("OpenPostbud_document_storage")
SHIPMENTS_FOLDER = STORAGE_FOLDER / "Shipments"
SINGLE_LETTERS_FOLDER = STORAGE_FOLDER / "Single_letters"
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
    """A dataclass representing an attachment file."""
    name: str
    data: bytes
    mime_type: str | None = None


def _get_shipment_folder(shipment_id: str) -> Path:
    """Get the folder associated with the given shipment id."""
    return SHIPMENTS_FOLDER / shipment_id


def _get_letter_path(shipment_id: str, letter_id: str) -> Path:
    """Get the path to the doc file of a letter belonging to a shipment."""
    return (_get_shipment_folder(shipment_id) / letter_id).with_suffix(LETTER_SUFFIX)


def _get_single_letter_path(letter_id: str) -> Path:
    """Get the path to the doc file of a single letter without a shipment."""
    return (SINGLE_LETTERS_FOLDER / letter_id).with_suffix(LETTER_SUFFIX)


def _write_doc(doc_path: Path, doc_bytes: bytes):
    """Write a document to the given path, creating the folder if needed."""
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_bytes(doc_bytes)


def _read_doc(doc_path: Path) -> bytes | None:
    """Read the document at the given path if it exists."""
    try:
        return doc_path.read_bytes()
    except FileNotFoundError:
        return None


def delete_shipment_docs(shipment_id: str):
    """Delete all stored documents associated with the given shipment."""
    folder_path = _get_shipment_folder(shipment_id)
    if folder_path.is_dir():
        shutil.rmtree(folder_path)


def save_letter_doc(shipment_id: str, letter_id: str, doc_bytes: bytes):
    """Cache the merged document of a letter belonging to a shipment.
    It's assumed the document is a pdf file.
    """
    _write_doc(_get_letter_path(shipment_id, letter_id), doc_bytes)


def get_letter_doc(shipment_id: str, letter_id: str) -> bytes | None:
    """Get the cached merged document of a letter belonging to a shipment,
    if it has been merged before.
    """
    return _read_doc(_get_letter_path(shipment_id, letter_id))


def save_single_letter_doc(letter_id: str, doc_bytes: bytes):
    """Save the document of a single letter without a shipment.
    It's assumed the document is a pdf file.
    """
    _write_doc(_get_single_letter_path(letter_id), doc_bytes)


def get_single_letter_doc(letter_id: str) -> bytes | None:
    """Get the document of a single letter without a shipment, if it exists."""
    return _read_doc(_get_single_letter_path(letter_id))


def delete_single_letter_doc(letter_id: str):
    """Delete the stored document for a single letter without a shipment."""
    _get_single_letter_path(letter_id).unlink(missing_ok=True)


def _get_attachments_folder(shipment_id: str) -> Path:
    """Get the attachments folder for the given shipment."""
    return _get_shipment_folder(shipment_id) / "attachments"


def get_attachments(shipment_id: str) -> list[Attachment]:
    """Get all attachments attached to the shipment."""
    folder = _get_attachments_folder(shipment_id)

    if not folder.is_dir():
        return []

    result = []

    for file in folder.rglob("*"):
        if file.is_file():
            mime_type = ATTACHMENT_FILE_TYPES[file.suffix.lower()]
            result.append(Attachment(file.name, file.read_bytes(), mime_type))

    return result


def list_attachments(shipment_id: str) -> list[tuple[str, int]]:
    """Return a list of names of all attachments on the shipment.
    Includes the index of the attachment to avoid name collisions.
    """
    folder = _get_attachments_folder(shipment_id)

    if not folder.is_dir():
        return []

    result = []

    for sub_folder in folder.iterdir():
        i = int(sub_folder.name)
        file_name = next(sub_folder.iterdir()).name
        result.append((file_name, i))

    return result


def get_attachment(shipment_id: str, index: int) -> Attachment:
    """Get the attachment file with the given index for the shipment."""
    folder = _get_attachments_folder(shipment_id) / str(index)

    if not folder.is_dir():
        raise ValueError(f"No attachment with index {index} exists for shipment {shipment_id}.")

    file_path = next(folder.iterdir())
    return Attachment(file_path.name, file_path.read_bytes(), ATTACHMENT_FILE_TYPES[file_path.suffix.lower()])


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
