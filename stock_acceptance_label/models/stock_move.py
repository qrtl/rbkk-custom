# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    acceptance_number = fields.Char(
        compute="_compute_acceptance_number",
        inverse="_inverse_acceptance_number",
        store=True,
        readonly=False,
        copy=False,
        help="Summary of the acceptance numbers of the detailed operations of "
        "the line. A line of a product without tracking can be numbered here "
        "directly; a tracked one is numbered per lot in its detailed "
        "operations.",
    )

    @api.depends("move_line_ids.acceptance_number")
    def _compute_acceptance_number(self):
        for move in self:
            move.acceptance_number = ", ".join(
                move.move_line_ids._get_acceptance_numbers()
            )

    def _inverse_acceptance_number(self):
        for move in self:
            if move.has_tracking != "none":
                continue
            move.move_line_ids.acceptance_number = move.acceptance_number

    def _get_acceptance_numbers(self):
        return list(
            dict.fromkeys(
                number
                for move in self
                for number in (
                    move.move_line_ids._get_acceptance_numbers()
                    or [move.acceptance_number]
                )
                if number
            )
        )

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity, reserved_quant)
        # Carry the number entered on the move over to its first operation.
        if self.acceptance_number and not self.move_line_ids._get_acceptance_numbers():
            vals["acceptance_number"] = self.acceptance_number
        return vals

    def _prepare_merge_moves_distinct_fields(self):
        return super()._prepare_merge_moves_distinct_fields() + ["acceptance_number"]
