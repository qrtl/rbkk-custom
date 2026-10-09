# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductChemicalConsumption(models.Model):
    _name = "product.chemical.consumption"
    _description = "Product Chemical Consumption"
    _order = "actual_date desc, id desc"

    move_id = fields.Many2one(
        "stock.move",
        string="Stock Move",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    substance_id = fields.Many2one(
        "product.chemical.substance",
        required=True,
        ondelete="restrict",
        index=True,
        readonly=True,
    )
    product_id = fields.Many2one(related="move_id.product_id")
    actual_date = fields.Datetime(
        related="move_id.date",
        string="Actual Date",
        help="Date the move was processed.",
    )
    location_id = fields.Many2one(related="move_id.location_id")
    location_dest_id = fields.Many2one(
        related="move_id.location_dest_id", string="Destination Location"
    )
    quantity = fields.Float(
        related="move_id.quantity", string="Moved Qty", digits="Product Unit of Measure"
    )
    product_uom_id = fields.Many2one(
        related="move_id.product_uom", string="Product UoM"
    )
    # Copied from the substance line when recorded, then left unchanged.
    content_rate = fields.Float(string="Content Rate (%)", readonly=True)
    amount = fields.Float(
        string="Consumed Amount",
        compute="_compute_amount",
        store=True,
        precompute=True,
        help="Amount of the substance used up, negative when it is returned "
        "to the stock.",
    )
    amount_uom_id = fields.Many2one(
        "uom.uom",
        string="Amount UoM",
        compute="_compute_amount_uom_id",
        store=True,
        precompute=True,
        help="Unit of measure the consumed amount is expressed in: the chemical "
        "aggregation unit of the UoM category, or the product unit when the "
        "category has none.",
    )

    @api.depends("move_id")
    def _compute_amount_uom_id(self):
        for rec in self:
            product_tmpl = rec.move_id.product_id.product_tmpl_id
            rec.amount_uom_id = product_tmpl._get_chemical_amount_uom()

    @api.depends(
        "quantity", "product_uom_id", "amount_uom_id", "content_rate", "move_id"
    )
    def _compute_amount(self):
        for rec in self:
            quantity = rec.product_uom_id._compute_quantity(
                rec.quantity, rec.amount_uom_id, round=False
            )
            sign = rec.move_id._get_chemical_consumption_sign()
            rec.amount = sign * quantity * rec.content_rate / 100.0

    def action_sync_from_move(self):
        return self.move_id.action_sync_chemical_consumption()
