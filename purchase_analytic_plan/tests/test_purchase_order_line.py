# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPurchaseOrderLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan_a = cls.env["account.analytic.plan"].create(
            {"name": "Plan A", "is_pol_analytic_plan": True}
        )
        cls.plan_b = cls.env["account.analytic.plan"].create({"name": "Plan B"})
        cls.account_a = cls.env["account.analytic.account"].create(
            {"name": "Account A", "plan_id": cls.plan_a.id, "company_id": False}
        )
        cls.account_b = cls.env["account.analytic.account"].create(
            {"name": "Account B", "plan_id": cls.plan_b.id, "company_id": False}
        )
        partner = cls.env["res.partner"].create({"name": "Vendor"})
        product = cls.env["product.product"].create(
            {"name": "Product", "type": "consu"}
        )
        cls.order = cls.env["purchase.order"].create({"partner_id": partner.id})
        cls._line_defaults = {
            "order_id": cls.order.id,
            "product_id": product.id,
            "product_qty": 1.0,
            "price_unit": 100.0,
        }

    def _create_line(self, dist=None):
        return self.env["purchase.order.line"].create(
            {**self._line_defaults, **({"analytic_distribution": dist} if dist else {})}
        )

    def test_multiple_accounts_picks_plan_account(self):
        line = self._create_line(
            {str(self.account_a.id): 60.0, str(self.account_b.id): 40.0}
        )
        self.assertEqual(line.pol_analytic_account_id, self.account_a)

    def test_plan_flag_change_recomputes_lines(self):
        line = self._create_line({str(self.account_a.id): 100.0})
        self.assertEqual(line.pol_analytic_account_id, self.account_a)
        self.plan_a.is_pol_analytic_plan = False
        self.assertFalse(line.pol_analytic_account_id)
        self.plan_a.is_pol_analytic_plan = True
        self.assertEqual(line.pol_analytic_account_id, self.account_a)

    def test_duplicate_pol_plan_raises(self):
        with self.assertRaises(ValidationError):
            self.plan_b.is_pol_analytic_plan = True
