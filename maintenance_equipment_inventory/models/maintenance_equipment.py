# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from .maintenance_equipment_inventory_record import RESULT_SELECTION


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
        RESULT_SELECTION,
        compute="_compute_last_inventory",
        store=True,
    )

    @api.depends("inventory_record_ids")
    def _compute_inventory_record_count(self):
        data = self.env["maintenance.equipment.inventory.record"]._read_group(
            [("equipment_id", "in", self.ids)],
            ["equipment_id"],
            ["__count"],
        )
        mapped = {equipment.id: count for equipment, count in data}
        for equipment in self:
            equipment.inventory_record_count = mapped.get(equipment.id, 0)

    @api.depends(
        "inventory_record_ids.state",
        "inventory_record_ids.inventory_date",
        "inventory_record_ids.result",
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
            equipment.last_inventory_result = last.result
