# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductChemicalLaw(models.Model):
    _name = "product.chemical.law"
    _description = "Chemical Law"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    note = fields.Text()
    major_category_ids = fields.One2many(
        "product.chemical.major.category",
        "law_id",
        string="Major Categories",
    )
    product_count = fields.Integer(compute="_compute_product_count")

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Law name must be unique."),
    ]

    def _compute_product_count(self):
        line_data = self.env["product.chemical.law.line"]._read_group(
            [("law_id", "in", self.ids)],
            groupby=["law_id"],
            aggregates=["product_tmpl_id:count_distinct"],
        )
        counts = {law.id: count for law, count in line_data}
        for rec in self:
            rec.product_count = counts.get(rec.id, 0)

    def action_view_products(self):
        self.ensure_one()
        product_ids = (
            self.env["product.chemical.law.line"]
            .search([("law_id", "=", self.id)])
            .product_tmpl_id.ids
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "product.product_template_action"
        )
        action["domain"] = [("id", "in", product_ids)]
        action["context"] = {"default_is_chemical": True}
        return action
