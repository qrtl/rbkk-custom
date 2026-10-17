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
