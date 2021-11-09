# Copyright 2021 Quartile Limited
{
    "name": "Product Label Template",
    "version": "12.0.1.1.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Products",
    "license": "Other proprietary",
    "depends": ["stock_lot_expiry_rpl", "stock_lot_serial"],
    "external_dependencies": {"python": ["treepoem"]},
    "data": [
        "security/ir.model.access.csv",
        "views/ir_actions_report_views.xml",
        "views/product_label_template_views.xml",
        "views/product_product_views.xml",
        "views/templates.xml",
        "views/stock_production_lot_views.xml",
    ],
    "installable": True,
}
