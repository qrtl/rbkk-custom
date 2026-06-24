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
