# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import format_date


class StockMove(models.Model):
    _inherit = "stock.move"

    acceptance_number = fields.Char(copy=False)

    def _prepare_merge_moves_distinct_fields(self):
        # Keep one label, and one acceptance number, per numbered line.
        return super()._prepare_merge_moves_distinct_fields() + ["acceptance_number"]

    def get_acceptance_arrival_date(self):
        """Return the configured arrival date, in the user time zone."""
        self.ensure_one()
        field = self.company_id._get_acceptance_arrival_date_field()
        if field.model == "stock.move":
            record = self
        elif field.model == "stock.picking":
            record = self.picking_id
        else:
            return False
        value = record[field.name] if record else False
        if not value:
            return False
        if field.ttype == "datetime":
            return fields.Datetime.context_timestamp(self, value).date()
        return value

    def _get_acceptance_lots(self):
        """Return the lots the transfer line is received in, if any."""
        self.ensure_one()
        return self.lot_ids

    def get_acceptance_lot_names(self):
        """Return the lot numbers of the transfer line, as a single string."""
        return ", ".join(self._get_acceptance_lots().mapped("name"))

    def get_acceptance_expiration_dates(self):
        """Keep one date per lot, in lot order, including duplicates and blanks."""
        return ", ".join(
            format_date(
                self.env,
                fields.Datetime.context_timestamp(self, lot.expiration_date).date(),
                date_format="yyyy/MM/dd",
            )
            if lot.expiration_date
            else ""
            for lot in self._get_acceptance_lots()
        )

    def get_acceptance_status_html(self):
        """Return the status area configured for the transfer's company."""
        self.ensure_one()
        return self.company_id._get_acceptance_status_html()
