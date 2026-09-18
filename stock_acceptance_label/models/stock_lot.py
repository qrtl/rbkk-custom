# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    acceptance_move_line_ids = fields.One2many(
        "stock.move.line",
        "lot_id",
        string="Acceptance Operations",
        help="Detailed operations the lot appears in, which the acceptance "
        "numbers of the lot are read from.",
    )
    acceptance_number = fields.Char(
        compute="_compute_acceptance_number",
        store=True,
        help="Acceptance numbers the lot was received under. A lot received "
        "several times carries them all, separated by commas.",
    )

    @api.depends(
        "acceptance_move_line_ids.acceptance_number",
        "acceptance_move_line_ids.state",
    )
    def _compute_acceptance_number(self):
        # Kept computed rather than appended to on receipt, so that a number
        # corrected or a receipt cancelled after the fact drops out instead of
        # staying on the lot for good.
        for lot in self:
            lines = lot.acceptance_move_line_ids.filtered(
                lambda line: line.state != "cancel"
            )
            lot.acceptance_number = ", ".join(lines._get_acceptance_numbers())
