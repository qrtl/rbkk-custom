# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductChemicalLaw(models.Model):
    _name = "product.chemical.law"
    _description = "Chemical Law"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    note = fields.Text()
    major_category_ids = fields.One2many(
        "product.chemical.law.major.category",
        "law_id",
        string="Major Categories",
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Law name must be unique."),
    ]
