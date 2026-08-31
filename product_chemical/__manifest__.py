# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Product Chemical",
    "version": "18.0.1.7.0",
    "category": "Inventory/Inventory",
    "summary": "Manage chemical substance information on products",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["product", "stock", "uom"],
    "data": [
        "security/ir.model.access.csv",
        "views/uom_category_views.xml",
        "views/product_chemical_law_views.xml",
        "views/product_chemical_law_category_views.xml",
        "views/product_chemical_substance_views.xml",
        "views/product_chemical_stock_views.xml",
        "views/product_chemical_consumption_views.xml",
        "views/product_template_views.xml",
        "views/stock_location_views.xml",
        "views/stock_move_views.xml",
        "views/product_chemical_menu.xml",
    ],
    "installable": True,
}
