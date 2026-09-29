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
            # Only the detailed operations are summarized, so the number
            # entered before they exist survives: it is carried over to the
            # first one created, which gives back the same summary.
            move.acceptance_number = ", ".join(
                move.move_line_ids._get_acceptance_numbers()
            )

    def _inverse_acceptance_number(self):
        for move in self:
            # A number entered on the line applies to its detailed operations,
            # which is where it is read back from. A tracked product is
            # numbered per lot, so its operations are left alone.
            if move.has_tracking != "none":
                continue
            move.move_line_ids.acceptance_number = move.acceptance_number

    def _get_acceptance_numbers(self):
        """Return the acceptance numbers of the lines, as a summary.

        The numbers of the detailed operations are used, falling back on the
        number of the line itself as long as it has no operation to read.
        """
        numbers = []
        for move in self:
            own = move.move_line_ids._get_acceptance_numbers() or [
                move.acceptance_number
            ]
            for number in own:
                if number and number not in numbers:
                    numbers.append(number)
        return numbers

    def _prepare_merge_moves_distinct_fields(self):
        # Keep one label, and one acceptance number, per numbered line.
        return super()._prepare_merge_moves_distinct_fields() + ["acceptance_number"]
