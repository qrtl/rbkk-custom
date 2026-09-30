# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    acceptance_number = fields.Char(related="lot_id.acceptance_number")
