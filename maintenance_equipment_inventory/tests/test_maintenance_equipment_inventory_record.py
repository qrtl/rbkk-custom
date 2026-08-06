# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, new_test_user, tagged


# Creating users requires fields contributed by modules that load after this
# one (e.g. ``res.partner.autopost_bills`` from ``account``), so the tests must
# run once every module is loaded.
@tagged("post_install", "-at_install")
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
                "result": "normal",
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

    def test_refuse_and_resubmit(self):
        record = self._create_record()
        record.action_submit()
        # A plain user cannot refuse.
        with self.assertRaises(UserError):
            record.with_user(self.user).action_refuse()
        record.with_user(self.manager).action_refuse()
        self.assertEqual(record.state, "refused")
        # A refused record stays editable so that it can be corrected, and the
        # reason for the refusal lives in the chatter.
        record.write({"result": "abnormal"})
        record.action_submit()
        self.assertEqual(record.state, "to_approve")
        record.with_user(self.manager).action_approve()
        self.assertEqual(record.state, "approved")

    def test_refuse_requires_pending_approval(self):
        record = self._create_record()
        with self.assertRaises(UserError):
            record.with_user(self.manager).action_refuse()

    def test_refused_record_is_not_the_last_inventory(self):
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_refuse()
        self.equipment.invalidate_recordset()
        self.assertFalse(self.equipment.last_inventory_date)

    def test_cancel_and_reset(self):
        record = self._create_record()
        # A plain user can cancel a record for equipment that is out of scope.
        record.with_user(self.user).action_cancel()
        self.assertEqual(record.state, "cancelled")
        record.action_reset_to_draft()
        self.assertEqual(record.state, "draft")

    def test_approved_record_cannot_be_cancelled(self):
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            record.action_cancel()

    def test_approved_record_is_locked(self):
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        for vals in (
            {"result": "abnormal"},
            {"inventory_date": "2026-06-02"},
            {"checked_by_id": self.user.id},
            {"note": "<p>Late edit</p>"},
        ):
            with self.assertRaises(UserError):
                record.write(vals)
        with self.assertRaises(UserError):
            record.unlink()

    def test_approved_record_still_accepts_chatter(self):
        # The lock only covers the business fields, so the mail framework can
        # still log messages and attachments on an approved record.
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_approve()
        record.message_post(body="Inventory sheet filed")
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

    def test_bulk_create_without_target_is_reported(self):
        # Skipping every selected equipment must not silently show an empty list.
        self._create_record()
        with self.assertRaises(UserError):
            self.equipment.action_create_inventory_records()

    def test_bulk_create_skips_refused_records(self):
        # A refused record means the stocktaking round is still unfinished for
        # that equipment, so it must not get a second record.
        record = self._create_record()
        record.action_submit()
        record.with_user(self.manager).action_refuse()
        equipment2 = self.env["maintenance.equipment"].create(
            {"name": "Test Equipment 2"}
        )
        equipments = self.equipment | equipment2
        action = equipments.action_create_inventory_records()
        records = self.Record.search(action["domain"])
        self.assertEqual(records.equipment_id, equipment2)

    def test_bulk_create_skips_cancelled_records(self):
        # Cancelling instead of deleting keeps the equipment out of a rerun.
        self._create_record().action_cancel()
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
