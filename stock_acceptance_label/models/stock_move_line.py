# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    acceptance_number = fields.Char(
        copy=False,
        help="Acceptance number of this detailed operation. It is the number "
        "printed on the label, and the one kept on the lot it is received in.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("acceptance_number") or not vals.get("move_id"):
                continue
            move = self.env["stock.move"].browse(vals["move_id"])
            # Carry the number entered on the transfer line over to its first
            # detailed operation: the operations are where the number is read
            # back from, and they are only created once the line is reserved.
            # Once one of them carries a number, the number of the transfer
            # line is their summary and must not be pushed back down.
            if (
                move.acceptance_number
                and not move.move_line_ids._get_acceptance_numbers()
            ):
                vals["acceptance_number"] = move.acceptance_number
        return super().create(vals_list)

    def _get_acceptance_numbers(self):
        """Return the acceptance numbers of the operations.

        Blanks are dropped and repeats are kept once, in the order of the
        operations, so that the result reads as a summary.
        """
        numbers = []
        for line in self:
            if line.acceptance_number and line.acceptance_number not in numbers:
                numbers.append(line.acceptance_number)
        return numbers
