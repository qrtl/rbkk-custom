# Copyright 2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductLabelType(models.Model):
    _name = "product.label.type"

    name = fields.Char("Label Type")
