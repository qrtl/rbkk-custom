# Copyright 2021 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import io

from PIL import Image

from odoo import api, fields, models
from odoo.tools.image import image_data_uri


class ProductLabelTemplate(models.Model):
    _name = "product.label.template"
    _rec_name = "product_id"
    _description = "Product Label Template"

    product_id = fields.Many2one("product.product", required=True)
    product_template_attribute_value_ids = fields.Many2many(
        related="product_id.product_template_attribute_value_ids"
    )
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id", store=True)
    paperformat_id = fields.Many2one(
        "report.paperformat",
        "Paper Format",
        required=True,
        help="Paper format used to print the PDF with",
    )
    label_image = fields.Binary(attachment=True)
    label_width = fields.Float(help="Width of the printed label image (in cm)")
    label_height = fields.Float(help="Height of the printed label image (in cm)")
    label_ratio = fields.Float()
    label_width_margin = fields.Float(
        help="Margin on the right side of the label (in cm)"
    )
    label_height_margin = fields.Float(help="Margin at the bottom of the label (in cm)")
    font_size = fields.Float(help="Size of the font (in cm)")
    width_padding_lot = fields.Float(
        "Width Padding (Lot)",
        help="Horizontal position of the lot from the left of the label (in cm)",
    )
    height_padding_lot = fields.Float(
        "Height Padding (Lot)",
        help="Vertical position of the lot from the top of the label (in cm)",
    )
    with_qr_code = fields.Boolean("With QR Code")
    qr_code_size = fields.Float("QR Code Size", help="Size of the QR code (in cm)")
    qr_code_width_padding = fields.Float(
        "Width Padding (QR)",
        help="Horizontal position of the QR code from the left of the label (in cm)",
    )
    qr_code_height_padding = fields.Float(
        "Height Padding (QR)",
        help="Vertical position of the QR code from the top of the label (in cm)",
    )
    with_barcode = fields.Boolean()
    barcode_width = fields.Float(help="Width of the printed barcode (in cm)")
    barcode_height = fields.Float(help="Height of the printed barcode (in cm)")
    barcode_width_padding = fields.Float(
        "Width Padding (Barcode)",
        help="Horizontal position of the barcode from the left of the label (in cm)",
    )
    barcode_height_padding = fields.Float(
        "Height Padding (Barcode)",
        help="Vertical position of the barcode from the top of the label (in cm)",
    )
    coefficient = fields.Float(
        "Conversion Coefficient",
        default=38.55,
        help="The coefficient to convert the parameter values from 'cm' to 'mm' "
        "taking the dpi setting into account.",
    )

    def get_label_layout_css(self, field_name):
        self.ensure_one()
        width_margin_field = getattr(self, f"{field_name}_width_margin")
        height_margin_field = getattr(self, f"{field_name}_height_margin")
        # margin-top and margin-left will be given by report.paperformat
        css_list = [
            "display: inline-table",
            f"margin-bottom: {height_margin_field * self.coefficient}mm",
            f"margin-right: {width_margin_field * self.coefficient}mm",
        ]
        return ";".join(css_list)

    def get_label_css(self):
        self.ensure_one()
        css_list = [
            "position: relative",
            f"background-image: url('{image_data_uri(self.label_image or b'')}')",
            f"height: {self.label_height * self.coefficient}mm",
            f"width: {self.label_width * self.coefficient}mm",
            "background-size: cover",
        ]
        return ";".join(css_list)

    def get_label_text_css(self, field_name):
        self.ensure_one()
        width_padding_field = getattr(self, f"width_padding_{field_name}")
        height_padding_field = getattr(self, f"height_padding_{field_name}")
        css_list = [
            "position: absolute",
            "font-family: Arial",
            f"font-size: {self.font_size * self.coefficient}mm",
            f"left: {width_padding_field * self.coefficient}mm",
            f"top: {height_padding_field * self.coefficient}mm",
        ]
        return ";".join(css_list)

    def get_qr_code_css(self):
        self.ensure_one()
        css_list = [
            "position: absolute",
            f"left: {self.qr_code_width_padding * self.coefficient}mm",
            f"top: {self.qr_code_height_padding * self.coefficient}mm",
            f"width: {self.qr_code_size * self.coefficient}mm",
            f"height: {self.qr_code_size * self.coefficient}mm",
        ]
        return ";".join(css_list)

    def get_barcode_css(self):
        self.ensure_one()
        css_list = [
            "position: absolute",
            f"left: {self.barcode_width_padding * self.coefficient}mm",
            f"top: {self.barcode_height_padding * self.coefficient}mm",
            f"width: {self.barcode_width * self.coefficient}mm",
            f"height: {self.barcode_height * self.coefficient}mm",
        ]
        return ";".join(css_list)

    @api.onchange("label_image")
    def _onchange_label_image(self):
        if self.label_image:
            # Borrowing logic from odoo image tool
            # https://github.com/odoo/odoo/blob/4e2d0b97f3ec0491294301a5a6b05086e158dea8/odoo/tools/image.py#L68-L69 # noqa
            image_stream = io.BytesIO(base64.b64decode(self.label_image))
            image = Image.open(image_stream)
            self.label_width = image.size[0]
            self.label_height = image.size[1]
            self.label_ratio = image.size[0] / image.size[1]

    @api.onchange("label_width")
    def _onchange_label_width(self):
        if self.label_width and self.label_ratio:
            self.label_height = self.label_width / self.label_ratio

    @api.onchange("label_height")
    def _onchange_label_height(self):
        if self.label_height and self.label_ratio:
            self.label_width = self.label_height * self.label_ratio
