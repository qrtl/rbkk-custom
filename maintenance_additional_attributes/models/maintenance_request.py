# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.tools.misc import format_datetime


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
        # Drop the outdated alert and let it be sent again on the new timing.
        if any(
            field in vals
            for field in ("schedule_date", "alert_period", "alert_period_unit")
        ):
            vals["alert_sent"] = False
            self.activity_unlink(
                ["maintenance_additional_attributes.mail_act_maintenance_alert"]
            )
        res = super().write(vals)
        if "stage_id" in vals:
            # Mark the alert as handled once the request is completed.
            self.filtered("done").activity_feedback(
                ["maintenance_additional_attributes.mail_act_maintenance_alert"]
            )
        # Keep the close date entered on completion.
        if vals.get("close_date") and "stage_id" in vals:
            self.filtered("done").write({"close_date": vals["close_date"]})
        return res

    def _cron_send_maintenance_alerts(self):
        requests = self.search(
            [
                ("archive", "=", False),
                ("stage_id.done", "=", False),
                ("schedule_date", "!=", False),
                ("alert_period", ">", 0),
                ("alert_period_unit", "!=", False),
                ("alert_sent", "=", False),
            ]
        )
        now = fields.Datetime.now()
        for request in requests:
            alert_date = request.schedule_date - relativedelta(
                **{f"{request.alert_period_unit}s": request.alert_period}
            )
            if now < alert_date:
                continue
            user = request.user_id or request.owner_user_id
            if not user:
                continue
            request.activity_schedule(
                "maintenance_additional_attributes.mail_act_maintenance_alert",
                date_deadline=alert_date.date(),
                summary=_("Scheduled Maintenance"),
                note=_(
                    "The scheduled maintenance date (%s) is approaching.",
                    format_datetime(self.env, request.schedule_date),
                ),
                user_id=user.id,
            )
            request.alert_sent = True
