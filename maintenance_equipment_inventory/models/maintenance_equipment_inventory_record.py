# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

RESULT_SELECTION = [
    ("ok", "Normal"),
    ("abnormal", "Abnormal"),
    ("lost", "Lost"),
]

# Fields that may still be written on an approved record without going through
# the state machine. This is limited to the mail chatter field that the mail
# framework writes without our ``allow_approved_write`` context (e.g. when an
# attachment is added). Workflow fields (state/approved_*) are intentionally
# excluded: they are only changed via the action methods, which set that
# context, so leaving them out keeps an approved record from being unlocked by
# a raw ``write({"state": "draft"})``.
APPROVED_WRITABLE_FIELDS = {
    "message_main_attachment_id",
}


class MaintenanceEquipmentInventoryRecord(models.Model):
    _name = "maintenance.equipment.inventory.record"
    _description = "Maintenance Equipment Inventory Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "inventory_date desc, id desc"
    _check_company_auto = True

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
        check_company=True,
    )
    company_id = fields.Many2one(
        related="equipment_id.company_id",
        store=True,
        index=True,
        readonly=True,
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
        default="ok",
        tracking=True,
    )
    checked_by_id = fields.Many2one(
        "res.users",
        string="Checked By",
        default=lambda self: self.env.user,
        tracking=True,
    )
    note = fields.Html(string="Remarks")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "maintenance_equipment_inventory_record_attachment_rel",
        "record_id",
        "attachment_id",
        string="Attachments",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
        ],
        string="Status",
        default="draft",
        required=True,
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
        if not self.env.context.get("allow_approved_write"):
            locked = self.filtered(lambda r: r.state == "approved")
            if locked and set(vals) - APPROVED_WRITABLE_FIELDS:
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
            if record.state != "draft":
                raise UserError(_("Only draft records can be submitted for approval."))
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
        self.with_context(allow_approved_write=True).write(
            {
                "state": "draft",
                "approved_by_id": False,
                "approved_date": False,
            }
        )
