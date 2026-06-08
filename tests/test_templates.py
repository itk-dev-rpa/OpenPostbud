"""Tests for the template data layer.

A non-".docx" file name is used throughout so that ``add_template`` skips the
docx merge-field extraction, which relies on external tooling.
"""

import unittest

from OpenPostbud.database.digital_post import templates
from tests import builders
from tests.db_test_case import DBTestCase


class TemplateTest(DBTestCase):
    def test_add_and_get_template(self):
        template_id = templates.add_template(file_name="letter.txt", file_data=b"hello")

        template = templates.get_template(template_id)

        self.assertEqual(template.file_name, "letter.txt")
        self.assertEqual(template.file_data, b"hello")
        # Non-docx templates have no merge fields.
        self.assertEqual(template.field_names, "[]")

    def test_get_template_name(self):
        template_id = templates.add_template(file_name="letter.txt", file_data=b"x")

        self.assertEqual(templates.get_template_name(template_id), "letter.txt")

    def test_get_template_by_shipment(self):
        # The result is memoised by shipment id; clear so the test is hermetic.
        templates.get_template_by_shipment.cache_clear()
        self.addCleanup(templates.get_template_by_shipment.cache_clear)

        template_id = builders.insert_template(file_name="letter.txt")
        shipment_id = builders.make_shipment(template_id=template_id)

        template = templates.get_template_by_shipment(shipment_id)

        self.assertEqual(template.id, template_id)
        self.assertEqual(template.file_name, "letter.txt")


if __name__ == "__main__":
    unittest.main()
