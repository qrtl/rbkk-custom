# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductTemplateChemicalSubstanceLine(models.Model):
    _name = "product.template.chemical.substance.line"
    _description = "Product Chemical Substance Line"

    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product",
        required=True,
        ondelete="cascade",
        index=True,
    )
    substance_id = fields.Many2one(
        "product.chemical.substance", required=True, ondelete="restrict"
    )
    cas_no = fields.Char(related="substance_id.cas_no", store=True, string="CAS No.")
    content_rate = fields.Float(
        string="Content Rate (%)",
        default=0.0,
    )

    _sql_constraints = [
        (
            "product_substance_uniq",
            "unique(product_tmpl_id, substance_id)",
            "Each substance can be added only once per product.",
        ),
        (
            "content_rate_range",
            "CHECK(content_rate >= 0 AND content_rate <= 100)",
            "Content rate must be between 0 and 100.",
        ),
    ]
