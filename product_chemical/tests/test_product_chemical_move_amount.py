# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestProductChemicalMoveAmount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_l = cls.env.ref("uom.product_uom_litre")
        cls.uom_ml = cls.env["uom.uom"].create(
            {
                "name": "mL",
                "category_id": cls.uom_l.category_id.id,
                "uom_type": "smaller",
                "factor": 1000.0,
                "rounding": 0.001,
            }
        )
        cls.uom_l.category_id.chemical_uom_id = cls.uom_ml
        cls.substance_a = cls.env["product.chemical.substance"].create(
            {"name": "Substance A", "cas_no": "TEST-00-1"}
        )
        cls.substance_b = cls.env["product.chemical.substance"].create(
            {"name": "Substance B", "cas_no": "TEST-00-2"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Reagent",
                "is_storable": True,
                "uom_id": cls.uom_l.id,
                "uom_po_id": cls.uom_l.id,
                "is_chemical": True,
                "track_chemical_consumption": True,
                "chemical_substance_line_ids": [
                    Command.create(
                        {"substance_id": cls.substance_a.id, "content_rate": 60.0}
                    ),
                    Command.create(
                        {"substance_id": cls.substance_b.id, "content_rate": 40.0}
                    ),
                ],
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.stock_location_2 = cls.env["stock.location"].create(
            {
                "name": "Test Shelf",
                "usage": "internal",
                "location_id": cls.stock_location.id,
            }
        )
        cls.consumption_location = cls.env["stock.location"].create(
            {
                "name": "Chemical Consumption",
                "usage": "internal",
                "location_id": cls.stock_location.id,
                "is_chemical_consumption_location": True,
            }
        )
        cls.tracked_product = cls.product
        cls.untracked_product = cls.env["product.product"].create(
            {
                "name": "Untracked Reagent",
                "is_storable": True,
                "uom_id": cls.uom_l.id,
                "uom_po_id": cls.uom_l.id,
                "is_chemical": True,
                "chemical_substance_line_ids": [
                    Command.create(
                        {"substance_id": cls.substance_a.id, "content_rate": 60.0}
                    ),
                    Command.create(
                        {"substance_id": cls.substance_b.id, "content_rate": 40.0}
                    ),
                ],
            }
        )
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    @classmethod
    def _make_move(cls, location, location_dest, quantity=10.0, product=None):
        move = cls.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": (product or cls.tracked_product).id,
                "product_uom_qty": quantity,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )
        move._action_confirm()
        move.quantity = quantity
        move.picked = True
        move._action_done()
        return move

    def _amount_a(self, move):
        return move.chemical_amount_ids.filtered(
            lambda a: a.substance_id == self.substance_a
        )

    def test_internal_to_consumption_is_recorded_as_negative(self):
        move = self._make_move(self.stock_location, self.consumption_location)
        amounts = move.chemical_amount_ids
        self.assertEqual(len(amounts), 2)
        amount_a = amounts.filtered(lambda a: a.substance_id == self.substance_a)
        # 10 L converted into the aggregation unit (mL) at a 60% content rate.
        self.assertEqual(amount_a.amount_uom_id, self.uom_ml)
        self.assertAlmostEqual(amount_a.amount, -6000.0)

    def test_consumption_to_internal_is_recorded_as_positive(self):
        move = self._make_move(self.consumption_location, self.stock_location)
        amount_a = self._amount_a(move)
        self.assertAlmostEqual(amount_a.amount, 6000.0)

    def test_only_tracked_products_create_records(self):
        move = self._make_move(
            self.stock_location,
            self.consumption_location,
            product=self.untracked_product,
        )
        self.assertFalse(move.chemical_amount_ids)

    def test_regular_internal_transfer_is_not_recorded(self):
        move = self._make_move(self.stock_location, self.stock_location_2)
        self.assertFalse(move.chemical_amount_ids)

    def test_supplier_to_internal_is_not_recorded(self):
        move = self._make_move(self.supplier_location, self.stock_location)
        self.assertFalse(move.chemical_amount_ids)

    def test_internal_to_customer_is_not_recorded(self):
        move = self._make_move(self.stock_location, self.customer_location)
        self.assertFalse(move.chemical_amount_ids)

    def test_amounts_are_snapshots(self):
        # A later revision of the product composition must not rewrite the
        # amounts of past movements, while a correction on the movement itself
        # has to recompute its amount.
        move = self._make_move(self.stock_location, self.consumption_location)
        amount_a = move.chemical_amount_ids.filtered(
            lambda a: a.substance_id == self.substance_a
        )
        self.tracked_product.chemical_substance_line_ids.filtered(
            lambda line: line.substance_id == self.substance_a
        ).content_rate = 30.0
        self.assertAlmostEqual(amount_a.content_rate, 60.0)
        self.assertAlmostEqual(amount_a.amount, -6000.0)
        amount_a.content_rate = 30.0
        self.assertAlmostEqual(amount_a.amount, -3000.0)

    def test_sync_follows_the_composition_of_the_product(self):
        # The rebuild has to replace the records, not recompute them in place:
        # a per-record recompute cannot add a substance registered after the
        # move was validated, nor drop one that was removed from the product.
        move = self._make_move(self.stock_location, self.consumption_location)
        self.tracked_product.chemical_substance_line_ids.filtered(
            lambda line: line.substance_id == self.substance_b
        ).unlink()
        substance_c = self.env["product.chemical.substance"].create(
            {"name": "Substance C", "cas_no": "TEST-00-3"}
        )
        self.tracked_product.chemical_substance_line_ids = [
            Command.create({"substance_id": substance_c.id, "content_rate": 25.0})
        ]
        move.action_sync_chemical_amounts()
        amounts = move.chemical_amount_ids
        self.assertEqual(amounts.substance_id, self.substance_a | substance_c)
        amount_c = amounts.filtered(lambda a: a.substance_id == substance_c)
        self.assertAlmostEqual(amount_c.amount, -2500.0)

    def test_sync_records_a_move_validated_before_installation(self):
        # Backfilling a past move must keep the date of the move, so that the
        # amount lands in the period it was actually handled in.
        move = self._make_move(self.stock_location, self.consumption_location)
        move.chemical_amount_ids.unlink()
        move.action_sync_chemical_amounts()
        self.assertEqual(len(move.chemical_amount_ids), 2)
        self.assertEqual(
            set(move.chemical_amount_ids.mapped("actual_date")), {move.date}
        )
