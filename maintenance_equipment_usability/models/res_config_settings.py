# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    usability_grace_period_months = fields.Integer(
        related="company_id.usability_grace_period_months",
        readonly=False,
        string="Usability Validity Period (Months)",
    )
