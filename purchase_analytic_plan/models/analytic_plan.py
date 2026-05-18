# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    is_pol_analytic_plan = fields.Boolean(
        string="Use for Purchase Order Lines",
    )

    def write(self, vals):
        res = super().write(vals)
        if "is_pol_analytic_plan" in vals:
            lines = self.env["purchase.order.line"].search(
                [("analytic_distribution", "!=", False)]
            )
            if lines:
                lines._compute_analytic_plan_account_id()
        return res

    @api.constrains("is_pol_analytic_plan")
    def _check_unique_pol_analytic_plan(self):
        for plan in self:
            if plan.is_pol_analytic_plan:
                existing = self.search(
                    [("is_pol_analytic_plan", "=", True), ("id", "!=", plan.id)],
                    limit=1,
                )
                if existing:
                    raise ValidationError(
                        _(
                            "Only one analytic plan can be set for purchase order"
                            "lines. Please disable the existing plan '%(plan)s' first.",
                            plan=existing.name,
                        )
                    )
