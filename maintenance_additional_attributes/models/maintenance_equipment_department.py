# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceEquipmentDepartment(models.Model):
    _name = "maintenance.equipment.department"
    _description = "Maintenance Equipment Department"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
