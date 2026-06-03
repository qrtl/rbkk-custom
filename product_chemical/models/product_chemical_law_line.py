# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductChemicalLawLine(models.Model):
    _name = "product.chemical.law.line"
    _description = "Product Chemical Law"

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    law_id = fields.Many2one(
        "product.chemical.law", required=True, ondelete="restrict"
    )
    major_category_id = fields.Many2one(
        "product.chemical.major.category",
        domain="[('law_id', '=', law_id)]",
        ondelete="restrict",
    )
    minor_category_id = fields.Many2one(
        "product.chemical.minor.category",
        domain="[('major_category_id', '=', major_category_id)]",
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "product_law_uniq",
            "unique(product_tmpl_id, law_id)",
            "Each law can be added only once per product.",
        ),
    ]

    @api.onchange("law_id")
    def _onchange_law_id(self):
        self.major_category_id = False
        self.minor_category_id = False

    @api.onchange("major_category_id")
    def _onchange_major_category_id(self):
        self.minor_category_id = False
