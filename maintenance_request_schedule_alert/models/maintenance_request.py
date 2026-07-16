# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    alert_period_months = fields.Integer(
        help="Number of months before the scheduled date at which the "
        "responsible user is alerted about this maintenance."
    )
    alert_sent = fields.Boolean(default=False, copy=False)

    def write(self, vals):
        # Re-arm the alert whenever the schedule is (re)set.
        if "schedule_date" in vals and "alert_sent" not in vals:
            vals["alert_sent"] = False
        return super().write(vals)

    @api.model
    def _cron_notify_maintenance_alert(self):
        requests = self.search(
            [
                ("archive", "=", False),
                ("stage_id.done", "=", False),
                ("schedule_date", "!=", False),
                ("alert_period_months", ">", 0),
                ("alert_sent", "=", False),
            ]
        )
        now = fields.Datetime.now()
        for request in requests:
            alert_date = request.schedule_date - relativedelta(
                months=request.alert_period_months
            )
            if now >= alert_date:
                request._notify_maintenance_alert()
                request.alert_sent = True

    def _notify_maintenance_alert(self):
        self.ensure_one()
        user = self.user_id or self.equipment_id.technician_user_id
        if not user:
            return
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=self.schedule_date.date(),
            summary=_("Upcoming maintenance"),
            note=_(
                "Maintenance for %(equipment)s is scheduled on %(date)s.",
                equipment=self.equipment_id.display_name or self.name,
                date=fields.Date.to_string(self.schedule_date.date()),
            ),
            user_id=user.id,
        )
