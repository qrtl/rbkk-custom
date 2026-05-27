# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    analytic_budget_id = fields.Many2one(
        "account.analytic.account",
        compute="_compute_analytic_budget_id",
        store=True,
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_budget_id(self):
        plan = self.env["account.analytic.plan"].search(
            [("is_budget", "=", True)], limit=1
        )
        if not plan:
            self.analytic_budget_id = False
            return
        for line in self:
            line.analytic_budget_id = line.distribution_analytic_account_ids.filtered(
                lambda a: a.plan_id == plan
            )[:1]
