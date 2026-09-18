# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import format_date


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
