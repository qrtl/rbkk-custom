This module lets you record the stocktaking (inventory) history of maintenance
equipment. Each inventory record goes through a
**Draft → To Approve → Approved** workflow and can no longer be edited once
approved.

Each record has three checks. Tick each one when it is fine, so an unticked
check means the equipment needs attention:

- **Equipment Found**: the equipment was found.
- **Seal Attached**: the seal is attached to the equipment.
- **In Use**: the equipment is in use. Leave it unticked when it is idle.

Inventory records can be created in bulk from the equipment list:

- **Assigned To** is set to the technician of the equipment, and can be changed.
- **Inventory Date** is set to the creation date, and can be changed.
- **Checked By** is left empty until the check is done, and must be set before
  the record is submitted.

A Maintenance Manager approves or refuses submitted records. A refused record
can be corrected and submitted again. A record can be cancelled when the
equipment is out of scope for the round (for instance, it has been scrapped).

The **Inventory** tab of the equipment form shows the **Last Inventory Date**
and the **Last Inventory Result** of the latest approved record. The result is
**Pass** when all three checks are ticked, and **Fail** otherwise.
