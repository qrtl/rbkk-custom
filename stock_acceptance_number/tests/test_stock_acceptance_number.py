# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


# Run after all modules have initialized their required product fields.
@tagged("post_install", "-at_install")
class TestStockAcceptanceNumber(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "is_storable": True}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "is_storable": True}
        )
        cls.product_lot = cls.env["product.product"].create(
            {"name": "Product Lot", "is_storable": True, "tracking": "lot"}
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

    def _create_lot(self, name):
        return self.env["stock.lot"].create(
            {"name": name, "product_id": self.product_lot.id}
        )

    def _receive_lot(self, lot, acceptance_number):
        picking = self._create_picking(self.product_lot)
        picking.action_confirm()
        picking.move_ids.move_line_ids.write(
            {"lot_id": lot.id, "acceptance_number": acceptance_number}
        )
        return picking

    def test_acceptance_number_is_not_copied(self):
        self.picking.move_ids[0].acceptance_number = "R016-20251017-01"
        self.assertFalse(self.picking.copy().move_ids[0].acceptance_number)

    def test_numbered_lines_are_not_merged(self):
        picking = self._create_picking(self.product_a, self.product_a)
        # Identical lines are merged on confirmation, so one label is printed.
        unnumbered = picking.copy()
        unnumbered.action_confirm()
        self.assertEqual(len(unnumbered.move_ids), 1)
        picking.move_ids[0].acceptance_number = "R016-20251017-01"
        picking.move_ids[1].acceptance_number = "R016-20251017-02"
        picking.action_confirm()
        self.assertEqual(len(picking.move_ids), 2)

    def test_number_is_carried_to_the_detailed_operation(self):
        picking = self._create_picking(self.product_a)
        move = picking.move_ids
        move.acceptance_number = "R016-20251017-01"
        self.assertFalse(move.move_line_ids)
        picking.action_confirm()
        self.assertEqual(move.move_line_ids.acceptance_number, "R016-20251017-01")
        self.assertEqual(move.acceptance_number, "R016-20251017-01")

    def test_number_entered_on_the_line_reaches_its_operations(self):
        picking = self._create_picking(self.product_a)
        picking.action_confirm()
        move = picking.move_ids
        move.acceptance_number = "R016-20251017-01"
        self.assertEqual(move.move_line_ids.acceptance_number, "R016-20251017-01")
        move.acceptance_number = False
        self.assertFalse(move.move_line_ids.acceptance_number)

    def test_line_summarizes_the_numbers_of_its_lots(self):
        picking = self._create_picking(self.product_lot)
        picking.move_ids.product_uom_qty = 2.0
        picking.action_confirm()
        move = picking.move_ids
        move.move_line_ids.quantity = 1.0
        lot_a = self._create_lot("LOT-A")
        lot_b = self._create_lot("LOT-B")
        move.move_line_ids.write(
            {"lot_id": lot_a.id, "acceptance_number": "R016-20251017-01"}
        )
        move.move_line_ids.create(
            {
                "move_id": move.id,
                "product_id": self.product_lot.id,
                "quantity": 1.0,
                "location_id": move.location_id.id,
                "location_dest_id": move.location_dest_id.id,
                "lot_id": lot_b.id,
                "acceptance_number": "R016-20251017-02",
            }
        )
        self.assertEqual(move.acceptance_number, "R016-20251017-01, R016-20251017-02")
        self.assertEqual(lot_a.acceptance_number, "R016-20251017-01")
        self.assertEqual(lot_b.acceptance_number, "R016-20251017-02")
        move.move_line_ids.acceptance_number = "R016-20251017-01"
        self.assertEqual(move.acceptance_number, "R016-20251017-01")

    def test_lot_received_several_times(self):
        lot = self._create_lot("LOT-0001")
        self._receive_lot(lot, "R016-20251017-01")
        picking = self._receive_lot(lot, "R016-20251018-01")
        self.assertEqual(lot.acceptance_number, "R016-20251017-01, R016-20251018-01")
        picking.action_cancel()
        self.assertEqual(lot.acceptance_number, "R016-20251017-01")

    def test_transfer_summary_and_search(self):
        self.picking.move_ids[0].acceptance_number = "R016-20251017-01"
        self.picking.move_ids[1].acceptance_number = "R016-20251017-02"
        self.assertEqual(
            self.picking.acceptance_number, "R016-20251017-01, R016-20251017-02"
        )
        found = self.env["stock.picking"].search(
            [("acceptance_number", "ilike", "20251017-02")]
        )
        self.assertIn(self.picking, found)
        self.assertNotIn(
            self.picking,
            self.env["stock.picking"].search(
                [("acceptance_number", "ilike", "20251019")]
            ),
        )
        self.picking.move_ids[1]._action_cancel()
        self.assertEqual(self.picking.acceptance_number, "R016-20251017-01")
