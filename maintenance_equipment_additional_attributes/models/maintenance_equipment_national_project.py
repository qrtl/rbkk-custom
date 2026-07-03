# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceEquipmentNationalProject(models.Model):
    _name = "maintenance.equipment.national.project"
    _description = "Maintenance Equipment National Project"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
