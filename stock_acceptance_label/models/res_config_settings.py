# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import is_html_empty


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    acceptance_label_arrival_date_field_id = fields.Many2one(
        related="company_id.acceptance_label_arrival_date_field_id",
        readonly=False,
    )

    acceptance_label_status_html = fields.Html(
        related="company_id.acceptance_label_status_html",
        readonly=False,
    )

    @api.onchange("company_id")
    def _onchange_company_id_acceptance_label(self):
        if self.company_id and is_html_empty(self.acceptance_label_status_html):
            self.acceptance_label_status_html = (
                self.company_id._get_acceptance_status_html()
            )
