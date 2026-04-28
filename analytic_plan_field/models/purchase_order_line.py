# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "analytic.plan.account.mixin"]
    _analytic_plan_config_param = "analytic_plan_field.purchase_order_line.plan_id"
