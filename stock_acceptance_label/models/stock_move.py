# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import format_date, html_sanitize

ARRIVAL_DATE_FIELD_PARAM = "stock_acceptance_label.arrival_date_field_id"
STATUS_HTML_PARAM = "stock_acceptance_label.status_html"
# The label is a form to be filled in by hand on the shop floor, so its dates
# are printed in a fixed format instead of the format of the language.
LABEL_DATE_FORMAT = "yyyy/MM/dd"


class StockMove(models.Model):
    _inherit = "stock.move"

    acceptance_number = fields.Char(copy=False)

    @api.model
    def _get_acceptance_arrival_date_field(self):
        """Return the field to print as the arrival date of the label.

        The field is selected in the inventory settings. The effective date of
        the transfer is used when the setting is empty or points to a field
        that does not exist anymore.
        """
        ir_model_fields = self.env["ir.model.fields"].sudo()
        param = (
            self.env["ir.config_parameter"].sudo().get_param(ARRIVAL_DATE_FIELD_PARAM)
        )
        field = (
            ir_model_fields.browse(int(param))
            if param and str(param).isdigit()
            else ir_model_fields
        )
        return field.exists() or ir_model_fields._get("stock.picking", "date_done")

    def get_acceptance_arrival_date(self):
        """Return the configured arrival date, in the user time zone."""
        self.ensure_one()
        field = self._get_acceptance_arrival_date_field()
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
        lot of the line is unknown.
        """
        dates = {
            fields.Datetime.context_timestamp(self, expiration_date).date()
            for expiration_date in self._get_acceptance_lots().mapped("expiration_date")
            if expiration_date
        }
        return ", ".join(
            format_date(self.env, date, date_format=LABEL_DATE_FORMAT)
            for date in sorted(dates)
        )

    @api.model
    def _get_default_acceptance_status_html(self):
        """Return the built-in status area, in the language of the user."""
        return self.env["ir.qweb"]._render(
            "stock_acceptance_label.acceptance_label_status"
        )

    @api.model
    def get_acceptance_status_html(self):
        """Return the status area of the label, as set in the inventory settings.

        The value is sanitized on printing as well as on saving the settings, so
        that the report cannot be made to run scripts through the underlying
        system parameter.
        """
        status_html = (
            self.env["ir.config_parameter"].sudo().get_param(STATUS_HTML_PARAM)
        )
        if not status_html:
            return self._get_default_acceptance_status_html()
        return html_sanitize(status_html)
