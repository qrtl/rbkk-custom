# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

RESULT_SELECTION = [
    ("normal", "Normal"),
    ("abnormal", "Abnormal"),
    ("lost", "Lost"),
]

# Business fields that are frozen once the record is approved. Workflow fields
# are deliberately left out so that the action methods can still move the
# record through its states; they are protected by being readonly on the model
# (the UI cannot write them) plus the group checks in those methods.
LOCKED_FIELDS = {
    "equipment_id",
    "inventory_date",
    "result",
    "checked_by_id",
    "note",
}


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
    result = fields.Selection(
        RESULT_SELECTION,
        string="Inventory Result",
        required=True,
        default="normal",
        tracking=True,
    )
    checked_by_id = fields.Many2one(
        "res.users",
        string="Checked By",
        default=lambda self: self.env.user,
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "maintenance.equipment.inventory.record"
                ) or _("New")
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & LOCKED_FIELDS and any(r.state == "approved" for r in self):
            raise UserError(
                _(
                    "Approved inventory records cannot be modified. "
                    "Reset the record to draft first."
                )
            )
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
        self.write({"state": "to_approve"})

    def action_approve(self):
        if not self.env.user.has_group("maintenance.group_equipment_manager"):
            raise UserError(
                _("Only Maintenance Managers can approve inventory records.")
            )
        for record in self:
            if record.state != "to_approve":
                raise UserError(_("Only records pending approval can be approved."))
        self.write(
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
        for record in self:
            if record.state != "to_approve":
                raise UserError(_("Only records pending approval can be refused."))
        self.write({"state": "refused"})

    def action_cancel(self):
        # Used when the equipment turns out to be out of scope for the round
        # (e.g. already scrapped). Cancelling instead of deleting keeps the
        # equipment out of the next bulk creation.
        for record in self:
            if record.state == "approved":
                raise UserError(_("Approved inventory records cannot be cancelled."))
        self.write({"state": "cancelled"})

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
        self.write(
            {
                "state": "draft",
                "approved_by_id": False,
                "approved_date": False,
            }
        )
