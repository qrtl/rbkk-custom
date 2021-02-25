# Copyright 2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_label_template_ids = fields.One2many(
        "product.label.template", "product_id", "Product Label Template"
    )
