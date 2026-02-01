# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.exceptions import UserError, ValidationError

from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpManualLotName(TestMrpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.group_user").write(
            {
                "implied_ids": [
                    Command.link(cls.env.ref("stock.group_production_lot").id)
                ]
            }
        )
        cls.product_lot = cls.env["product.product"].create(
            {
                "name": "Product with Lot",
                "is_storable": True,
                "tracking": "lot",
                "mrp_manual_lot_name": True,
            }
        )
        cls.product_serial = cls.env["product.product"].create(
            {
                "name": "Product with Serial",
                "is_storable": True,
                "tracking": "serial",
                "mrp_manual_lot_name": True,
            }
        )
        cls.component = cls.env["product.product"].create(
            {
                "name": "Component",
                "is_storable": True,
                "tracking": "none",
            }
        )
        cls.bom_lot = cls.env["mrp.bom"].create(
            {
                "product_id": cls.product_lot.id,
                "product_tmpl_id": cls.product_lot.product_tmpl_id.id,
                "product_uom_id": cls.uom_unit.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create({"product_id": cls.component.id, "product_qty": 1}),
                ],
            }
        )
        cls.bom_serial = cls.env["mrp.bom"].create(
            {
                "product_id": cls.product_serial.id,
                "product_tmpl_id": cls.product_serial.product_tmpl_id.id,
                "product_uom_id": cls.uom_unit.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create({"product_id": cls.component.id, "product_qty": 1}),
                ],
            }
        )

    def _create_mo(self, product, bom):
        mo = self.env["mrp.production"].create(
            {"product_id": product.id, "bom_id": bom.id, "product_qty": 1}
        )
        mo.action_confirm()
        return mo

    def test_manual_lot_name_creation(self):
        """Test that manual lot name is used when creating lot."""
        mo = self._create_mo(self.product_lot, self.bom_lot)
        self.assertTrue(mo.mrp_manual_lot_name)
        mo.lot_producing_name = "CUSTOM-LOT-001"
        mo.qty_producing = 1
        mo.action_generate_serial()
        self.assertEqual(mo.lot_producing_id.name, "CUSTOM-LOT-001")
        self.assertFalse(mo.lot_producing_name)

    def test_manual_serial_name_creation(self):
        """Test that manual serial name is used when creating serial."""
        mo = self._create_mo(self.product_serial, self.bom_serial)
        self.assertTrue(mo.mrp_manual_lot_name)
        mo.lot_producing_name = "CUSTOM-SERIAL-001"
        mo.qty_producing = 1
        mo.action_generate_serial()
        self.assertEqual(mo.lot_producing_id.name, "CUSTOM-SERIAL-001")
        self.assertFalse(mo.lot_producing_name)

    def test_duplicate_lot_name_validation(self):
        """Test that duplicate lot names are rejected."""
        self.env["stock.lot"].create(
            {
                "name": "EXISTING-LOT",
                "product_id": self.product_lot.id,
                "company_id": self.env.company.id,
            }
        )
        mo = self._create_mo(self.product_lot, self.bom_lot)
        with self.assertRaises(ValidationError):
            mo.lot_producing_name = "EXISTING-LOT"

    def test_manual_lot_disabled(self):
        """Test normal behavior when manual lot entry is disabled."""
        self.product_lot.mrp_manual_lot_name = False
        mo = self._create_mo(self.product_lot, self.bom_lot)
        self.assertFalse(mo.mrp_manual_lot_name)
        mo.qty_producing = 1
        mo.action_generate_serial()
        self.assertTrue(mo.lot_producing_id)
        self.assertTrue(mo.lot_producing_id.name)

    def test_button_mark_done_without_lot_name(self):
        """Test that marking done without lot name raises UserError."""
        mo = self._create_mo(self.product_lot, self.bom_lot)
        mo.qty_producing = 1
        with self.assertRaises(UserError):
            mo.button_mark_done()
