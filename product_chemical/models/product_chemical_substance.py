# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductChemicalSubstance(models.Model):
    _name = "product.chemical.substance"
    _description = "Chemical Substance"
    _order = "name"
    _rec_names_search = ["name", "cas_no"]

    name = fields.Char(required=True, translate=True)
    cas_no = fields.Char(string="CAS No.", required=True)
    content_rate = fields.Float(
        string="Content Rate (%)",
        default=0.0,
        help="Default content rate (%) used when adding this substance to a product.",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("cas_no_uniq", "unique(cas_no)", "CAS No. must be unique."),
        (
            "content_rate_range",
            "CHECK(content_rate >= 0 AND content_rate <= 100)",
            "Content rate must be between 0 and 100.",
        ),
    ]

    @api.depends("name", "cas_no")
    def _compute_display_name(self):
        for rec in self:
            if rec.name and rec.cas_no:
                rec.display_name = f"[{rec.cas_no}] {rec.name}"
            else:
                rec.display_name = rec.name or rec.cas_no or ""
