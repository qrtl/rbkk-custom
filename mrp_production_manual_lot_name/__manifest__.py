# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "MRP Production Manual Lot Name",
    "version": "18.0.1.0.0",
    "category": "Manufacturing",
    "summary": "Allow manual lot/serial number entry in manufacturing orders",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["mrp"],
    "data": [
        "views/product_template_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
}
