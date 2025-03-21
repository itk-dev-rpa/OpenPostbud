"""This module runs a FastApi application which exposes a single
endpoint for converting docx to pdf using LibreOffice."""

import dotenv
dotenv.load_dotenv()

from typing import Annotated
import os
import tempfile
from pathlib import Path
import asyncio
import subprocess

from fastapi import FastAPI, File
from fastapi.responses import Response
import uvicorn


PATH_TO_LIBREOFFICE = os.environ["path_to_libreoffice"]

app = FastAPI()


@app.post("/")
async def convert_to_pdf(word_file: Annotated[bytes, File()]):
    """An endpoint for converting word files to pdf.
    It works by writing the word file to a temp dir and then calling Libre Office
    to convert to a pdf file.
    Usage example: 
    with open("Test.docx", "rb") as file:
        pdf_bytes = requests.post("http://127.0.0.1:8000", files={"word_file": file}).content

    Args:
        word_file: The Word file to convert.

    Returns:
        A HTTP response with the pdf files bytes as the content.
    """
    with tempfile.TemporaryDirectory(suffix="OpenPostbud") as tmpdir:
        word_path = Path(tmpdir) / Path("doc.docx")
        pdf_path = word_path.with_suffix(".pdf")

        word_path.write_bytes(word_file)

        await run_subprocess([PATH_TO_LIBREOFFICE, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, str(word_path)])

        pdf_bytes = pdf_path.read_bytes()

    return Response(content=pdf_bytes)


async def run_subprocess(cmd: list[str], timeout: int=30):
    """Call a system command in a async thread.

    Args:
        cmd: The command as a list of arguments.
        timeout: The timeout for the subprocess. Defaults to 30.

    Raises:
        RuntimeError: If the subprocess returned a non-zero error code.
        RuntimeError: If the subprocess timed out.
    """
    process = await asyncio.to_thread(subprocess.Popen, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _, stderr = await asyncio.wait_for(asyncio.to_thread(process.communicate), timeout)
        if process.returncode != 0:
            raise RuntimeError(f"Error: {stderr.decode()}")
    except asyncio.TimeoutError:
        process.kill()
        raise RuntimeError("Process timed out")


if __name__ == "__main__":
    uvicorn.run("pdf_converter:app")
