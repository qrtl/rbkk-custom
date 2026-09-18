# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    acceptance_number = fields.Char(
        compute="_compute_acceptance_number",
        search="_search_acceptance_number",
        help="Summary of the acceptance numbers of the lines of the transfer.",
    )

    @api.depends("move_ids.acceptance_number", "move_ids.state")
    def _compute_acceptance_number(self):
        for picking in self:
            moves = picking.move_ids.filtered(lambda move: move.state != "cancel")
            picking.acceptance_number = ", ".join(moves._get_acceptance_numbers())

    def _search_acceptance_number(self, operator, value):
        # Searched on the lines, whose own number is stored and indexed, rather
        # than on the summary, which is not.
        return [("move_ids.acceptance_number", operator, value)]

    def get_acceptance_label_pages(self):
        """Return the moves to print a label for, grouped per sheet.

        The moves are kept in the order of the transfers they belong to, so that
        the labels of a transfer stay together.
        """
        moves = [
            move
            for picking in self
            for move in picking.move_ids
            if move.state != "cancel"
        ]
        return [moves[index : index + 3] for index in range(0, len(moves), 3)]
