# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Maintenance Equipment Inventory",
    "version": "18.0.1.0.0",
    "category": "Maintenance",
    "summary": "Manage stocktaking (inventory) history for maintenance equipment "
    "with a draft/to approve/approved workflow",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["maintenance"],
    "data": [
        "security/ir.model.access.csv",
        "security/maintenance_equipment_inventory_security.xml",
        "data/ir_sequence_data.xml",
        "views/maintenance_equipment_inventory_record_views.xml",
        "views/maintenance_equipment_views.xml",
    ],
    "installable": True,
}
