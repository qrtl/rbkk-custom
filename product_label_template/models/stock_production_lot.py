# Copyright 2019-2021 Quartile Limited

import base64
from io import BytesIO

import treepoem

from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    gs1_string = fields.Char("GS1 String", compute="_compute_gs1_string", store=True)
    gs1_image = fields.Binary(
        "GS1 Image", compute="_compute_gs1_image", store=True, attachment=True
    )

    @api.depends("product_id.barcode", "ref", "date_produced", "expiry_date")
    def _compute_gs1_string(self):
        """See 2-2 GS1-element-strings (under #2-Encoding-data) in following document.
        https://www.gs1.org/standards/gs1-datamatrix-guideline/25
        """
        for rec in self:
            if all(
                [rec.product_id.barcode, rec.ref, rec.date_produced, rec.expiry_date]
            ):
                rec.gs1_string = (
                    "(01)%s" % rec.product_id.barcode
                    + "(10)%s" % rec.ref
                    + "(11)%s" % str(rec.date_produced)
                    + "(17)%s" % str(rec.expiry_date)
                )

    @api.depends("gs1_string")
    def _compute_gs1_image(self):
        for rec in self:
            if rec.gs1_string:
                image = treepoem.generate_barcode(
                    barcode_type="datamatrix", data=rec.gs1_string
                ).convert(
                    "1"
                )  # .convert("1") means monochrome output.
                # Buffer the value with BytesIO() and get the image string from there.
                # Keeping PIL image itself in the binary field doesn't let Odoo render
                # the image when it's called in printing.
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                rec.gs1_image = base64.b64encode(buffered.getvalue())
