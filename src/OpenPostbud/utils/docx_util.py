"""This module contains functions to work with docx files."""

from io import BytesIO
import logging

from docxtpl import DocxTemplate
import requests


def get_merge_fields(word_template: bytes) -> list[str]:
    """Get the list of merge fields in the given docx file.

    Args:
        doc_bytes: A docx file as bytes.

    Returns:
        A sorted list of merge field names.
    """
    template = DocxTemplate(BytesIO(word_template))
    fields = template.get_undeclared_template_variables()
    return sorted(list(fields))


def merge_word_file(word_template: bytes, field_data: dict[str, str]) -> bytes:
    """Merge a Word template with the given merge field values.

    Args:
        word_template: The Word template as bytes.
        field_data: Merge field data as a dict.

    Returns:
        The merged Word file as bytes.
    """
    merged_template = BytesIO()

    template = DocxTemplate(BytesIO(word_template))
    template.render(field_data)
    template.save(merged_template)

    return merged_template.getvalue()


def convert_word_to_pdf(document: bytes) -> bytes:
    """Convert a docx file to pdf using the Gotenberg PDF converter api.

    Args:
        document: The docx file as bytes.

    Returns:
        The converted pdf file as bytes.
    """
    logging.info(f"Sending word file to converter. Size {len(document)}")
    result = requests.post("http://gotenberg:3000/forms/libreoffice/convert", files={"files": ("document.docx", document)}, timeout=30)
    result.raise_for_status()
    logging.info(f"Received pdf from converter. Size: {len(result.content)}")
    return result.content
