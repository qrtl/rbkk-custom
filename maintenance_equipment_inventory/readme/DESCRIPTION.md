This module lets you record and manage the stocktaking (inventory) history of
maintenance equipment.

Each inventory check is stored as a `maintenance.equipment.inventory.record`,
linked to its equipment through a One2many relation. Records follow a
**Draft → To Approve → Approved** workflow, support attachments and message
tracking (mail.thread), and become read-only once approved.

The latest approved inventory date and result are shown directly on the
equipment form through stored computed fields.
