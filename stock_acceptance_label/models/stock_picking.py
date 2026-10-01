# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_acceptance_label_pages(self):
        lines = [
            line
            for picking in self
            for move in picking.move_ids
            for line in move.move_line_ids
            if line.state != "cancel"
        ]
        return [lines[index : index + 3] for index in range(0, len(lines), 3)]
