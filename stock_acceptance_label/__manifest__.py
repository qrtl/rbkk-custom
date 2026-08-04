# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Acceptance Label",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Print acceptance labels from transfers, 3 per A4 portrait sheet",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "maintainers": ["kanda999"],
    "depends": ["product_expiry", "stock"],
    "data": [
        "report/stock_acceptance_label_report.xml",
        "report/stock_acceptance_label_templates.xml",
        "views/res_config_settings_views.xml",
        "views/stock_picking_views.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "stock_acceptance_label/static/src/scss/report_acceptance_label.scss",
        ],
    },
    "installable": True,
}
