# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pol_analytic_plan_id = fields.Many2one(
        "account.analytic.plan",
        string="Analytic Plan for Purchase Order Lines",
    )
