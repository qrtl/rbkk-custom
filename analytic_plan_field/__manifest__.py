# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Analytic Plan Field",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Add stored computed fields to models from analytic plan distribution",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["purchase", "analytic"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/purchase_order_line_views.xml",
    ],
    "installable": True,
}
