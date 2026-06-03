# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductChemicalMinorCategory(models.Model):
    _name = "product.chemical.minor.category"
    _description = "Chemical Minor Category"
    _order = "major_category_id, sequence, name"

    name = fields.Char(required=True, translate=True)
    major_category_id = fields.Many2one(
        "product.chemical.major.category",
        required=True,
        ondelete="cascade",
        index=True,
    )
    law_id = fields.Many2one(
        related="major_category_id.law_id", store=True, index=True
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "name_major_uniq",
            "unique(major_category_id, name)",
            "Minor category name must be unique per major category.",
        ),
    ]
