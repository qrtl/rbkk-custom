# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    set_name = fields.Char()
    generic_name_id = fields.Many2one(
        comodel_name="maintenance.equipment.generic.name",
        string="General Name",
    )
    is_fixed_asset = fields.Boolean(string="Fixed Asset")
    fixed_asset_code = fields.Char()
    is_gmp = fields.Boolean(string="GMP")
    management_no = fields.Char()
    is_measuring_instrument = fields.Boolean(string="Measuring Instrument")
    national_project = fields.Char()
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Used in location",
        domain="[('usage', '=', 'view')]",
        tracking=True,
    )
    manufacturer = fields.Char()
    manufacturer_serial_no = fields.Char()
    acquisition_date = fields.Date()
    equipment_department_id = fields.Many2one(
        comodel_name="maintenance.equipment.department",
        string="Equipment Department",
    )
