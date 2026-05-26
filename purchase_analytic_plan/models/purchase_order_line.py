# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pol_budget_id = fields.Many2one(
        "account.analytic.account",
        compute="_compute_pol_budget_id",
        store=True,
        readonly=True,
    )

    @api.depends("analytic_distribution")
    def _compute_pol_budget_id(self):
        analytic_account_obj = self.env["account.analytic.account"]
        plan = self.env["account.analytic.plan"].search(
            [("is_pol_budget", "=", True)], limit=1
        )
        for line in self:
            line.pol_budget_id = False
            if not line.analytic_distribution or not plan:
                continue
            account_ids = {
                int(account_id)
                for key in line.analytic_distribution
                for account_id in key.split(",")
            }
            line.pol_budget_id = analytic_account_obj.search(
                [("id", "in", list(account_ids)), ("plan_id", "=", plan.id)],
                limit=1,
            )
