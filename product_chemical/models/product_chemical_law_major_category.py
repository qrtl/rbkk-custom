# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductChemicalLawMajorCategory(models.Model):
    _name = "product.chemical.law.major.category"
    _description = "Chemical Law Major Category"
    _order = "law_id, sequence, name"

    name = fields.Char(required=True, translate=True)
    law_id = fields.Many2one(
        "product.chemical.law", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    minor_category_ids = fields.One2many(
        "product.chemical.law.minor.category",
        "major_category_id",
        string="Minor Categories",
    )

    _sql_constraints = [
        (
            "name_law_uniq",
            "unique(law_id, name)",
            "Major category name must be unique per law.",
        ),
    ]
