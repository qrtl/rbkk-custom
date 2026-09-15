# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    is_chemical_consumption_location = fields.Boolean(
        string="Chemical Consumption Location"
    )
