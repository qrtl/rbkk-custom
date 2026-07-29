# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, new_test_user


class TestMaintenanceEquipmentInventoryRecord(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": "Test Equipment"}
        )
        cls.manager = new_test_user(
            cls.env,
            login="inv_manager",
            groups="maintenance.group_equipment_manager",
        )
        cls.user = new_test_user(
            cls.env,
            login="inv_user",
            groups="base.group_user",
        )
        cls.Record = cls.env["maintenance.equipment.inventory.record"]

    def _create_record(self):
        return self.Record.create(
            {
                "equipment_id": self.equipment.id,
                "inventory_date": "2026-06-01",
                "result": "ok",
            }
        )

    def test_sequence_assigned(self):
        record = self._create_record()
        self.assertNotEqual(record.name, "New")
        self.assertTrue(record.name.startswith("INV/"))

    def test_workflow_and_approval(self):
        record = self._create_record()
        self.assertEqual(record.state, "draft")
        record.action_submit()
        self.assertEqual(record.state, "to_approve")
        # A plain user cannot approve.
        with self.assertRaises(UserError):
            record.with_user(self.user).action_approve()
        record.with_user(self.manager).action_approve()
        self.assertEqual(record.state, "approved")
        self.assertEqual(record.approved_by_id, self.manager)
        self.assertTrue(record.approved_date)

    def test_approved_record_is_locked(self):
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            record.write({"result": "abnormal"})
        with self.assertRaises(UserError):
            record.unlink()

    def test_approved_state_cannot_be_reset_by_raw_write(self):
        # A raw write on the workflow field must not bypass the lock; resetting
        # an approved record has to go through action_reset_to_draft.
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            record.with_user(self.user).write({"state": "draft"})
        self.assertEqual(record.state, "approved")

    def test_reset_to_draft_unlocks(self):
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        record.action_reset_to_draft()
        self.assertEqual(record.state, "draft")
        self.assertFalse(record.approved_by_id)
        # Editing is allowed again once back in draft.
        record.write({"result": "abnormal"})
        self.assertEqual(record.result, "abnormal")

    def test_reset_to_draft_requires_manager(self):
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        # A plain user cannot reset an approved record to draft.
        with self.assertRaises(UserError):
            record.with_user(self.user).action_reset_to_draft()

    def test_reset_to_approve_by_user(self):
        # A plain user may pull a not-yet-approved record back to draft.
        record = self._create_record()
        record.action_submit()
        self.assertEqual(record.state, "to_approve")
        record.with_user(self.user).action_reset_to_draft()
        self.assertEqual(record.state, "draft")

    def test_equipment_last_inventory_computed(self):
        first = self._create_record()
        first.action_submit()
        first.with_user(self.manager).action_approve()
        second = self.Record.create(
            {
                "equipment_id": self.equipment.id,
                "inventory_date": "2026-06-10",
                "result": "abnormal",
            }
        )
        second.action_submit()
        second.with_user(self.manager).action_approve()
        # A draft record must not affect the computed values.
        self.Record.create(
            {
                "equipment_id": self.equipment.id,
                "inventory_date": "2026-06-20",
                "result": "lost",
            }
        )
        self.equipment.invalidate_recordset()
        self.assertEqual(str(self.equipment.last_inventory_date), "2026-06-10")
        self.assertEqual(self.equipment.last_inventory_result, "abnormal")

    def test_bulk_create_inventory_records(self):
        equipment2 = self.env["maintenance.equipment"].create(
            {"name": "Test Equipment 2"}
        )
        equipments = self.equipment | equipment2
        action = equipments.action_create_inventory_records()
        records = self.Record.search(action["domain"])
        self.assertEqual(len(records), 2)
        self.assertEqual(records.equipment_id, equipments)
        # Records are created with just the equipment; defaults fill the rest.
        self.assertTrue(all(r.state == "draft" for r in records))
        self.assertTrue(all(r.name.startswith("INV/") for r in records))

    def test_bulk_create_skips_open_records(self):
        # An existing open (draft) record makes the equipment be skipped.
        self._create_record()
        equipment2 = self.env["maintenance.equipment"].create(
            {"name": "Test Equipment 2"}
        )
        equipments = self.equipment | equipment2
        action = equipments.action_create_inventory_records()
        records = self.Record.search(action["domain"])
        self.assertEqual(records.equipment_id, equipment2)

    def test_bulk_create_reruns_after_approval(self):
        # An equipment whose only record is approved is eligible again.
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        action = self.equipment.action_create_inventory_records()
        records = self.Record.search(action["domain"])
        self.assertEqual(len(records), 1)
        self.assertEqual(records.equipment_id, self.equipment)
