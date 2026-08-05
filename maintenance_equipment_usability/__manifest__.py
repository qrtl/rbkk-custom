# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Maintenance Equipment Usability",
    "version": "18.0.1.0.0",
    "category": "Maintenance",
    "summary": "Compute equipment usability from maintenance request results",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "maintainers": ["smorita7749"],
    "license": "LGPL-3",
    "depends": ["maintenance"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/maintenance_request_views.xml",
        "views/maintenance_equipment_views.xml",
    ],
    "installable": True,
}
