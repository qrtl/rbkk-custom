# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductChemicalMoveAmount(models.Model):
    _name = "product.chemical.move.amount"
    _description = "Product Chemical Amount by Stock Move"
    _order = "actual_date desc, id desc"

    move_id = fields.Many2one(
        "stock.move",
        string="Stock Move",
        required=True,
        ondelete="cascade",
        index=True,
    )
    substance_id = fields.Many2one(
        "product.chemical.substance", required=True, ondelete="restrict", index=True
    )
    product_id = fields.Many2one(related="move_id.product_id", store=True, index=True)
    actual_date = fields.Datetime(
        related="move_id.date",
        string="Actual Date",
        store=True,
        index=True,
        help="Date the move was processed.",
    )
    company_id = fields.Many2one(related="move_id.company_id", store=True, index=True)
    location_id = fields.Many2one(related="move_id.location_id", store=True)
    location_dest_id = fields.Many2one(
        related="move_id.location_dest_id", string="Destination Location", store=True
    )
    picking_type_id = fields.Many2one(related="move_id.picking_type_id", store=True)
    direction = fields.Selection(
        [
            ("in", "Receipt"),
            ("out", "Delivery"),
            ("internal", "Internal Transfer"),
        ],
        compute="_compute_direction",
        store=True,
        precompute=True,
        index=True,
    )
    # The direction, the quantity, the units and the content rate are
    # snapshots: they are precomputed from the move when the record is created
    # and are not recomputed when the product composition is revised
    # afterwards, so that past movements keep the amounts that were actually
    # handled. Precomputing them matters: computed on flush instead, they would
    # pick up whatever the product holds by the end of the transaction.
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
        readonly=False,
    )
    amount = fields.Float(
        string="Component Amount",
        compute="_compute_amount",
        store=True,
        precompute=True,
        help="Amount of the substance moved, negative for a delivery.",
    )
    amount_uom_id = fields.Many2one(
        "uom.uom",
        string="Amount UoM",
        compute="_compute_amount_uom_id",
        store=True,
        precompute=True,
        help="Unit of measure the component amount is expressed in: the chemical "
        "aggregation unit of the UoM category, or the product unit when the "
        "category has none.",
    )

    _sql_constraints = [
        (
            "move_substance_uniq",
            "unique(move_id, substance_id)",
            "Each substance can be recorded only once per stock move.",
        ),
        (
            "content_rate_range",
            "CHECK(content_rate >= 0 AND content_rate <= 100)",
            "Content rate must be between 0 and 100.",
        ),
    ]

    @api.depends("move_id")
    def _compute_direction(self):
        for rec in self:
            from_internal = rec.move_id.location_id.usage == "internal"
            to_internal = rec.move_id.location_dest_id.usage == "internal"
            if from_internal and to_internal:
                rec.direction = "internal"
            elif to_internal:
                rec.direction = "in"
            else:
                rec.direction = "out"

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
        "quantity", "product_uom_id", "amount_uom_id", "content_rate", "direction"
    )
    def _compute_amount(self):
        # Amounts are converted into the chemical aggregation unit of the
        # product's UoM category, so that amounts of the same kind (weight,
        # volume) add up, the way product.chemical.location.amount does it.
        for rec in self:
            quantity = rec.quantity
            if rec.product_uom_id and rec.amount_uom_id:
                quantity = rec.product_uom_id._compute_quantity(
                    quantity, rec.amount_uom_id, round=False
                )
            sign = -1 if rec.direction == "out" else 1
            rec.amount = sign * quantity * rec.content_rate / 100.0

    def action_sync_from_move(self):
        """Rebuild the amounts of the moves these records belong to."""
        return self.move_id.action_sync_chemical_amounts()
