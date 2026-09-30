# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Acceptance Number",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Number the goods received in a transfer, per lot",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "maintainers": ["kanda999"],
    "depends": ["stock"],
    "data": [
        "views/stock_lot_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
