# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceEquipmentGenericName(models.Model):
    _name = "maintenance.equipment.generic.name"
    _description = "Maintenance Equipment General Name"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
