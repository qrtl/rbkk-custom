# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


# This module is loaded early in the module graph, so the tests have to run once
# every module is loaded: creating a product otherwise fails on the not-null
# columns of the modules that are not loaded yet.
@tagged("post_install", "-at_install")
class TestStockAcceptanceLabel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor"})
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "is_storable": True,
                "default_code": "SH30221.26",
                "barcode": "1234567890128",
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "is_storable": True}
        )
        cls.picking_type = cls.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        cls.location = cls.env.ref("stock.stock_location_suppliers")
        cls.location_dest = cls.picking_type.default_location_dest_id
        cls.picking = cls._create_picking(cls.product_a, cls.product_b)

    @classmethod
    def _create_picking(cls, *products):
        return cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "partner_id": cls.vendor.id,
                "location_id": cls.location.id,
                "location_dest_id": cls.location_dest.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom_qty": 1.0,
                            "location_id": cls.location.id,
                            "location_dest_id": cls.location_dest.id,
                        }
                    )
                    for product in products
                ],
            }
        )

    def _validate(self, picking):
        picking.action_confirm()
        for move in picking.move_ids:
            move.write({"quantity": move.product_uom_qty, "picked": True})
        if "check_ids" in picking._fields:
            # Pass the quality checks created by the optional quality modules,
            # as they would otherwise block the transfer. One by one, as the
            # quality modules only handle a single check at a time.
            for check in picking.check_ids.filtered(
                lambda check: check.quality_state == "none"
            ):
                check.quality_state = "pass"
        # _action_done() instead of button_validate(), which may return a wizard
        # depending on the modules installed (quality checks, backorders, ...).
        picking._action_done()

    def test_acceptance_number_is_not_copied(self):
        self.picking.move_ids[0].acceptance_number = "R016-20251017-01"
        self.assertFalse(self.picking.copy().move_ids[0].acceptance_number)

    def test_label_pages_layout(self):
        other_picking = self._create_picking(*([self.product_a] * 5))
        pages = (self.picking | other_picking).get_acceptance_label_pages()
        self.assertEqual([len(page) for page in pages], [3, 3, 1])
        # The labels of a transfer stay together, in the order of the transfers.
        self.assertEqual(pages[0][0].picking_id, self.picking)
        self.assertEqual(pages[0][2].picking_id, other_picking)

    def test_cancelled_move_is_skipped(self):
        self.picking.move_ids[0]._action_cancel()
        pages = self.picking.get_acceptance_label_pages()
        self.assertEqual([move.product_id for move in pages[0]], [self.product_b])

    def test_arrival_date(self):
        move = self.picking.move_ids[0]
        self.assertFalse(move.get_acceptance_arrival_date())
        self._validate(self.picking)
        expected = fields.Datetime.context_timestamp(
            self.picking, self.picking.date_done
        ).date()
        self.assertEqual(move.get_acceptance_arrival_date(), expected)

    def test_report_html(self):
        self.picking.move_ids[0].acceptance_number = "R016-20251017-01"
        html = (
            self.env["ir.actions.report"]
            ._render_qweb_html(
                "stock_acceptance_label.report_stock_acceptance_label",
                self.picking.ids,
            )[0]
            .decode()
        )
        self.assertIn("R016-20251017-01", html)
        self.assertIn("SH30221.26", html)
        self.assertEqual(html.count("o_pal_cell"), 2)
