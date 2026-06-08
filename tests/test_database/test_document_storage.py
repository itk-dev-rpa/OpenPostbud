"""Tests for the document storage helpers (filesystem only, no database).

The module's storage folder is redirected to a temp directory so tests never
touch the real ``OpenPostbud_document_storage`` folder.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from OpenPostbud.database import document_storage


class DocumentStorageTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="openpostbud_docs_")
        shipments_folder = Path(self._tmpdir) / "Shipments"
        self._patcher = patch.object(
            document_storage, "SHIPMENTS_FOLDER", shipments_folder
        )
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_then_get_round_trips(self):
        document_storage.save_letter_doc("S-1", "L-1", b"%PDF-data")

        self.assertEqual(document_storage.get_letter_doc("S-1", "L-1"), b"%PDF-data")

    def test_get_missing_doc_returns_none(self):
        self.assertIsNone(document_storage.get_letter_doc("S-1", "missing"))

    def test_delete_shipment_docs_removes_folder(self):
        document_storage.save_letter_doc("S-1", "L-1", b"a")
        document_storage.save_letter_doc("S-1", "L-2", b"b")

        document_storage.delete_shipment_docs("S-1")

        self.assertIsNone(document_storage.get_letter_doc("S-1", "L-1"))
        self.assertIsNone(document_storage.get_letter_doc("S-1", "L-2"))

    def test_delete_missing_shipment_is_noop(self):
        # Should not raise when there is nothing to delete.
        document_storage.delete_shipment_docs("S-unknown")


if __name__ == "__main__":
    unittest.main()
