# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Maintenance Additional Attributes",
    "version": "18.0.1.0.0",
    "category": "Maintenance",
    "summary": "Add specific attributes to maintenance equipment and requests",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "maintainers": ["smorita7749"],
    "license": "LGPL-3",
    "depends": ["maintenance", "purchase", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "security/maintenance_equipment_security.xml",
        "data/mail_activity_type.xml",
        "data/ir_cron.xml",
        "views/maintenance_equipment_department_views.xml",
        "views/maintenance_equipment_generic_name_views.xml",
        "views/maintenance_equipment_views.xml",
        "views/maintenance_request_views.xml",
    ],
    "installable": True,
}
