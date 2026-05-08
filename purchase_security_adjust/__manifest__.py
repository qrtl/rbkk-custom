# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Security Adjust",
    "version": "18.0.1.0.0",
    "category": "Purchase",
    "summary": "Allow purchase users to view the purchase secondary UoM on products",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "depends": ["purchase_order_secondary_unit"],
    "data": [
        "views/product_views.xml",
    ],
    "installable": True,
}
