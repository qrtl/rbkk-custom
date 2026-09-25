This module lets you record and manage the stocktaking (inventory) history of
maintenance equipment.

Each inventory check is stored as a `maintenance.equipment.inventory.record`,
linked to its equipment through a One2many relation. Records follow a
**Draft → To Approve → Approved** workflow, keep their history in the chatter
(mail.thread), and become read-only once approved.

A Maintenance Manager can also refuse a record pending approval. A refused
record stays editable so that it can be corrected and submitted again; the
reason for the refusal is logged in the chatter.

A record can be cancelled when the equipment turns out to be out of scope for
the round (for instance because it has been scrapped). Cancelling rather than
deleting keeps the equipment out of the next bulk creation.

The latest approved inventory date and result are shown directly on the
equipment form through stored computed fields.
