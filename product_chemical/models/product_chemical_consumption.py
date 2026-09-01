# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductChemicalConsumption(models.Model):
    _name = "product.chemical.consumption"
    _description = "Product Chemical Consumption"
    _order = "actual_date desc, id desc"

    # The record is a snapshot: every field is precomputed at creation and none
    # of them follows a later change on the move, so past records keep what was
    # actually handled. Precomputing matters -- computed on flush instead, they
    # would pick up whatever the move and the product hold by the end of the
    # transaction. Nothing is editable either; a wrong composition is fixed on
    # the product and replayed with the Update Chemical Consumption action.
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
    product_id = fields.Many2one(
        "product.product",
        compute="_compute_product_id",
        store=True,
        precompute=True,
        index=True,
    )
    actual_date = fields.Datetime(
        compute="_compute_actual_date",
        store=True,
        precompute=True,
        index=True,
        help="Date the move was processed.",
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        compute="_compute_location_id",
        store=True,
        precompute=True,
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        compute="_compute_location_dest_id",
        store=True,
        precompute=True,
    )
    quantity = fields.Float(
        string="Moved Qty",
        compute="_compute_quantity",
        store=True,
        precompute=True,
        digits="Product Unit of Measure",
    )
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Product UoM",
        compute="_compute_product_uom_id",
        store=True,
        precompute=True,
        help="Unit of measure the moved quantity is expressed in.",
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
    def _compute_product_id(self):
        for rec in self:
            rec.product_id = rec.move_id.product_id

    @api.depends("move_id")
    def _compute_actual_date(self):
        for rec in self:
            rec.actual_date = rec.move_id.date

    @api.depends("move_id")
    def _compute_location_id(self):
        for rec in self:
            rec.location_id = rec.move_id.location_id

    @api.depends("move_id")
    def _compute_location_dest_id(self):
        for rec in self:
            rec.location_dest_id = rec.move_id.location_dest_id

    @api.depends("move_id")
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = rec.move_id.quantity

    @api.depends("move_id")
    def _compute_product_uom_id(self):
        for rec in self:
            rec.product_uom_id = rec.move_id.product_uom

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
            quantity = rec.quantity
            if rec.product_uom_id and rec.amount_uom_id:
                quantity = rec.product_uom_id._compute_quantity(
                    quantity, rec.amount_uom_id, round=False
                )
            sign = rec.move_id._get_chemical_consumption_sign()
            rec.amount = sign * quantity * rec.content_rate / 100.0

    def action_sync_from_move(self):
        """Rebuild the amounts of the moves these records belong to."""
        return self.move_id.action_sync_chemical_consumption()
