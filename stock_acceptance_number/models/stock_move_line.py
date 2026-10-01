# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    acceptance_number = fields.Char(
        copy=False,
        help="Acceptance number of this detailed operation. It is the one "
        "kept on the lot the goods are received in.",
    )

    def _get_acceptance_numbers(self):
        return list(
            dict.fromkeys(
                line.acceptance_number for line in self if line.acceptance_number
            )
        )
