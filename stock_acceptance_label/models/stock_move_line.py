# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def get_acceptance_arrival_date(self):
        self.ensure_one()
        field = self.company_id._get_acceptance_arrival_date_field()
        if field.model == "stock.move":
            record = self.move_id
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

    def get_acceptance_expiration_date(self):
        self.ensure_one()
        if not self.lot_id.expiration_date:
            return False
        return fields.Datetime.context_timestamp(
            self, self.lot_id.expiration_date
        ).date()
