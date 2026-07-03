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
    gmp_function = fields.Selection(
        selection=[
            ("manufacturing", "Manufacturing"),
            ("qc", "QC"),
        ],
        string="GMP Function",
    )
    gmp_category = fields.Selection(
        selection=[
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
        ],
        string="GMP Category",
    )
    is_measuring_instrument = fields.Boolean(string="Measuring Instrument")
    national_project_id = fields.Many2one(
        comodel_name="maintenance.equipment.national.project",
        string="National Project ID",
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Used in location",
        domain="[('usage', '=', 'internal')]",
        tracking=True,
    )
    manufacturer = fields.Char()
    acquisition_date = fields.Date()
