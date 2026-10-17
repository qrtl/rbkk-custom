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
    # product_expiry for the expiration date of the lot, and
    # stock_acceptance_number for the number the label prints.
    "depends": ["product_expiry", "stock_acceptance_number"],
    "data": [
        "report/stock_acceptance_label_report.xml",
        "report/stock_acceptance_label_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
