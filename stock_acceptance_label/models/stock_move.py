# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

ARRIVAL_DATE_FIELD_PARAM = "stock_acceptance_label.arrival_date_field_id"


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
