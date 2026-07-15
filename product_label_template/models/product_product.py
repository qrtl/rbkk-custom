# Copyright 2021 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_label_template_ids = fields.One2many(
        "product.label.template", "product_id", "Product Label Template"
    )
