# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Maintenance Equipment Additional Attributes",
    "version": "18.0.1.0.0",
    "category": "Maintenance",
    "summary": "Add specific attributes to maintenance equipment",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "maintainers": ["smorita7749"],
    "license": "LGPL-3",
    "depends": ["maintenance", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/maintenance_equipment_generic_name_views.xml",
        "views/maintenance_equipment_national_project_views.xml",
        "views/maintenance_equipment_views.xml",
    ],
    "installable": True,
}
