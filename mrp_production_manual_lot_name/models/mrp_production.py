# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    mrp_manual_lot_name = fields.Boolean(
        related="product_id.mrp_manual_lot_name",
    )
    lot_producing_name = fields.Char(
        string="Lot/Serial Number Name",
        help="Enter the lot/serial number name manually.",
    )

    @api.constrains("lot_producing_name", "product_id")
    def _check_lot_producing_name_unique(self):
        for production in self:
            if not production.lot_producing_name:
                continue
            existing_lot = self.env["stock.lot"].search(
                [
                    ("name", "=", production.lot_producing_name),
                    ("product_id", "=", production.product_id.id),
                    ("company_id", "=", production.company_id.id),
                ],
                limit=1,
            )
            if existing_lot:
                raise ValidationError(
                    _(
                        "A lot/serial number with name '%(lot_name)s' already exists "
                        "for product '%(product_name)s'.",
                        lot_name=production.lot_producing_name,
                        product_name=production.product_id.display_name,
                    )
                )

    def _prepare_stock_lot_values(self):
        res = super()._prepare_stock_lot_values()
        if self.mrp_manual_lot_name and self.lot_producing_name:
            res["name"] = self.lot_producing_name
        return res

    def _set_lot_producing(self):
        res = super()._set_lot_producing()
        for production in self:
            if production.lot_producing_name and production.lot_producing_id:
                production.lot_producing_name = False
        return res
