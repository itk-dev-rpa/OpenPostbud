"""This module runs a FastApi application which exposes a single
endpoint for converting docx to pdf using LibreOffice."""

from typing import Annotated
import tempfile
from pathlib import Path
import asyncio
import logging

from fastapi import FastAPI, File
from fastapi.responses import Response
import uvicorn

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
    logging.info(f"Word file received. Size: {len(word_file)}")

    with tempfile.TemporaryDirectory(prefix="OpenPostbud") as tmpdir:
        word_path = Path(tmpdir) / Path("doc.docx")
        pdf_path = word_path.with_suffix(".pdf")

        word_path.write_bytes(word_file)

        process = await asyncio.create_subprocess_exec("libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, str(word_path),
                                                       stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Libreoffice didn't return 0. Return code: {process.returncode} | stdout: {stdout.decode()} | stderr: {stderr.decode()}")

        pdf_bytes = pdf_path.read_bytes()

    logging.info(f"File converted. Result size: {len(pdf_bytes)}")
    return Response(content=pdf_bytes)


if __name__ == "__main__":
    uvicorn.run("pdf_converter:app", host="0.0.0.0", port=8100)
