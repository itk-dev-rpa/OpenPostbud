"""This module defines the worker process that sends Digital Post.
It is spawned as a separate process next to the UI process.
"""

from datetime import datetime
import time

import dotenv
from sqlalchemy import select, update

from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.letters import Letter, LetterStatus


dotenv.load_dotenv()


def start_process():
    while True:
        letter = get_waiting_letter()
        if letter:
            send_letter(letter)
            set_letter_status(letter, LetterStatus.SENT)
        else:
            break
            time.sleep(60)


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


def send_letter(letter: Letter):
    document, name = letter.merge_letter()
    with open(f"{letter.id}-{name}", 'wb') as file:
        file.write(document)


def set_letter_status(letter: Letter, status: LetterStatus):
    with connection.get_session() as session:
        q = (
            update(Letter)
            .where(Letter.id == letter.id)
            .values(
                status=status,
                updated_at=datetime.now()
            )
        )
        session.execute(q)
        session.commit()


if __name__ == '__main__':
    start_process()
