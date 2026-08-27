# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    chemical_amount_ids = fields.One2many(
        "product.chemical.move.amount", "move_id", string="Chemical Amounts"
    )

    def _is_chemical_consumption_issue(self):
        self.ensure_one()
        return (
            self.location_id.usage == "internal"
            and self.location_dest_id.usage == "internal"
            and not self.location_id.is_chemical_consumption_location
            and self.location_dest_id.is_chemical_consumption_location
        )

    def _is_chemical_consumption_receipt(self):
        self.ensure_one()
        return (
            self.location_id.usage == "internal"
            and self.location_dest_id.usage == "internal"
            and self.location_id.is_chemical_consumption_location
            and not self.location_dest_id.is_chemical_consumption_location
        )

    def _get_chemical_amount_sign(self):
        """Return the sign the moved amount has to be recorded with.

        Only moves between a regular internal location and a chemical
        consumption location are tracked. A move into the consumption location
        is treated as a consumption and recorded as negative; the reverse move
        restores stock and is recorded as positive.
        """
        self.ensure_one()
        if self._is_chemical_consumption_receipt():
            return 1
        if self._is_chemical_consumption_issue():
            return -1
        return 0

    def _is_chemical_amount_move(self):
        """Return whether the move has to be recorded as a chemical movement."""
        self.ensure_one()
        if self.state != "done" or not self.product_id.track_chemical_consumption:
            return False
        if float_is_zero(self.quantity, precision_rounding=self.product_uom.rounding):
            return False
        return (
            self._is_chemical_consumption_issue()
            or self._is_chemical_consumption_receipt()
        )

    def _create_chemical_amounts(self):
        vals_list = []
        for move in self:
            if move.chemical_amount_ids or not move._is_chemical_amount_move():
                continue
            vals_list += [
                {"move_id": move.id, "substance_id": line.substance_id.id}
                for line in move.product_id.chemical_substance_line_ids
            ]
        return self.env["product.chemical.move.amount"].create(vals_list)

    def action_sync_chemical_amounts(self):
        """Rebuild the chemical amounts of the moves from the current composition.

        The records are replaced rather than recomputed, so that a substance
        added to (or removed from) the product after the move was validated is
        reflected as well. Manual corrections made on the replaced records are
        lost, which is the point of the operation.
        """
        self.chemical_amount_ids.unlink()
        amounts = self._create_chemical_amounts()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._(
                    "%(count)s chemical movement(s) recorded.", count=len(amounts)
                ),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _action_done(self, cancel_backorder=False):
        moves_done = super()._action_done(cancel_backorder=cancel_backorder)
        moves_done.sudo()._create_chemical_amounts()
        return moves_done
