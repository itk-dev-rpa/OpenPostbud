"""This module defines the worker process that sends Digital Post.
It is spawned as a separate process next to the UI process.
"""

import base64
from datetime import datetime
import os
import time
import tempfile
from pathlib import Path
import subprocess

import dotenv
from sqlalchemy import select, update
from python_serviceplatformen.authentication import KombitAccess
from python_serviceplatformen import digital_post
from python_serviceplatformen.models.message import create_digital_post_with_main_document, Sender, Recipient, File

from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter, LetterStatus


dotenv.load_dotenv()


def start_process():
    cvr = os.environ["cvr"]
    cert_path = os.environ["kombit_cert_path"]
    test = bool(os.environ["Kombit_test_env"])
    kombit_access = KombitAccess(cvr, cert_path, test=test)
    sleep_time = float(os.environ["shipment_worker_sleep_time"])

    while True:
        letter = get_waiting_letter()
        if letter:
            send_letter(letter, kombit_access)
        else:
            time.sleep(sleep_time)


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
    document, file_name = letter.merge_letter()
    pdf_document = convert_word_to_pdf(document)
    b64_doc = base64.b64encode(pdf_document).decode()

    message = create_digital_post_with_main_document(
        label="Hallo der er post!",  # TODO
        sender=Sender(
            senderID=os.environ["cvr"],
            idType="CVR",
            label=os.environ["sender_label"],
        ),
        recipient=Recipient(
            recipientID=letter.recipient_id,
            idType="CPR"  # TODO
        ),
        files=[
            File(
                filename="Brev.pdf",
                encodingFormat="application/pdf",  # TODO
                language="da",  # TODO
                content=b64_doc
            )
        ]
    )

    transaction_id = digital_post.send_message("Digital Post", message, kombit_access)
    set_letter_status(letter, LetterStatus.SENT, transaction_id)


def convert_word_to_pdf(document: bytes) -> bytes:
    """Convert a docx file to pdf using LibreOffice.
    This is done by temporarily writing the file to a temp dir.

    Args:
        document: The docx file as bytes.

    Returns:
        The converted pdf file as bytes.
    """
    with tempfile.TemporaryDirectory(suffix="OpenPostbud") as tmpdir:
        word_path = Path(tmpdir) / Path("doc.docx")
        pdf_path = word_path.with_suffix(".pdf")

        with word_path.open("wb") as word_file:
            word_file.write(document)

        subprocess.run(args=[os.environ["path_to_libreoffice"], "--headless", "--convert-to", "pdf", "--outdir", tmpdir, word_path], check=True)

        with pdf_path.open("rb") as pdf_file:
            return pdf_file.read()


def set_letter_status(letter: Letter, status: LetterStatus, transaction_id: str | None = None):
    with connection.get_session() as session:
        q = (
            update(Letter)
            .where(Letter.id == letter.id)
            .values(
                status=status,
                updated_at=datetime.now(),
                transaction_id=transaction_id
            )
        )
        session.execute(q)
        session.commit()


if __name__ == '__main__':
    start_process()
