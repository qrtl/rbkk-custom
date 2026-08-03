# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .stock_move import ARRIVAL_DATE_FIELD_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    acceptance_label_arrival_date_field_id = fields.Many2one(
        "ir.model.fields",
        string="Arrival Date Field",
        domain=[
            ("model", "in", ["stock.move", "stock.picking"]),
            ("ttype", "in", ["date", "datetime"]),
        ],
        default=lambda self: self._default_acceptance_label_arrival_date_field_id(),
        config_parameter=ARRIVAL_DATE_FIELD_PARAM,
        help="Field printed as the arrival date on the acceptance label. Date "
        "fields of the transfer and of its lines can be selected, and datetime "
        "fields are converted to the user time zone. The effective date of the "
        "transfer is used when this is left empty.",
    )

    @api.model
    def _default_acceptance_label_arrival_date_field_id(self):
        return self.env["stock.move"]._get_acceptance_arrival_date_field().id
