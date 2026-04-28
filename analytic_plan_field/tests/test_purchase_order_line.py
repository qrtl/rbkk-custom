# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestPurchaseOrderLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan_a = cls.env["account.analytic.plan"].create({"name": "Test Plan A"})
        cls.plan_b = cls.env["account.analytic.plan"].create({"name": "Test Plan B"})
        cls.account_a = cls.env["account.analytic.account"].create(
            {"name": "Test Account A1", "plan_id": cls.plan_a.id}
        )
        cls.account_b = cls.env["account.analytic.account"].create(
            {"name": "Test Account B1", "plan_id": cls.plan_b.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu"}
        )
        cls.order = cls.env["purchase.order"].create({"partner_id": cls.partner.id})
        cls.env["ir.config_parameter"].set_param(
            "analytic_plan_field.purchase_order_line.plan_id", str(cls.plan_a.id)
        )

    def _create_line(self, distribution=None):
        vals = {
            "order_id": self.order.id,
            "product_id": self.product.id,
            "product_qty": 1.0,
            "price_unit": 100.0,
        }
        if distribution is not None:
            vals["analytic_distribution"] = distribution
        return self.env["purchase.order.line"].create(vals)

    def test_account_from_configured_plan(self):
        line = self._create_line({str(self.account_a.id): 100.0})
        self.assertEqual(line.analytic_plan_account_id, self.account_a)

    def test_account_from_other_plan_is_ignored(self):
        line = self._create_line({str(self.account_b.id): 100.0})
        self.assertFalse(line.analytic_plan_account_id)

    def test_no_analytic_distribution(self):
        line = self._create_line()
        self.assertFalse(line.analytic_plan_account_id)

    def test_field_updates_on_distribution_change(self):
        line = self._create_line({str(self.account_b.id): 100.0})
        self.assertFalse(line.analytic_plan_account_id)
        line.analytic_distribution = {str(self.account_a.id): 100.0}
        self.assertEqual(line.analytic_plan_account_id, self.account_a)

    def test_multiple_accounts_picks_plan_account(self):
        line = self._create_line(
            {str(self.account_a.id): 60.0, str(self.account_b.id): 40.0}
        )
        self.assertEqual(line.analytic_plan_account_id, self.account_a)
