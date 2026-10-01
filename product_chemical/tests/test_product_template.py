# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.law = cls.env["product.chemical.law"].create({"name": "Test Law"})
        cls.substance = cls.env["product.chemical.substance"].create(
            {"name": "Substance A", "cas_no": "9999910-10-1"}
        )
        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Reagent",
                "is_storable": True,
                "is_chemical": True,
                "track_chemical_consumption": True,
                "chemical_law_line_ids": [Command.create({"law_id": cls.law.id})],
                "chemical_substance_line_ids": [
                    Command.create(
                        {"substance_id": cls.substance.id, "content_rate": 60.0}
                    )
                ],
            }
        )

    def test_duplicate_keeps_the_composition(self):
        # One2many defaults to copy=False while the two flags, being booleans,
        # are copied regardless. Dropping copy=True therefore yields a duplicate
        # that still presents itself as a tracked chemical but holds no
        # substance at all, so it is reported nowhere and records no
        # consumption -- a silent loss of the very data this module manages.
        copy = self.product_tmpl.copy()
        self.assertTrue(copy.is_chemical)
        self.assertEqual(copy.chemical_substance_line_ids.substance_id, self.substance)
        self.assertAlmostEqual(copy.chemical_substance_line_ids.content_rate, 60.0)
        self.assertEqual(copy.chemical_law_line_ids.law_id, self.law)

    def test_unsetting_is_chemical_clears_the_tracking_flag(self):
        # The write path is the one worth pinning: the form merely hides the
        # flag, so an import or plain ORM code is what walks a non-chemical
        # product into carrying a tracking flag nothing acts on any more.
        self.product_tmpl.write({"is_chemical": False})
        self.assertFalse(self.product_tmpl.track_chemical_consumption)

    def test_creating_a_non_chemical_product_cannot_track_consumption(self):
        product_tmpl = self.env["product.template"].create(
            {"name": "Plain", "track_chemical_consumption": True}
        )
        self.assertFalse(product_tmpl.track_chemical_consumption)

    def _create_document(self, filename, content):
        return self.env["product.template.chemical.document"].create(
            {
                "product_tmpl_id": self.product_tmpl.id,
                "file": base64.b64encode(content),
                "filename": filename,
            }
        )

    def test_only_a_pdf_can_be_opened(self):
        # The file type is read off the stored attachment, not the filename,
        # so a Word file renamed to .pdf is still not offered for opening.
        pdf = self._create_document("sds.pdf", b"%PDF-1.4\n%%EOF")
        renamed = self._create_document("word.pdf", b"plain text")
        self.assertTrue(pdf.is_pdf)
        self.assertFalse(renamed.is_pdf)

    def test_cas_no_must_be_half_width_numbers_and_hyphens(self):
        Substance = self.env["product.chemical.substance"]
        for cas_no in ["６４-１７-５", "64-17", "64_17_5", "CAS-17-5"]:
            with self.subTest(cas_no=cas_no), self.assertRaises(ValidationError):
                Substance.create({"name": "Invalid", "cas_no": cas_no})
