# Copyright 2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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
    # When adding a new font, you add ("string for CSS", "display name")
    # The string for CSS can be checked with `fc-list | awk -F ":" '{print $2}'`
    font_family = fields.Selection(
        [("Arial", "Arial"), ("Calibri", "Calibri")],
        default="Arial",
        required=True,
        help="Font applied to the printed texts",
    )
    font_size = fields.Float(help="Size of the font (in cm)")
    line_height = fields.Float(
        "Line Spacing",
        help="Line spacing between the printed texts (in proportion to the font size)",
    )
    width_padding = fields.Float(
        "Width Padding (Dates)",
        help="Horizontal position of the texts from the left of the label (in cm)",
    )
    height_padding = fields.Float(
        "Height Padding (Dates)",
        help="Vertical position of the texts from the top of the label (in cm)",
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
    with_gs1_code = fields.Boolean("With GS1 Code")
    gs1_code_size = fields.Float(
        "GS1 Code Size", help="Size of the GS1 Data Matrix code (in cm)"
    )
    gs1_code_width_padding = fields.Float(
        "Width Padding (GS1)",
        help="Horizontal position of the GS1 Data Matrix code from the left of the "
        "label (in cm)",
    )
    gs1_code_height_padding = fields.Float(
        "Height Padding (GS1)",
        help="Vertical position of the GS1 Data Matrix code from the top of the label "
        "(in cm)",
    )
    coefficient = fields.Float(
        "Conversion Coefficient",
        compute="_compute_coefficient",
        help="The coefficient to convert the parameter values from 'cm' to 'mm' "
        "taking the dpi setting into account.",
    )

    def _compute_coefficient(self):
        for template in self:
            # TODO How was '0.1285' calculated?
            template.coefficient = template.paperformat_id.dpi * 0.1285

    def get_label_layout_css(self):
        self.ensure_one()
        # margin-top and margin-left will be given by report.paperformat
        css_list = [
            "display: inline-table",
            "margin-bottom: %smm" % str(self.label_height_margin * self.coefficient),
            "margin-right: %smm" % str(self.label_width_margin * self.coefficient),
        ]
        return ";".join(css_list)

    def get_label_css(self):
        self.ensure_one()
        css_list = [
            "position: relative",
            "background-image: url('%s')" % image_data_uri(self.label_image),
            "height: %smm" % str(self.label_height * self.coefficient),
            "width: %smm" % str(self.label_width * self.coefficient),
            "background-size: cover",
        ]
        return ";".join(css_list)

    def get_label_text_css(self):
        self.ensure_one()
        css_list = [
            "position: absolute",
            "font-family: %s" % self.font_family,
            "font-size: %smm" % str(self.font_size * self.coefficient),
            "line-height: %s" % self.line_height,
            "left: %smm" % str(self.width_padding * self.coefficient),
            "top: %smm" % str(self.height_padding * self.coefficient),
        ]
        return ";".join(css_list)

    def get_qr_code_css(self):
        self.ensure_one()
        css_list = [
            "position: absolute",
            "left: %smm" % str(self.qr_code_width_padding * self.coefficient),
            "top: %smm" % str(self.qr_code_height_padding * self.coefficient),
            "width: %smm" % str(self.qr_code_size * self.coefficient),
            "height: %smm" % str(self.qr_code_size * self.coefficient),
        ]
        return ";".join(css_list)

    def get_gs1_code_css(self):
        self.ensure_one()
        css_list = [
            "position: absolute",
            "left: %smm" % str(self.gs1_code_width_padding * self.coefficient),
            "top: %smm" % str(self.gs1_code_height_padding * self.coefficient),
            "width: %smm" % str(self.gs1_code_size * self.coefficient),
            "height: %smm" % str(self.gs1_code_size * self.coefficient),
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
