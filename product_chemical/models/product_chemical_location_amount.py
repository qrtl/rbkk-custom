# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductChemicalLocationAmount(models.Model):
    _name = "product.chemical.location.amount"
    _description = "Product Chemical Amount by Location"
    _auto = False
    _order = "product_tmpl_id, location_id, substance_id"
    _depends = {
        "product.template": ["is_chemical"],
        "product.product": ["product_tmpl_id"],
        "product.chemical.substance.line": [
            "product_tmpl_id",
            "substance_id",
            "content_rate",
        ],
        "product.chemical.substance": ["cas_no"],
        "stock.quant": ["product_id", "location_id", "quantity"],
        "stock.location": ["usage"],
    }

    product_tmpl_id = fields.Many2one(
        "product.template", string="Product", readonly=True
    )
    location_id = fields.Many2one(
        "stock.location", string="Location", readonly=True
    )
    substance_id = fields.Many2one(
        "product.chemical.substance", string="Substance", readonly=True
    )
    cas_no = fields.Char(string="CAS No.", readonly=True)
    quantity = fields.Float(string="On Hand Qty", readonly=True)
    content_rate = fields.Float(string="Content Rate (%)", readonly=True)
    component_amount = fields.Float(string="Component Amount", readonly=True)

    @property
    def _table_query(self):
        return """
            SELECT
                ROW_NUMBER() OVER () AS id,
                pt.id AS product_tmpl_id,
                sq.location_id AS location_id,
                sub_line.substance_id AS substance_id,
                sub.cas_no AS cas_no,
                SUM(sq.quantity) AS quantity,
                sub_line.content_rate AS content_rate,
                SUM(sq.quantity) * sub_line.content_rate / 100.0
                    AS component_amount
            FROM product_template pt
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            JOIN product_chemical_substance_line sub_line
                ON sub_line.product_tmpl_id = pt.id
            JOIN product_chemical_substance sub
                ON sub.id = sub_line.substance_id
            JOIN stock_quant sq ON sq.product_id = pp.id
            JOIN stock_location sl
                ON sl.id = sq.location_id AND sl.usage = 'internal'
            WHERE pt.is_chemical = TRUE
            GROUP BY
                pt.id,
                sq.location_id,
                sub_line.substance_id,
                sub.cas_no,
                sub_line.content_rate
        """
