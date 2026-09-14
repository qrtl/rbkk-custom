# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_acceptance_label_pages(self):
        """Return the moves to print a label for, grouped per sheet.

        The moves are kept in the order of the transfers they belong to, so that
        the labels of a transfer stay together.
        """
        labels_per_page = 3
        moves = [
            move
            for picking in self
            for move in picking.move_ids
            if move.state != "cancel"
        ]
        return [
            moves[index : index + labels_per_page]
            for index in range(0, len(moves), labels_per_page)
        ]
