# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Purchase Analytic Plan",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Expose a stored analytic plan account on purchase order lines",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["purchase"],
    "data": [
        "views/analytic_plan_views.xml",
        "views/purchase_order_line_views.xml",
    ],
    "installable": True,
}
