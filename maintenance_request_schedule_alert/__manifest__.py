# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Maintenance Request Schedule Alert",
    "version": "18.0.1.0.0",
    "category": "Maintenance",
    "summary": "Alert the responsible user a configurable period before the "
    "scheduled maintenance date",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "maintainers": ["smorita7749"],
    "license": "LGPL-3",
    "depends": ["maintenance"],
    "data": [
        "data/ir_cron.xml",
        "views/maintenance_request_views.xml",
    ],
    "installable": True,
}
