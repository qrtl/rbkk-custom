# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
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

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        # The close date can be recorded before the request is completed, but
        # the standard create() clears it while the request is not in a done
        # stage. Restore the date the user entered.
        for request, vals in zip(requests, vals_list, strict=True):
            if vals.get("close_date") and not request.close_date:
                request.close_date = vals["close_date"]
        return requests

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
        # The standard write() rewrites the close date on every stage change
        # (today() when the request is completed, empty otherwise), so keep
        # track of the date the user entered to restore it afterwards.
        close_dates = (
            {request.id: request.close_date for request in self}
            if "stage_id" in vals
            else {}
        )
        res = super().write(vals)
        if "stage_id" in vals:
            # Mark the alert as handled once the request is completed.
            self.filtered("done").activity_feedback(
                ["maintenance_additional_attributes.mail_act_maintenance_alert"]
            )
            for request in self:
                if "close_date" in vals:
                    close_date = vals["close_date"]
                elif close_dates.get(request.id):
                    close_date = close_dates[request.id]
                else:
                    # No date was ever recorded: let the standard behavior of
                    # stamping the completion date apply.
                    continue
                close_date = fields.Date.to_date(close_date)
                if request.close_date != close_date:
                    request.close_date = close_date
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
            user = request.user_id or request.equipment_id.technician_user_id
            if not user:
                continue
            env = self.env(context={**self.env.context, "lang": user.lang})
            activity = request.activity_schedule(
                "maintenance_additional_attributes.mail_act_maintenance_alert",
                date_deadline=fields.Datetime.context_timestamp(
                    request.with_context(tz=user.tz), alert_date
                ).date(),
                summary=env._("Scheduled Maintenance"),
                note=env._(
                    "The scheduled maintenance date (%s) is approaching.",
                    format_datetime(env, request.schedule_date, tz=user.tz),
                ),
                user_id=user.id,
            )
            if activity:
                request.alert_sent = True
