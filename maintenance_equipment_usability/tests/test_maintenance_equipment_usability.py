# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestMaintenanceEquipmentUsability(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": "Usability Test Equipment", "status": "operating"}
        )
        cls.open_stage = cls.env.ref("maintenance.stage_0")
        cls.done_stage = cls.env.ref("maintenance.stage_3")
        cls.today = fields.Date.context_today(cls.equipment)

    def _create_request(self, stage, result="none", request_date=None, close_date=None):
        vals = {
            "name": f"Request {stage.name}",
            "equipment_id": self.equipment.id,
            "stage_id": stage.id,
            "request_date": request_date or self.today,
            "maintenance_result": result,
        }
        if close_date:
            vals["close_date"] = close_date
        return self.env["maintenance.request"].create(vals)

    def test_usability_unknown_without_completed_result(self):
        self.assertEqual(self.equipment.usability_state, "unknown")
        # A result on a request that is not done yet is ignored.
        self._create_request(self.open_stage, result="passed")
        self.assertEqual(self.equipment.usability_state, "unknown")
        # A done request without a result is ignored.
        self._create_request(self.done_stage, result="none", close_date=self.today)
        self.assertEqual(self.equipment.usability_state, "unknown")
        self.assertFalse(self.equipment.latest_maintenance_result_request_id)
        self.assertFalse(self.equipment.latest_maintenance_result_date)

    def test_passed_within_grace_is_usable(self):
        close = self.today - relativedelta(months=1)
        self._create_request(self.done_stage, result="passed", close_date=close)
        self.assertEqual(self.equipment.usability_state, "usable")

    def test_passed_past_grace_is_unusable(self):
        close = self.today - relativedelta(months=13)
        self._create_request(self.done_stage, result="passed", close_date=close)
        self.assertEqual(self.equipment.usability_state, "unusable")

    def test_failed_is_unusable(self):
        self._create_request(self.done_stage, result="failed", close_date=self.today)
        self.assertEqual(self.equipment.usability_state, "unusable")

    def test_non_operating_status_is_unusable(self):
        self._create_request(
            self.done_stage,
            result="passed",
            close_date=self.today - relativedelta(months=1),
        )
        # Operating + passed within grace = usable.
        self.assertEqual(self.equipment.usability_state, "usable")
        # Any non-operating status forces unusable regardless of the result.
        self.equipment.status = "idle"
        self.assertEqual(self.equipment.usability_state, "unusable")
        self.equipment.status = "preparing"
        self.assertEqual(self.equipment.usability_state, "unusable")

    def test_usability_uses_latest_result_by_close_date(self):
        self._create_request(
            self.done_stage,
            result="passed",
            close_date=self.today - relativedelta(months=1),
        )
        self.assertEqual(self.equipment.usability_state, "usable")
        failed = self._create_request(
            self.done_stage, result="failed", close_date=self.today
        )
        self.assertEqual(self.equipment.usability_state, "unusable")
        self.assertEqual(self.equipment.latest_maintenance_result_request_id, failed)

    def test_grace_period_setting_extends_usability(self):
        close = self.today - relativedelta(months=13)
        self._create_request(self.done_stage, result="passed", close_date=close)
        # Default 12-month grace: the 13-month-old result has expired.
        self.assertEqual(self.equipment.usability_state, "unusable")
        # Extending the grace period to 14 months makes it usable again.
        self.env.company.usability_grace_period_months = 14
        self.equipment.invalidate_recordset(["usability_state"])
        self.assertEqual(self.equipment.usability_state, "usable")

    def test_search_usability_state(self):
        usable_equipment = self.equipment
        self._create_request(
            self.done_stage,
            result="passed",
            close_date=self.today - relativedelta(months=1),
        )
        expired_equipment = self.env["maintenance.equipment"].create(
            {"name": "Expired Equipment", "status": "operating"}
        )
        self.env["maintenance.request"].create(
            {
                "name": "Expired Request",
                "equipment_id": expired_equipment.id,
                "stage_id": self.done_stage.id,
                "request_date": self.today - relativedelta(months=13),
                "close_date": self.today - relativedelta(months=13),
                "maintenance_result": "passed",
            }
        )
        usable = self.env["maintenance.equipment"].search(
            [("usability_state", "=", "usable")]
        )
        unusable = self.env["maintenance.equipment"].search(
            [("usability_state", "=", "unusable")]
        )
        self.assertIn(usable_equipment, usable)
        self.assertNotIn(expired_equipment, usable)
        self.assertIn(expired_equipment, unusable)

    def test_create_followup_request_from_failed(self):
        request = self._create_request(
            self.done_stage, result="failed", close_date=self.today
        )
        request.action_create_followup_request()
        followup = request.followup_request_ids
        self.assertEqual(len(followup), 1)
        self.assertEqual(followup.source_request_id, request)
        self.assertEqual(followup.equipment_id, self.equipment)
        self.assertEqual(followup.maintenance_type, "corrective")
