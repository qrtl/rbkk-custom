# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import is_html_empty


# Run after all modules have initialized their required product fields.
@tagged("post_install", "-at_install")
class TestStockAcceptanceLabel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.acceptance_label_arrival_date_field_id = cls.env[
            "ir.model.fields"
        ]._get("stock.picking", "date_done")
        cls.company.acceptance_label_status_html = False
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
        cls.product_lot = cls.env["product.product"].create(
            {
                "name": "Product Lot",
                "is_storable": True,
                "tracking": "lot",
                "use_expiration_date": True,
            }
        )
        # Fixed time zone, as the label prints dates and not datetimes.
        cls.env.user.tz = "Asia/Tokyo"
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
            # Optional quality modules require checks to pass before validation.
            for check in picking.check_ids.filtered(
                lambda check: check.quality_state == "none"
            ):
                check.quality_state = "pass"
        # Finish directly to avoid optional validation wizards.
        picking._action_done()

    def _set_arrival_date_field(self, model, name):
        self.company.acceptance_label_arrival_date_field_id = self.env[
            "ir.model.fields"
        ]._get(model, name)

    def test_acceptance_number_is_not_copied(self):
        self.picking.move_ids[0].acceptance_number = "R016-20251017-01"
        self.assertFalse(self.picking.copy().move_ids[0].acceptance_number)

    def test_numbered_lines_are_not_merged(self):
        picking = self._create_picking(self.product_a, self.product_a)
        # Identical lines are merged on confirmation, so one label is printed.
        unnumbered = picking.copy()
        unnumbered.action_confirm()
        self.assertEqual(len(unnumbered.move_ids), 1)
        # Lines that carry their own acceptance number keep their own label.
        picking.move_ids[0].acceptance_number = "R016-20251017-01"
        picking.move_ids[1].acceptance_number = "R016-20251017-02"
        picking.action_confirm()
        self.assertEqual(len(picking.move_ids), 2)

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
        self.company.acceptance_label_arrival_date_field_id = False
        self.assertEqual(move.get_acceptance_arrival_date(), expected)

    def test_arrival_date_from_configured_field(self):
        self._set_arrival_date_field("stock.picking", "scheduled_date")
        move = self.picking.move_ids[0]
        expected = fields.Datetime.context_timestamp(
            self.picking, self.picking.scheduled_date
        ).date()
        self.assertEqual(move.get_acceptance_arrival_date(), expected)
        # A field of the line itself can be selected as well.
        self._set_arrival_date_field("stock.move", "date_deadline")
        move.date_deadline = "2026-08-03 00:30:00"
        expected = fields.Datetime.context_timestamp(move, move.date_deadline).date()
        self.assertEqual(move.get_acceptance_arrival_date(), expected)

    def test_arrival_date_setting(self):
        settings = self.env["res.config.settings"].create({})
        # The setting reflects the effective date of the transfer by default.
        self.assertEqual(
            settings.acceptance_label_arrival_date_field_id,
            self.env["ir.model.fields"]._get("stock.picking", "date_done"),
        )
        settings.acceptance_label_arrival_date_field_id = self.env[
            "ir.model.fields"
        ]._get("stock.picking", "scheduled_date")
        settings.execute()
        self.assertEqual(
            self.company.acceptance_label_arrival_date_field_id.name,
            "scheduled_date",
        )

    def _create_lot(self, name, expiration_date):
        return self.env["stock.lot"].create(
            {
                "name": name,
                "product_id": self.product_lot.id,
                "expiration_date": expiration_date,
            }
        )

    def test_lot_and_expiration_date(self):
        picking = self._create_picking(self.product_lot)
        picking.action_confirm()
        move = picking.move_ids[0]
        # Nothing is printed as long as the lot of the line is unknown.
        self.assertFalse(move.get_acceptance_lot_names())
        self.assertFalse(move.get_acceptance_expiration_dates())
        # 2027-03-31 00:30 in Asia/Tokyo, to cover the time zone conversion.
        lot = self._create_lot("LOT-0001", "2027-03-30 15:30:00")
        move.move_line_ids.lot_id = lot
        self.assertEqual(move.get_acceptance_lot_names(), "LOT-0001")
        self.assertEqual(move.get_acceptance_expiration_dates(), "2027/03/31")

        lot.expiration_date = False
        self.assertEqual(move.get_acceptance_lot_names(), "LOT-0001")
        self.assertFalse(move.get_acceptance_expiration_dates())

    def test_several_lots_on_one_line(self):
        picking = self._create_picking(self.product_lot)
        picking.move_ids.product_uom_qty = 2.0
        picking.action_confirm()
        move = picking.move_ids[0]
        move.move_line_ids.quantity = 1.0
        lot_a = self._create_lot("LOT-A", "2027-12-30 15:30:00")
        lot_b = self._create_lot("LOT-B", False)
        move.move_line_ids.lot_id = lot_a
        move.move_line_ids.create(
            {
                "move_id": move.id,
                "product_id": self.product_lot.id,
                "quantity": 1.0,
                "location_id": move.location_id.id,
                "location_dest_id": move.location_dest_id.id,
                "lot_id": lot_b.id,
            }
        )
        # A later first date catches sorting; equal and empty dates catch filtering.
        for expiration_date, expected in [
            ("2027-03-30 15:30:00", "2027/12/31, 2027/03/31"),
            ("2027-12-30 15:30:00", "2027/12/31, 2027/12/31"),
            (False, "2027/12/31, "),
        ]:
            with self.subTest(expiration_date=expiration_date):
                lot_b.expiration_date = expiration_date
                self.assertEqual(move.get_acceptance_lot_names(), "LOT-A, LOT-B")
                self.assertEqual(move.get_acceptance_expiration_dates(), expected)

    def test_status_area_setting(self):
        move = self.picking.move_ids[0]
        # The built-in status area is printed as long as the setting is empty.
        self.assertIn("Under Inspection", move.get_acceptance_status_html())
        settings = self.env["res.config.settings"].create(
            {"acceptance_label_status_html": "<div>Accepted</div>"}
        )
        settings.execute()
        self.assertIn("Accepted", move.get_acceptance_status_html())
        # Emptying the setting restores the built-in status area.
        settings.acceptance_label_status_html = "<p><br></p>"
        settings.execute()
        self.assertTrue(is_html_empty(self.company.acceptance_label_status_html))
        self.assertIn("Under Inspection", move.get_acceptance_status_html())

    def test_status_area_is_sanitized(self):
        self.company.acceptance_label_status_html = (
            "<div>Accepted</div><script>alert(1)</script>"
        )
        status_html = self.picking.move_ids[0].get_acceptance_status_html()
        self.assertIn("Accepted", status_html)
        self.assertNotIn("script", status_html)

    def test_settings_are_company_specific(self):
        other_company = self.env["res.company"].create({"name": "Other Company"})
        settings = self.env["res.config.settings"].create(
            {
                "company_id": other_company.id,
                "acceptance_label_arrival_date_field_id": self.env["ir.model.fields"]
                ._get("stock.picking", "scheduled_date")
                .id,
                "acceptance_label_status_html": "<div>Other company</div>",
            }
        )
        settings.execute()
        self.assertEqual(
            other_company.acceptance_label_arrival_date_field_id.name, "scheduled_date"
        )
        self.assertIn("Other company", other_company.acceptance_label_status_html)
        # Printing follows the move's company even when another company is active.
        move = self.picking.move_ids[0].with_company(other_company)
        self.assertFalse(move.get_acceptance_arrival_date())
        self.assertIn("Under Inspection", move.get_acceptance_status_html())

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
        self.assertIn("Under Inspection", html)
        # Counted on the class attributes, as the class names also appear in the
        # selectors of the stylesheet of the report.
        self.assertEqual(html.count('class="o_pal_cell"'), 2)
        # The barcode is a row of the label, printed for the product that has one.
        self.assertEqual(html.count('class="o_pal_value o_pal_barcode"'), 2)
        self.assertEqual(html.count("<img"), 1)
