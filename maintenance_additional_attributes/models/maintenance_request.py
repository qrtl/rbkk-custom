# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    alert_period = fields.Integer(
        help="Amount of time before the scheduled date at which the "
        "responsible user should be alerted about this maintenance.",
    )
    alert_period_unit = fields.Selection(
        selection=[
            ("day", "Days"),
            ("week", "Weeks"),
            ("month", "Months"),
        ],
        default="month",
    )
    alert_sent = fields.Boolean(copy=False)

    def write(self, vals):
        res = super().write(vals)
        # Keep the close date entered on completion.
        if vals.get("close_date") and "stage_id" in vals:
            self.filtered("done").write({"close_date": vals["close_date"]})
        return res
