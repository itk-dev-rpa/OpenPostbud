"""This module handles storing and retrieving documents in
the document storage.
"""


from pathlib import Path
import shutil


STORAGE_FOLDER = Path("OpenPostbud_document_storage")
SHIPMENTS_FOLDER = STORAGE_FOLDER / "Shipments"


def _get_shipment_folder(shipment_id: str) -> Path:
    """Get the folder associated with the given shipment id."""
    return SHIPMENTS_FOLDER / shipment_id


def delete_shipment_docs(shipment_id: str):
    """Delete the given shipment and all letters associated with it."""
    folder_path = _get_shipment_folder(shipment_id)
    if folder_path.exists():
        shutil.rmtree(folder_path)


def _get_letter_path(shipment_id: str, letter_id: str) -> Path:
    """Get the path to the letter's doc file."""
    folder_path = _get_shipment_folder(shipment_id)
    return (folder_path / letter_id).with_suffix(".pdf")


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

    if letter_path.exists():
        return letter_path.read_bytes()

    return None
