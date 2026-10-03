# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _name = "maintenance.equipment"
    _inherit = ["maintenance.equipment", "image.mixin"]

    set_name = fields.Char()
    vendor_product_name = fields.Char()
    generic_name_id = fields.Many2one(
        comodel_name="maintenance.equipment.generic.name",
        string="General Name",
    )
    is_fixed_asset = fields.Boolean(string="Fixed Asset")
    fixed_asset_code = fields.Char()
    is_gmp = fields.Boolean(string="GMP")
    management_no = fields.Char()
    is_national_project = fields.Boolean(string="National Project")
    national_project_name = fields.Char()
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Used in location",
        domain="[('usage', '=', 'view')]",
        tracking=True,
    )
    manufacturer = fields.Char()
    manufacturer_serial_no = fields.Char()
    purchase_order_id = fields.Many2one(comodel_name="purchase.order")
    acquisition_date = fields.Date()
    usable_temperature = fields.Char(string="Usable Temperature (°C)")
    usable_humidity = fields.Char(string="Usable Humidity (%RH, Non-condensing)")
    is_manufacturer_calibration = fields.Boolean(string="Manufacturer Calibration")
    is_in_house_calibration = fields.Boolean(string="In-house Calibration")
    is_fluorocarbon_inspection = fields.Boolean(string="Fluorocarbon Inspection Target")
