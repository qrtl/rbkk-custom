# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    usability_validity_months = fields.Integer(
        string="Usability Validity Period (Months)",
        default=12,
    )

    @api.constrains("usability_validity_months")
    def _check_usability_validity_months(self):
        if any(company.usability_validity_months < 1 for company in self):
            raise ValidationError(
                _("The usability validity period must be at least one month.")
            )
