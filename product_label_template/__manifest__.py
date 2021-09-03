# Copyright 2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Product Label Template",
    "version": "12.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Products",
    "license": "LGPL-3",
    "depends": ["mrp", "stock_lot_expiry_rpl"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_label_template_views.xml",
        "views/product_product_views.xml",
        "views/templates.xml",
    ],
    "installable": True,
}
