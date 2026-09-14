# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import format_date

# The label is a form to be filled in by hand on the shop floor, so its dates
# are printed in a fixed format instead of the format of the language.
LABEL_DATE_FORMAT = "yyyy/MM/dd"


class StockMove(models.Model):
    _inherit = "stock.move"

    acceptance_number = fields.Char(copy=False)

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
        return self.move_line_ids.lot_id

    def get_acceptance_lot_names(self):
        """Return the lot numbers of the transfer line, as a single string."""
        return ", ".join(self._get_acceptance_lots().mapped("name"))

    def get_acceptance_expiration_dates(self):
        """Return the expiration dates of the lots, as a single string.

        The dates come from the lots, so that nothing is printed as long as the
        lot of the line is unknown. Keep one entry per lot, in the same order as
        the lot numbers, including duplicate dates and empty entries.
        """
        return ", ".join(
            format_date(
                self.env,
                fields.Datetime.context_timestamp(self, lot.expiration_date).date(),
                date_format=LABEL_DATE_FORMAT,
            )
            if lot.expiration_date
            else ""
            for lot in self._get_acceptance_lots()
        )

    def get_acceptance_status_html(self):
        """Return the status area configured for the transfer's company."""
        self.ensure_one()
        return self.company_id._get_acceptance_status_html()
