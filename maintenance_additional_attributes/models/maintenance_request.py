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
        # The standard create() and write() derive the close date from the
        # stage, discarding the date the user recorded (see write()). Return the
        # requests in the original environment so that the context does not leak
        # to the caller.
        return (
            super(
                MaintenanceRequest, self.with_context(maintenance_keep_close_date=True)
            )
            .create(vals_list)
            .with_env(self.env)
        )

    def write(self, vals):
        # The standard create() and write() rewrite the close date whenever the
        # stage changes (today() when the request is completed, empty
        # otherwise), which discards the date the user recorded. Those updates
        # come back here as a write on the close date alone, so ignore them,
        # except for the requests that have no date recorded yet.
        if list(vals) == ["close_date"] and self.env.context.get(
            "maintenance_keep_close_date"
        ):
            requests = self.filtered(lambda request: not request.close_date)
            return super(MaintenanceRequest, requests).write(vals) if requests else True
        # Drop the outdated alert and let it be sent again on the new timing.
        if any(
            field in vals
            for field in ("schedule_date", "alert_period", "alert_period_unit")
        ):
            vals["alert_sent"] = False
            self.activity_unlink(
                ["maintenance_additional_attributes.mail_act_maintenance_alert"]
            )
        res = super(
            MaintenanceRequest, self.with_context(maintenance_keep_close_date=True)
        ).write(vals)
        if "stage_id" in vals:
            # Mark the alert as handled once the request is completed.
            self.filtered("done").activity_feedback(
                ["maintenance_additional_attributes.mail_act_maintenance_alert"]
            )
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
