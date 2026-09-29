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
        return [("move_ids.acceptance_number", operator, value)]

    def get_acceptance_label_pages(self):
        lines = [
            line
            for picking in self
            for move in picking.move_ids
            for line in move.move_line_ids
            if line.state != "cancel"
        ]
        return [lines[index : index + 3] for index in range(0, len(lines), 3)]
