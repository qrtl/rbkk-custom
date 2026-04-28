# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    analytic_plan_purchase_order_line_id = fields.Many2one(
        "account.analytic.plan",
        config_parameter="analytic_plan_field.purchase_order_line.plan_id",
    )
