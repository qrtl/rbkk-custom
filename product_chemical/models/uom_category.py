# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UomCategory(models.Model):
    _inherit = "uom.category"

    chemical_uom_id = fields.Many2one(
        "uom.uom",
        string="Chemical Aggregation UoM",
        domain="[('category_id', '=', id)]",
        ondelete="restrict",
        help="Chemical component amounts of products measured in this category are "
        "converted to this unit before being aggregated. Leave it empty to report "
        "the amounts without conversion, e.g. for count-managed products.",
    )

    @api.constrains("chemical_uom_id")
    def _check_chemical_uom_id(self):
        # The field domain is only enforced client side, so keep import and ORM
        # writes from pointing at a unit of another category.
        for categ in self:
            if categ.chemical_uom_id and categ.chemical_uom_id.category_id != categ:
                raise ValidationError(
                    self.env._(
                        "The chemical aggregation unit of measure of category "
                        "%(category)s must belong to that category.",
                        category=categ.name,
                    )
                )
