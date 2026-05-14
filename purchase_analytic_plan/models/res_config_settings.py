# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pol_analytic_plan_id = fields.Many2one(
        "account.analytic.plan",
        related="company_id.pol_analytic_plan_id",
        readonly=False,
    )
