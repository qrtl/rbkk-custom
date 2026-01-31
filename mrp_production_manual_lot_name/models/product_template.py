# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mrp_manual_lot_name = fields.Boolean(
        string="Manual Lot Name in Manufacturing",
        help="If enabled, allows manual entry of lot/serial number name "
        "when creating manufacturing orders.",
    )
