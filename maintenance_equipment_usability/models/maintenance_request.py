# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    maintenance_result = fields.Selection(
        selection=[
            ("none", "No Result"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        default="none",
        required=True,
        copy=False,
        tracking=True,
    )
    # Drives equipment validity, so changes should leave a trace.
    close_date = fields.Date(copy=False, tracking=True)
    source_request_id = fields.Many2one(
        comodel_name="maintenance.request",
        string="Source Request",
        copy=False,
        readonly=True,
        help="Failed request this follow-up request was created from.",
    )
    followup_request_ids = fields.One2many(
        comodel_name="maintenance.request",
        inverse_name="source_request_id",
        string="Follow-up Requests",
    )
    has_followup_request = fields.Boolean(compute="_compute_has_followup_request")

    @api.depends("followup_request_ids")
    def _compute_has_followup_request(self):
        # Not followup_request_ids: its cache is filtered by record rules.
        source_ids = {
            source.id
            for [source] in self.sudo()._read_group(
                [("source_request_id", "in", self.ids)], ["source_request_id"]
            )
        }
        for request in self:
            request.has_followup_request = request.id in source_ids

    @api.model_create_multi
    def create(self, vals_list):
        return (
            super(MaintenanceRequest, self.with_context(usability_reopened_ids=()))
            .create(vals_list)
            .with_env(self.env)
        )

    def write(self, vals):
        # Core rewrites close_date after a stage change: UTC today on
        # completion, empty otherwise. Keep a recorded date, use the user's
        # date, and clear it only on reopening.
        reopened_ids = self.env.context.get("usability_reopened_ids")
        if reopened_ids is not None and set(vals) == {"close_date"}:
            if vals["close_date"]:
                requests = self.filtered(lambda r: not r.close_date)
                vals = {"close_date": fields.Date.context_today(self)}
            else:
                requests = self.filtered(lambda r: r.id in reopened_ids)
            return super(MaintenanceRequest, requests).write(vals) if requests else True
        if "stage_id" in vals:
            stage = self.env["maintenance.stage"].browse(vals["stage_id"])
            reopened = () if stage.done else tuple(self.filtered("done").ids)
            self = self.with_context(usability_reopened_ids=reopened)
        return super().write(vals)

    @api.constrains("close_date")
    def _check_close_date(self):
        today = fields.Date.context_today(self)
        if any(request.close_date and request.close_date > today for request in self):
            raise ValidationError(_("The close date cannot be in the future."))

    @api.constrains("stage_id", "maintenance_result", "equipment_id")
    def _check_maintenance_result_when_done(self):
        # Only completed results count, and completed requests may be locked
        # (maintenance_request_done_readonly).
        for request in self:
            if (
                request.stage_id.done
                and request.maintenance_result == "none"
                and request.equipment_id
                and not request.equipment_id.maintenance_exempt
            ):
                raise ValidationError(
                    _(
                        "Set the Maintenance Result (Passed or Failed) of '%s' "
                        "before completing it.",
                        request.display_name,
                    )
                )

    def action_create_followup_request(self):
        self.ensure_one()
        if self.maintenance_result != "failed" or self.has_followup_request:
            raise UserError(
                _(
                    "A follow-up request can only be created once, from a "
                    "failed request."
                )
            )
        followup = self.env["maintenance.request"].create(
            {
                "name": _("Follow-up of %s", self.name),
                "equipment_id": self.equipment_id.id,
                "maintenance_team_id": self.maintenance_team_id.id,
                "maintenance_type": "corrective",
                "source_request_id": self.id,
                "company_id": self.company_id.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "maintenance.request",
            "res_id": followup.id,
            "view_mode": "form",
            "target": "current",
        }
