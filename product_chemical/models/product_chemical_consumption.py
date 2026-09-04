# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductChemicalConsumption(models.Model):
    _name = "product.chemical.consumption"
    _description = "Product Chemical Consumption"
    _order = "actual_date desc, id desc"

    # The move side is read straight off the move, so correcting a move
    # corrects the amounts booked against it. The composition is not: the
    # content rate is precomputed at creation -- computed on flush it would
    # pick up whatever the product holds by the end of the transaction -- and
    # stays put when the product is revised, so past records keep the rate that
    # was applied to them. A wrong rate is put right on the product and
    # replayed with the Update Chemical Consumption action.
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
    content_rate = fields.Float(
        string="Content Rate (%)",
        compute="_compute_content_rate",
        store=True,
        precompute=True,
    )
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

    _sql_constraints = [
        (
            "move_substance_uniq",
            "unique(move_id, substance_id)",
            "Each substance can be recorded only once per stock move.",
        ),
    ]

    @api.depends("move_id")
    def _compute_amount_uom_id(self):
        for rec in self:
            product_tmpl = rec.move_id.product_id.product_tmpl_id
            rec.amount_uom_id = product_tmpl._get_chemical_amount_uom()

    @api.depends("move_id", "substance_id")
    def _compute_content_rate(self):
        for rec in self:
            rates = {
                line.substance_id: line.content_rate
                for line in rec.move_id.product_id.chemical_substance_line_ids
            }
            rec.content_rate = rates.get(rec.substance_id, 0.0)

    @api.depends(
        "quantity", "product_uom_id", "amount_uom_id", "content_rate", "move_id"
    )
    def _compute_amount(self):
        # Amounts are converted into the chemical aggregation unit of the
        # product's UoM category, so that amounts of the same kind (weight,
        # volume) add up, the way product.chemical.stock does it.
        for rec in self:
            quantity = rec.product_uom_id._compute_quantity(
                rec.quantity, rec.amount_uom_id, round=False
            )
            sign = rec.move_id._get_chemical_consumption_sign()
            rec.amount = sign * quantity * rec.content_rate / 100.0

    def action_sync_from_move(self):
        """Rebuild the amounts of the moves these records belong to."""
        return self.move_id.action_sync_chemical_consumption()
