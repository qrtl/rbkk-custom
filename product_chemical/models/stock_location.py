# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    chemical_amount_ids = fields.One2many(
        "product.chemical.location.amount",
        "location_id",
        string="Chemical Components",
        readonly=True,
    )
