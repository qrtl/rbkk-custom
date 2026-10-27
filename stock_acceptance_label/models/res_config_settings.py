# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


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
