# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    chemical_consumption_ids = fields.One2many(
        "product.chemical.consumption", "move_id", string="Chemical Consumption"
    )

    def _get_chemical_consumption_sign(self):
        """Return the sign the moved amount has to be recorded with.

        The records measure how much of the substance was used up, not how the
        stock varied: issuing the goods out of an internal location into a
        chemical consumption location is a consumption and is recorded as
        positive, and the reverse move returns them to the stock and is
        recorded as negative, cancelling that consumption. The consumption
        location is usually a virtual one (a production location, or an
        inventory adjustment location standing for a scrapping or a
        non-manufacturing issue), so only its counterpart is required to be
        internal. Any other move returns 0, i.e. is not recorded at all.
        """
        self.ensure_one()
        source, dest = self.location_id, self.location_dest_id
        from_consumption = source.is_chemical_consumption_location
        to_consumption = dest.is_chemical_consumption_location
        if from_consumption == to_consumption:
            return 0
        if to_consumption:
            return 1 if source.usage == "internal" else 0
        return -1 if dest.usage == "internal" else 0

    def _is_chemical_consumption_move(self):
        """Return whether the move has to be recorded as a chemical consumption."""
        self.ensure_one()
        product = self.product_id
        if self.state != "done":
            return False
        if not product.is_chemical or not product.track_chemical_consumption:
            return False
        if float_is_zero(self.quantity, precision_rounding=self.product_uom.rounding):
            return False
        return bool(self._get_chemical_consumption_sign())

    def _create_chemical_consumption(self):
        vals_list = []
        for move in self:
            if (
                move.chemical_consumption_ids
                or not move._is_chemical_consumption_move()
            ):
                continue
            vals_list += [
                {"move_id": move.id, "substance_id": line.substance_id.id}
                for line in move.product_id.chemical_substance_line_ids
            ]
        return self.env["product.chemical.consumption"].create(vals_list)

    def action_sync_chemical_consumption(self):
        """Rebuild the chemical consumption of the moves from the current composition.

        The records are replaced rather than recomputed, so that a substance
        added to (or removed from) the product after the move was validated is
        reflected as well. Manual corrections made on the replaced records are
        lost, which is the point of the operation.
        """
        self.chemical_consumption_ids.unlink()
        amounts = self._create_chemical_consumption()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._(
                    "%(count)s chemical consumption record(s) created.",
                    count=len(amounts),
                ),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _action_done(self, cancel_backorder=False):
        moves_done = super()._action_done(cancel_backorder=cancel_backorder)
        moves_done.sudo()._create_chemical_consumption()
        return moves_done
