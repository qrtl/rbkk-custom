# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AnalyticPlanAccountMixin(models.AbstractModel):
    _name = "analytic.plan.account.mixin"
    _description = "Analytic Plan Account Mixin"

    # Override in each inheriting model with the ir.config_parameter key
    # that stores the analytic plan ID to filter by.
    _analytic_plan_config_param = ""

    analytic_plan_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Plan Account",
        compute="_compute_analytic_plan_account",
        store=True,
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_plan_account(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(self._analytic_plan_config_param)
        )
        plan_id = int(param) if param else 0
        for rec in self:
            rec.analytic_plan_account_id = False
            if not rec.analytic_distribution or not plan_id:
                continue
            account_ids = set()
            for key in rec.analytic_distribution:
                account_ids.update(int(x) for x in key.split(","))
            rec.analytic_plan_account_id = self.env["account.analytic.account"].search(
                [("id", "in", list(account_ids)), ("plan_id", "=", plan_id)],
                limit=1,
            )
