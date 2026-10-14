# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Business fields that are frozen once the record is submitted, so that the
# manager approves the values that were submitted.
LOCKED_FIELDS = {
    "equipment_id",
    "inventory_date",
    "equipment_found",
    "seal_attached",
    "in_use",
    "user_id",
    "checked_by_id",
    "note",
}
# Workflow fields, only written by the action methods through
# _write_workflow(). Being readonly only keeps the UI from writing them; a
# plain write() over RPC would bypass the state and group checks.
WORKFLOW_FIELDS = {"state", "approved_by_id", "approved_date"}


class MaintenanceEquipmentInventoryRecord(models.Model):
    _name = "maintenance.equipment.inventory.record"
    _description = "Maintenance Equipment Inventory Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "inventory_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Equipment",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    serial_no = fields.Char(related="equipment_id.serial_no")
    fixed_asset_code = fields.Char(related="equipment_id.fixed_asset_code")
    company_id = fields.Many2one(
        related="equipment_id.company_id",
        store=True,
        index=True,
    )
    inventory_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    equipment_found = fields.Boolean(tracking=True)
    seal_attached = fields.Boolean(tracking=True)
    in_use = fields.Boolean(
        tracking=True,
        help="Leave unticked when the equipment is idle.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        compute="_compute_user_id",
        store=True,
        readonly=False,
        index=True,
        tracking=True,
    )
    checked_by_id = fields.Many2one(
        "res.users",
        string="Checked By",
        tracking=True,
    )
    note = fields.Html(string="Remarks")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_date = fields.Datetime(
        string="Approved On",
        readonly=True,
        copy=False,
    )

    @api.depends("equipment_id")
    def _compute_user_id(self):
        for record in self:
            record.user_id = record.equipment_id.technician_user_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # New records start as draft; the default may come along in vals.
            if any(vals.get(field) for field in WORKFLOW_FIELDS - {"state"}) or (
                vals.get("state", "draft") != "draft"
            ):
                raise UserError(_("Use the workflow buttons to change the status."))
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "maintenance.equipment.inventory.record"
                ) or _("New")
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & WORKFLOW_FIELDS:
            raise UserError(_("Use the workflow buttons to change the status."))
        if set(vals) & LOCKED_FIELDS and any(
            r.state in ("to_approve", "approved") for r in self
        ):
            raise UserError(
                _(
                    "Submitted or approved inventory records cannot be "
                    "modified. Reset the record to draft first."
                )
            )
        return super().write(vals)

    def _write_workflow(self, vals):
        return super().write(vals)

    def unlink(self):
        if any(r.state == "approved" for r in self):
            raise UserError(_("You cannot delete an approved inventory record."))
        return super().unlink()

    def action_submit(self):
        for record in self:
            if record.state not in ("draft", "refused"):
                raise UserError(
                    _("Only draft or refused records can be submitted for approval.")
                )
            if not record.checked_by_id:
                raise UserError(
                    _(
                        "Set who checked the equipment of %(record)s before "
                        "submitting it.",
                        record=record.name,
                    )
                )
        self._write_workflow({"state": "to_approve"})

    def action_approve(self):
        if not self.env.user.has_group("maintenance.group_equipment_manager"):
            raise UserError(
                _("Only Maintenance Managers can approve inventory records.")
            )
        for record in self:
            if record.state != "to_approve":
                raise UserError(_("Only records pending approval can be approved."))
        self._write_workflow(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approved_date": fields.Datetime.now(),
            }
        )

    def action_refuse(self):
        if not self.env.user.has_group("maintenance.group_equipment_manager"):
            raise UserError(
                _("Only Maintenance Managers can refuse inventory records.")
            )
        if any(r.state != "to_approve" for r in self):
            raise UserError(_("Only records pending approval can be refused."))
        self._write_workflow({"state": "refused"})

    def action_cancel(self):
        # Used when the equipment turns out to be out of scope for the round
        # (e.g. already scrapped). Cancelling instead of deleting keeps the
        # equipment out of the next bulk creation.
        if any(r.state in ("approved", "cancelled") for r in self):
            raise UserError(_("Approved or cancelled records cannot be cancelled."))
        self._write_workflow({"state": "cancelled"})

    def action_reset_to_draft(self):
        if any(r.state == "approved" for r in self) and not self.env.user.has_group(
            "maintenance.group_equipment_manager"
        ):
            raise UserError(
                _(
                    "Only Maintenance Managers can reset approved inventory "
                    "records to draft."
                )
            )
        self._write_workflow(
            {
                "state": "draft",
                "approved_by_id": False,
                "approved_date": False,
            }
        )
