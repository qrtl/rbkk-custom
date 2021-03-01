# Copyright 2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import io

from PIL import Image

from odoo import api, fields, models
from odoo.tools.image import image_data_uri


class ProductLabelTemplate(models.Model):
    _name = "product.label.template"

    product_label_type_id = fields.Many2one("product.label.type", required=True)
    product_id = fields.Many2one("product.product", required=True)
    label_image = fields.Binary(string="Product Label", attachment=True,)
    label_width = fields.Float(
        "Label Width", compute="_compute_label_size", store=True, readonly=False
    )
    label_height = fields.Float(
        "Label Height", compute="_compute_label_size", store=True, readonly=False
    )
    font_family = fields.Char("Font Family")
    font_size = fields.Float("Font Size")
    line_height = fields.Float("Line Spacing")
    width_padding = fields.Float("Width Padding (Text)")
    height_padding = fields.Float("Height Padding (Text)")
    with_qr_code = fields.Boolean("With QR Code")
    qr_code_size = fields.Integer("QR Code Size")
    qr_code_width_padding = fields.Float("Width Padding (QR Code)")
    qr_code_height_padding = fields.Float("Height Padding (QR Code)")

    def get_label_css(self):
        css_list = [
            "position: relative",
            "background-image: url('%s')" % image_data_uri(self.label_image),
            "height: %spx" % self.label_height,
            "width: %spx" % self.label_width,
            "background-size: cover",
        ]
        return ";".join(css_list)

    def get_label_text_css(self):
        css_list = ["position: absolute"]
        if self.font_family:
            css_list.append("font-family: %s" % self.font_family)
        if self.font_size:
            css_list.append("font-size: %spx" % self.font_size)
        if self.line_height:
            css_list.append("line-height: %s" % self.line_height)
        if self.width_padding:
            css_list.append("left: %spx" % self.width_padding)
        if self.height_padding:
            css_list.append("top: %spx" % self.height_padding)
        return ";".join(css_list)

    def get_qr_code_css(self):
        css_list = ["position: absolute"]
        if self.qr_code_width_padding:
            css_list.append("left: %spx" % self.width_padding)
        if self.qr_code_height_padding:
            css_list.append("top: %spx" % self.height_padding)
        return ";".join(css_list)

    @api.multi
    @api.depends("label_image")
    def _compute_label_size(self):
        for template in self:
            if template.label_image:
                # Borrowing logic from odoo image tool
                # https://github.com/odoo/odoo/blob/4e2d0b97f3ec0491294301a5a6b05086e158dea8/odoo/tools/image.py#L68-L69 # noqa
                image_stream = io.BytesIO(base64.b64decode(template.label_image))
                image = Image.open(image_stream)
                template.label_width = image.size[0]
                template.label_height = image.size[1]
