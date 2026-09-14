# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import html_sanitize, is_html_empty


class ResCompany(models.Model):
    _inherit = "res.company"

    acceptance_label_arrival_date_field_id = fields.Many2one(
        "ir.model.fields",
        string="Arrival Date Field",
        domain=[
            ("model", "in", ["stock.move", "stock.picking"]),
            ("ttype", "in", ["date", "datetime"]),
        ],
        default=lambda self: self.env["ir.model.fields"]._get(
            "stock.picking", "date_done"
        ),
        ondelete="set null",
        help="Field printed as the arrival date on the acceptance label. Date "
        "fields of the transfer and of its lines can be selected, and datetime "
        "fields are converted to the user time zone. The effective date of the "
        "transfer is used when this is left empty.",
    )
    acceptance_label_status_html = fields.Html(
        string="Status Area",
        help="Status area printed on the acceptance label. It is meant to be "
        "filled in by hand, and can be edited freely as long as it stays within "
        "a few lines: the label has a fixed height, and anything that does not "
        "fit is cut off. Empty it to restore the built-in status area.",
    )

    def _get_acceptance_arrival_date_field(self):
        self.ensure_one()
        return self.acceptance_label_arrival_date_field_id or self.env[
            "ir.model.fields"
        ]._get("stock.picking", "date_done")

    def _get_acceptance_status_html(self):
        self.ensure_one()
        if is_html_empty(self.acceptance_label_status_html):
            return self.env["ir.qweb"]._render(
                "stock_acceptance_label.acceptance_label_status"
            )
        return html_sanitize(self.acceptance_label_status_html)
