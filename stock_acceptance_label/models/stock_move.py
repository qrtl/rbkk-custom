# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    acceptance_number = fields.Char(copy=False)

    def get_acceptance_arrival_date(self):
        """Return the effective date of the transfer, in the user time zone."""
        self.ensure_one()
        date_done = self.picking_id.date_done
        if not date_done:
            return False
        return fields.Datetime.context_timestamp(self, date_done).date()
