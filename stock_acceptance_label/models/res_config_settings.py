# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import is_html_empty

from .stock_move import ARRIVAL_DATE_FIELD_PARAM, STATUS_HTML_PARAM


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

    # Read and written by hand rather than through config_parameter, which only
    # supports the simple field types.
    acceptance_label_status_html = fields.Html(
        string="Status Area",
        help="Status area printed on the acceptance label. It is meant to be "
        "filled in by hand, and can be edited freely as long as it stays within "
        "a few lines: the label has a fixed height, and anything that does not "
        "fit is cut off. Empty it to restore the built-in status area.",
    )

    @api.model
    def _default_acceptance_label_arrival_date_field_id(self):
        return self.env["stock.move"]._get_acceptance_arrival_date_field().id

    def get_values(self):
        res = super().get_values()
        # Show the status area that is actually printed, so that the built-in one
        # only has to be adjusted.
        res["acceptance_label_status_html"] = self.env[
            "stock.move"
        ].get_acceptance_status_html()
        return res

    def set_values(self):
        res = super().set_values()
        status_html = self.acceptance_label_status_html
        self.env["ir.config_parameter"].sudo().set_param(
            STATUS_HTML_PARAM, False if is_html_empty(status_html) else status_html
        )
        return res
