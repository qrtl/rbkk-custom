# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestProductChemicalStock(TransactionCase):
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
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        # No aggregation unit: a piece count is not converted.
        cls.uom_unit.category_id.chemical_uom_id = False
        cls.substance = cls.env["product.chemical.substance"].create(
            {"name": "Substance A", "cas_no": "9999920-20-1"}
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.liquid = cls._make_chemical(cls.uom_l)
        cls.counted = cls._make_chemical(cls.uom_unit)

    @classmethod
    def _make_chemical(cls, uom, attribute_line_ids=None):
        return cls.env["product.template"].create(
            {
                "name": f"Test Reagent ({uom.name})",
                "is_storable": True,
                "uom_id": uom.id,
                "uom_po_id": uom.id,
                "is_chemical": True,
                "attribute_line_ids": attribute_line_ids or [],
                "chemical_substance_line_ids": [
                    Command.create(
                        {"substance_id": cls.substance.id, "content_rate": 50.0}
                    )
                ],
            }
        )

    def _add_stock(self, product, location, quantity):
        self.env["stock.quant"]._update_available_quantity(product, location, quantity)

    def _rows(self, product_tmpl):
        # search() without a flush: _depends must push pending data first.
        return self.env["product.chemical.stock"].search(
            [("product_tmpl_id", "=", product_tmpl.id)]
        )

    def test_substance_entered_twice_is_one_row_per_line(self):
        self.liquid.chemical_substance_line_ids = [
            Command.create({"substance_id": self.substance.id, "content_rate": 50.0})
        ]
        self._add_stock(self.liquid.product_variant_id, self.stock_location, 3.0)
        rows = self._rows(self.liquid)
        self.assertEqual(rows.mapped("quantity"), [3.0, 3.0])
        self.assertEqual(rows.mapped("component_amount"), [1500.0, 1500.0])

    def test_amount_is_converted_into_the_aggregation_uom(self):
        # 3 L at 50% is 1500 mL; the quantity stays in the product unit.
        self._add_stock(self.liquid.product_variant_id, self.stock_location, 3.0)
        row = self._rows(self.liquid)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.quantity, 3.0)
        self.assertEqual(row.product_uom_id, self.uom_l)
        self.assertAlmostEqual(row.component_amount, 1500.0)
        self.assertEqual(row.amount_uom_id, self.uom_ml)

    def test_category_without_aggregation_uom_is_left_unconverted(self):
        self._add_stock(self.counted.product_variant_id, self.stock_location, 8.0)
        row = self._rows(self.counted)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.component_amount, 4.0)
        self.assertEqual(row.amount_uom_id, self.uom_unit)

    def test_only_internal_locations_are_reported(self):
        self._add_stock(self.liquid.product_variant_id, self.stock_location, 3.0)
        self._add_stock(self.liquid.product_variant_id, self.customer_location, 5.0)
        rows = self._rows(self.liquid)
        self.assertEqual(rows.location_id, self.stock_location)
        self.assertAlmostEqual(rows.component_amount, 1500.0)

    def test_variants_of_a_product_are_summed_into_one_row(self):
        attribute = self.env["product.attribute"].create(
            {
                "name": "Pack",
                "value_ids": [
                    Command.create({"name": "Small"}),
                    Command.create({"name": "Large"}),
                ],
            }
        )
        product_tmpl = self._make_chemical(
            self.uom_l,
            attribute_line_ids=[
                Command.create(
                    {
                        "attribute_id": attribute.id,
                        "value_ids": [Command.set(attribute.value_ids.ids)],
                    }
                )
            ],
        )
        small, large = product_tmpl.product_variant_ids
        self._add_stock(small, self.stock_location, 3.0)
        self._add_stock(large, self.stock_location, 1.0)
        row = self._rows(product_tmpl)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.quantity, 4.0)
        self.assertAlmostEqual(row.component_amount, 2000.0)
