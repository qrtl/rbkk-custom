# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_chemical = fields.Boolean(string="Chemical")
    track_chemical_consumption = fields.Boolean(default=False)
    # Copied over on duplication: One2many defaults to copy=False, which would
    # leave the duplicate flagged as a chemical while holding no composition at
    # all, so it would be reported nowhere and record no consumption.
    chemical_law_line_ids = fields.One2many(
        "product.template.chemical.law.line",
        "product_tmpl_id",
        string="Laws",
        copy=True,
    )
    chemical_substance_line_ids = fields.One2many(
        "product.template.chemical.substance.line",
        "product_tmpl_id",
        string="Chemical Substances",
        copy=True,
    )
    chemical_substance_ids = fields.Many2many(
        "product.chemical.substance",
        compute="_compute_chemical_substance_ids",
        search="_search_chemical_substance_ids",
        string="Substances",
    )
    risk_assessment_file = fields.Binary(string="Risk Assessment Sheet")
    risk_assessment_filename = fields.Char(string="Risk Assessment Sheet Filename")
    chemical_stock_ids = fields.One2many(
        "product.chemical.stock",
        "product_tmpl_id",
        string="Component Amount by Location",
        readonly=True,
    )

    @api.depends("chemical_substance_line_ids.substance_id")
    def _compute_chemical_substance_ids(self):
        for rec in self:
            rec.chemical_substance_ids = rec.chemical_substance_line_ids.substance_id

    def _search_chemical_substance_ids(self, operator, value):
        return [("chemical_substance_line_ids.substance_id", operator, value)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("is_chemical"):
                vals["track_chemical_consumption"] = False
        return super().create(vals_list)

    def write(self, vals):
        if "is_chemical" in vals and not vals["is_chemical"]:
            vals = dict(vals, track_chemical_consumption=False)
        return super().write(vals)

    def _get_chemical_amount_uom(self):
        """Return the unit chemical amounts of this product are expressed in.

        The same rule is applied in SQL by product.chemical.stock, so
        that both reports aggregate amounts into the same unit.
        """
        self.ensure_one()
        return self.uom_id.category_id.chemical_uom_id or self.uom_id
