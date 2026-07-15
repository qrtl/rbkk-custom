# Copyright 2021 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Product Label Template",
    "version": "18.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Inventory",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/ir_actions_report_views.xml",
        "views/product_label_template_views.xml",
        "views/product_product_views.xml",
        "reports/product_label_report.xml",
    ],
    "installable": True,
}
