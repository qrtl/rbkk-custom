# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    alert_period_months = fields.Integer(
        string="Alert Period (Months)",
        help="Number of months before the scheduled date at which the "
        "responsible user should be alerted about this maintenance.",
    )
    alert_sent = fields.Boolean(
        copy=False,
    )
