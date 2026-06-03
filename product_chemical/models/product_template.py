# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_chemical = fields.Boolean(string="Chemical")
    chemical_law_line_ids = fields.One2many(
        "product.chemical.law.line", "product_tmpl_id", string="Laws"
    )
    chemical_substance_line_ids = fields.One2many(
        "product.chemical.substance.line",
        "product_tmpl_id",
        string="Chemical Substances",
    )
    chemical_substance_ids = fields.Many2many(
        "product.chemical.substance",
        compute="_compute_chemical_substance_ids",
        search="_search_chemical_substance_ids",
        string="Substances",
    )
    risk_assessment_pdf = fields.Binary(string="Risk Assessment Sheet")
    risk_assessment_pdf_filename = fields.Char(
        string="Risk Assessment Sheet Filename"
    )
    chemical_location_amount_ids = fields.One2many(
        "product.chemical.location.amount",
        "product_tmpl_id",
        string="Component Amount by Location",
        readonly=True,
    )

    @api.depends("chemical_substance_line_ids.substance_id")
    def _compute_chemical_substance_ids(self):
        for rec in self:
            rec.chemical_substance_ids = rec.chemical_substance_line_ids.substance_id

    def _search_chemical_substance_ids(self, operator, value):
        lines = self.env["product.chemical.substance.line"].search(
            [("substance_id", operator, value)]
        )
        return [("id", "in", lines.product_tmpl_id.ids)]
