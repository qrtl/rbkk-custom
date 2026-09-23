# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    usability_grace_period_months = fields.Integer(
        string="Usability Validity Period (Months)",
        default=12,
    )
