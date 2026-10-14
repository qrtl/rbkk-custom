# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    inventory_record_ids = fields.One2many(
        "maintenance.equipment.inventory.record",
        "equipment_id",
        string="Inventory Records",
    )
    inventory_record_count = fields.Integer(
        compute="_compute_inventory_record_count",
    )
    last_inventory_date = fields.Date(
        compute="_compute_last_inventory",
        store=True,
    )
    last_inventory_result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        compute="_compute_last_inventory",
        store=True,
        help="Pass when every check of the last approved inventory is ticked.",
    )

    @api.depends("inventory_record_ids")
    def _compute_inventory_record_count(self):
        for equipment in self:
            equipment.inventory_record_count = len(equipment.inventory_record_ids)

    @api.depends(
        "inventory_record_ids.state",
        "inventory_record_ids.inventory_date",
        "inventory_record_ids.equipment_found",
        "inventory_record_ids.seal_attached",
        "inventory_record_ids.in_use",
    )
    def _compute_last_inventory(self):
        for equipment in self:
            approved = equipment.inventory_record_ids.filtered(
                lambda r: r.state == "approved"
            )
            last = approved.sorted(
                key=lambda r: (r.inventory_date, r.id), reverse=True
            )[:1]
            equipment.last_inventory_date = last.inventory_date
            if not last:
                equipment.last_inventory_result = False
            elif last.equipment_found and last.seal_attached and last.in_use:
                equipment.last_inventory_result = "pass"
            else:
                equipment.last_inventory_result = "fail"

    def action_create_inventory_records(self):
        """Bulk-create a draft inventory record per selected equipment.

        Equipment whose latest record is not approved are skipped to avoid
        duplicates: that record means the stocktaking round is either still
        unfinished or deliberately closed (refused/cancelled) for that
        equipment. Only the latest record counts, so an old cancelled record
        does not keep the equipment out once a newer one is approved. The
        created records are then shown.
        """
        Record = self.env["maintenance.equipment.inventory.record"]
        latest = {}
        # Records come newest first (the model's _order).
        for record in Record.search([("equipment_id", "in", self.ids)]):
            latest.setdefault(record.equipment_id, record)
        targets = self.filtered(
            lambda equipment: equipment not in latest
            or latest[equipment].state == "approved"
        )
        if not targets:
            raise UserError(
                _(
                    "All the selected equipment already have an open inventory "
                    "record."
                )
            )
        records = Record.create([{"equipment_id": eq.id} for eq in targets])
        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Records"),
            "res_model": "maintenance.equipment.inventory.record",
            "view_mode": "list,form",
            "domain": [("id", "in", records.ids)],
        }
