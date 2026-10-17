# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    # The components of a manufacturing order are picked from the quants
    # rather than from the lots, so the number of the lot has to be read
    # and searched here as well.
    acceptance_number = fields.Char(related="lot_id.acceptance_number")
