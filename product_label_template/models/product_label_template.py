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
    attribute_value_ids = fields.Many2many(related="product_id.attribute_value_ids")
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id", store=True)
    paperformat_id = fields.Many2one(
        "report.paperformat",
        "Paper Format",
        required=True,
        help="Paper format used to print the PDF with",
    )
    qr_paperformat_id = fields.Many2one(
        "report.paperformat",
        "Paper Format (QR)",
        help="Paper format used to print only QR codes.",
    )
    label_image = fields.Binary(attachment=True)
    label_width = fields.Float(help="Width of the printed label image (in cm)")
    label_height = fields.Float(help="Height of the printed label image (in cm)")
    label_ratio = fields.Float()
    label_width_margin = fields.Float(
        help="Margin on the right side of the label (in cm)"
    )
    label_height_margin = fields.Float(help="Margin at the bottom of the label (in cm)")

    """
    NOTE: parameter of font_family has used to select font,
    but latest requirement is limited to Arial font.
    Codes below would be a good example to use this function again.
    # When adding a new font, you add ("string for CSS", "display name")
    # The string for CSS can be checked with `fc-list | awk -F ":" '{print $2}'`
    font_family = fields.Selection(
        [("Arial", "Arial"), ("Calibri", "Calibri")],
        default="Arial",
        required=True,
        help="Font applied to the printed texts",
    )
    """
    font_size = fields.Float(help="Size of the font (in cm)")
    width_padding_lot = fields.Float(
        "Width Padding (Lot)",
        oldname="width_padding",
        help="Horizontal position of the lot from the left of the label (in cm)",
    )
    height_padding_lot = fields.Float(
        "Height Padding (Lot)",
        oldname="height_padding",
        help="Vertical position of the lot from the top of the label (in cm)",
    )
    # some products do not need to show production date on label.
    with_prod_date = fields.Boolean("With production date")
    width_padding_production_date = fields.Float(
        "Width Padding (Prod. Date)",
        help="Horizontal position of the prod. date from the left of the label (in cm)",
    )
    height_padding_production_date = fields.Float(
        "Height Padding (Prod. Date)",
        help="Vertical position of the prod. date from the top of the label (in cm)",
    )
    width_padding_expiry_date = fields.Float(
        "Width Padding (Exp. Date)",
        help="Horizontal position of the exp. date from the left of the label (in cm)",
    )
    height_padding_expiry_date = fields.Float(
        "Height Padding (Exp. Date)",
        help="Vertical position of the exp. date from the top of the label (in cm)",
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

    with_individual_qr_code = fields.Boolean("With Individual QR Code")
    qr_code_width_margin = fields.Float(
        help="Horizontal margin between the QR codes (in cm)"
    )
    qr_code_height_margin = fields.Float(
        help="Vertical margin between the QR codes (in cm)"
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
        # compute="_compute_coefficient",
        default=38.55,
        help="The coefficient to convert the parameter values from 'cm' to 'mm' "
        "taking the dpi setting into account.",
    )

    """
    NOTE: dpi * 0.1285 is good value in dev. env., but it is not so in other servers.
    # 13.37 under 300 dpi was reported by one whose env. is MS windows and chrome.
    # 38.55 under 300 dpi and 12.7 under 100 dpi was by Macintosh user.
    def _compute_coefficient(self):
        for template in self:
            # '0.1285' was decided by updating label width moderately to paper size
            # (wide=210mm) under left and right margins are 0 mm on dev. env. of qrtl.
            template.coefficient = template.paperformat_id.dpi * 0.1285
    """

    def get_label_layout_css(self, field_name):
        self.ensure_one()
        width_margin_field = getattr(self, "%s_width_margin" % field_name)
        height_margin_field = getattr(self, "%s_height_margin" % field_name)
        # margin-top and margin-left will be given by report.paperformat
        css_list = [
            "display: inline-table",
            "margin-bottom: %smm" % str(height_margin_field * self.coefficient),
            "margin-right: %smm" % str(width_margin_field * self.coefficient),
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

    def get_label_text_css(self, field_name):
        self.ensure_one()
        width_padding_field = getattr(self, "width_padding_%s" % field_name)
        height_padding_field = getattr(self, "height_padding_%s" % field_name)
        css_list = [
            "position: absolute",
            "font-family: Arial",
            "font-size: %smm" % str(self.font_size * self.coefficient),
            "left: %smm" % str(width_padding_field * self.coefficient),
            "top: %smm" % str(height_padding_field * self.coefficient),
        ]
        return ";".join(css_list)

    def get_qr_code_css(self, qr_only=False):
        self.ensure_one()
        css_list = [
            # When qr_only is true, there is no parent element and in that case
            # 'relative' should be applied for the position attribute to avoid the
            # overlap of the images.
            "position: %s" % ("relative" if qr_only else "absolute"),
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
