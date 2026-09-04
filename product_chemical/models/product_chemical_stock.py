# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductChemicalStock(models.Model):
    _name = "product.chemical.stock"
    _description = "Product Chemical Stock"
    _auto = False
    _order = "product_tmpl_id, location_id, substance_id"
    _depends = {
        "product.template": ["is_chemical", "uom_id"],
        "product.product": ["product_tmpl_id"],
        "product.template.chemical.substance.line": [
            "product_tmpl_id",
            "substance_id",
            "content_rate",
        ],
        "product.chemical.substance": ["cas_no"],
        "stock.quant": ["product_id", "location_id", "quantity"],
        "stock.location": ["usage"],
        "uom.uom": ["category_id", "factor"],
        "uom.category": ["chemical_uom_id"],
    }

    product_tmpl_id = fields.Many2one(
        "product.template", string="Product", readonly=True
    )
    location_id = fields.Many2one("stock.location", string="Location", readonly=True)
    substance_id = fields.Many2one(
        "product.chemical.substance", string="Substance", readonly=True
    )
    cas_no = fields.Char(string="CAS No.", readonly=True)
    quantity = fields.Float(string="On Hand Qty", readonly=True)
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Product UoM",
        readonly=True,
        help="Unit of measure the on-hand quantity is expressed in.",
    )
    uom_category_id = fields.Many2one(
        "uom.category", string="UoM Category", readonly=True
    )
    content_rate = fields.Float(string="Content Rate (%)", readonly=True)
    component_amount = fields.Float(readonly=True)
    amount_uom_id = fields.Many2one(
        "uom.uom",
        string="Amount UoM",
        readonly=True,
        help="Unit of measure the component amount is expressed in: the chemical "
        "aggregation unit of the UoM category, or the product unit when the "
        "category has none.",
    )

    @property
    def _table_query(self):
        # Component amounts are converted into the chemical aggregation unit of
        # the product's UoM category, so that amounts of the same kind (weight,
        # volume) add up. Categories without an aggregation unit are reported
        # unconverted, which keeps count-managed products listed while leaving
        # them out of the weight and volume totals.
        return """
            SELECT
                ROW_NUMBER() OVER () AS id,
                pt.id AS product_tmpl_id,
                sq.location_id AS location_id,
                sub_line.substance_id AS substance_id,
                sub.cas_no AS cas_no,
                pt.uom_id AS product_uom_id,
                pu.category_id AS uom_category_id,
                COALESCE(uc.chemical_uom_id, pt.uom_id) AS amount_uom_id,
                SUM(sq.quantity) AS quantity,
                sub_line.content_rate AS content_rate,
                SUM(sq.quantity)
                    * COALESCE(au.factor / pu.factor, 1.0)
                    * sub_line.content_rate / 100.0
                    AS component_amount
            FROM product_template pt
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            JOIN product_template_chemical_substance_line sub_line
                ON sub_line.product_tmpl_id = pt.id
            JOIN product_chemical_substance sub
                ON sub.id = sub_line.substance_id
            JOIN stock_quant sq ON sq.product_id = pp.id
            JOIN stock_location sl
                ON sl.id = sq.location_id AND sl.usage = 'internal'
            JOIN uom_uom pu ON pu.id = pt.uom_id
            JOIN uom_category uc ON uc.id = pu.category_id
            LEFT JOIN uom_uom au ON au.id = uc.chemical_uom_id
            WHERE pt.is_chemical = TRUE
            GROUP BY
                pt.id,
                sq.location_id,
                sub_line.substance_id,
                sub.cas_no,
                pt.uom_id,
                pu.category_id,
                pu.factor,
                uc.chemical_uom_id,
                au.factor,
                sub_line.content_rate
        """
