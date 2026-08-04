# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.stock_acceptance_label.models.stock_move import (
    ARRIVAL_DATE_FIELD_PARAM,
    STATUS_HTML_PARAM,
)


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

    def setUp(self):
        super().setUp()
        # Drop the settings stored in the database, so that the tests describe
        # the behaviour of the module and not how the label happens to be
        # configured in the database they run on.
        config_parameter = self.env["ir.config_parameter"].sudo()
        config_parameter.set_param(ARRIVAL_DATE_FIELD_PARAM, False)
        config_parameter.set_param(STATUS_HTML_PARAM, False)

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

    def _set_arrival_date_field(self, model, name):
        self.env["ir.config_parameter"].sudo().set_param(
            ARRIVAL_DATE_FIELD_PARAM,
            self.env["ir.model.fields"]._get(model, name).id,
        )

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

    def test_arrival_date_falls_back_on_invalid_setting(self):
        self.env["ir.config_parameter"].sudo().set_param(ARRIVAL_DATE_FIELD_PARAM, "0")
        self._validate(self.picking)
        expected = fields.Datetime.context_timestamp(
            self.picking, self.picking.date_done
        ).date()
        self.assertEqual(
            self.picking.move_ids[0].get_acceptance_arrival_date(), expected
        )

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
            self.env["stock.move"]._get_acceptance_arrival_date_field().name,
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
        move.move_line_ids.lot_id = self._create_lot("LOT-0001", "2027-03-30 15:30:00")
        self.assertEqual(move.get_acceptance_lot_names(), "LOT-0001")
        self.assertEqual(move.get_acceptance_expiration_dates(), "2027/03/31")

    def test_lot_without_expiration_date(self):
        picking = self._create_picking(self.product_lot)
        picking.action_confirm()
        move = picking.move_ids[0]
        move.move_line_ids.lot_id = self._create_lot("LOT-0002", False)
        self.assertEqual(move.get_acceptance_lot_names(), "LOT-0002")
        self.assertFalse(move.get_acceptance_expiration_dates())

    def test_several_lots_on_one_line(self):
        picking = self._create_picking(self.product_lot)
        picking.move_ids[0].product_uom_qty = 2.0
        picking.action_confirm()
        move = picking.move_ids[0]
        move.move_line_ids.write({"quantity": 1.0})
        move.move_line_ids[0].lot_id = self._create_lot(
            "LOT-0003", "2027-03-30 15:30:00"
        )
        move.move_line_ids.create(
            {
                "move_id": move.id,
                "product_id": self.product_lot.id,
                "quantity": 1.0,
                "location_id": move.location_id.id,
                "location_dest_id": move.location_dest_id.id,
                "lot_id": self._create_lot("LOT-0004", "2027-04-01 15:30:00").id,
            }
        )
        self.assertEqual(move.get_acceptance_lot_names(), "LOT-0003, LOT-0004")
        self.assertEqual(
            move.get_acceptance_expiration_dates(), "2027/03/31, 2027/04/02"
        )

    def test_status_area_setting(self):
        settings = self.env["res.config.settings"].create({})
        # The setting comes filled in with the default status area.
        self.assertIn("Under Inspection", settings.acceptance_label_status_html)
        settings.acceptance_label_status_html = "<div>Accepted</div>"
        settings.execute()
        self.assertIn("Accepted", self.env["stock.move"].get_acceptance_status_html())
        # Emptying the setting restores the default status area.
        settings.acceptance_label_status_html = "<p><br></p>"
        settings.execute()
        self.assertFalse(
            self.env["ir.config_parameter"].sudo().get_param(STATUS_HTML_PARAM)
        )
        self.assertIn(
            "Under Inspection", self.env["stock.move"].get_acceptance_status_html()
        )

    def test_status_area_is_sanitized(self):
        self.env["ir.config_parameter"].sudo().set_param(
            STATUS_HTML_PARAM, "<div>Accepted</div><script>alert(1)</script>"
        )
        status_html = self.env["stock.move"].get_acceptance_status_html()
        self.assertIn("Accepted", status_html)
        self.assertNotIn("script", status_html)

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
        self.assertEqual(html.count("o_pal_cell"), 2)
        # The barcode is a row of the label, printed for the product that has one.
        self.assertEqual(html.count("o_pal_barcode"), 2)
        self.assertEqual(html.count("<img"), 1)
