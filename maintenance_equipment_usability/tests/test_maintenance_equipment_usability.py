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

    def test_maintenance_exempt_ignores_maintenance_result(self):
        self._create_request(self.done_stage, result="failed", close_date=self.today)
        self.assertEqual(self.equipment.usability_state, "unusable")
        # The maintenance result is not evaluated for exempt equipment.
        self.equipment.maintenance_exempt = True
        self.assertEqual(self.equipment.usability_state, "usable")
        # The status still gates usability.
        self.equipment.status = "idle"
        self.assertEqual(self.equipment.usability_state, "unusable")

    def test_maintenance_exempt_without_result_is_usable(self):
        # Without the flag the equipment usability is unknown.
        self.assertEqual(self.equipment.usability_state, "unknown")
        self.equipment.maintenance_exempt = True
        self.assertEqual(self.equipment.usability_state, "usable")

    def test_search_usability_state_with_maintenance_exempt(self):
        exempt_equipment = self.env["maintenance.equipment"].create(
            {
                "name": "Exempt Equipment",
                "status": "operating",
                "maintenance_exempt": True,
            }
        )
        self.env["maintenance.request"].create(
            {
                "name": "Exempt Request",
                "equipment_id": exempt_equipment.id,
                "stage_id": self.done_stage.id,
                "request_date": self.today,
                "close_date": self.today,
                "maintenance_result": "failed",
            }
        )
        usable = self.env["maintenance.equipment"].search(
            [("usability_state", "=", "usable")]
        )
        unusable = self.env["maintenance.equipment"].search(
            [("usability_state", "=", "unusable")]
        )
        unknown = self.env["maintenance.equipment"].search(
            [("usability_state", "=", "unknown")]
        )
        self.assertIn(exempt_equipment, usable)
        self.assertNotIn(exempt_equipment, unusable)
        self.assertNotIn(exempt_equipment, unknown)

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

    def test_search_usability_state_operators(self):
        self._create_request(
            self.done_stage,
            result="passed",
            close_date=self.today - relativedelta(months=1),
        )
        unknown_equipment = self.env["maintenance.equipment"].create(
            {"name": "Unknown Equipment", "status": "operating"}
        )
        Equipment = self.env["maintenance.equipment"]
        unknown = Equipment.search([("usability_state", "=", "unknown")])
        self.assertIn(unknown_equipment, unknown)
        self.assertNotIn(self.equipment, unknown)
        not_usable = Equipment.search([("usability_state", "!=", "usable")])
        self.assertIn(unknown_equipment, not_usable)
        self.assertNotIn(self.equipment, not_usable)
        usable_or_unknown = Equipment.search(
            [("usability_state", "in", ["usable", "unknown"])]
        )
        self.assertIn(self.equipment, usable_or_unknown)
        self.assertIn(unknown_equipment, usable_or_unknown)
        not_unknown = Equipment.search([("usability_state", "not in", ["unknown"])])
        self.assertIn(self.equipment, not_unknown)
        self.assertNotIn(unknown_equipment, not_unknown)

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

    def test_followup_request_keeps_company(self):
        request = self._create_request(
            self.done_stage, result="failed", close_date=self.today
        )
        company_b = self.env["res.company"].create({"name": "Company B"})
        self.env.user.company_ids |= company_b
        request.with_context(
            allowed_company_ids=[company_b.id, request.company_id.id]
        ).action_create_followup_request()
        self.assertEqual(request.followup_request_ids.company_id, request.company_id)

    def test_in_warranty_without_result_is_usable(self):
        self.equipment.warranty_date = self.today
        self.assertEqual(self.equipment.usability_state, "usable")
        self.equipment.warranty_date = self.today - relativedelta(days=1)
        self.assertEqual(self.equipment.usability_state, "unknown")

    def test_in_warranty_passed_past_grace_is_usable(self):
        self._create_request(
            self.done_stage,
            result="passed",
            close_date=self.today - relativedelta(months=13),
        )
        self.assertEqual(self.equipment.usability_state, "unusable")
        self.equipment.warranty_date = self.today + relativedelta(months=1)
        self.assertEqual(self.equipment.usability_state, "usable")

    def test_in_warranty_failed_is_unusable(self):
        self.equipment.warranty_date = self.today + relativedelta(months=1)
        self._create_request(self.done_stage, result="failed", close_date=self.today)
        self.assertEqual(self.equipment.usability_state, "unusable")

    def test_in_warranty_not_operating_is_unusable(self):
        self.equipment.warranty_date = self.today + relativedelta(months=1)
        self.equipment.status = "idle"
        self.assertEqual(self.equipment.usability_state, "unusable")

    def test_search_usability_state_with_warranty(self):
        Equipment = self.env["maintenance.equipment"]
        in_warranty = Equipment.create(
            {
                "name": "In Warranty",
                "status": "operating",
                "warranty_date": self.today + relativedelta(months=1),
            }
        )
        expired = Equipment.create(
            {
                "name": "Warranty Expired",
                "status": "operating",
                "warranty_date": self.today - relativedelta(days=1),
            }
        )
        failed = Equipment.create(
            {
                "name": "Failed In Warranty",
                "status": "operating",
                "warranty_date": self.today + relativedelta(months=1),
            }
        )
        self.env["maintenance.request"].create(
            {
                "name": "Failed Request",
                "equipment_id": failed.id,
                "stage_id": self.done_stage.id,
                "request_date": self.today,
                "close_date": self.today,
                "maintenance_result": "failed",
            }
        )
        for state in ("usable", "unusable", "unknown"):
            found = Equipment.search([("usability_state", "=", state)])
            for equipment in (in_warranty, expired, failed):
                self.assertEqual(equipment in found, equipment.usability_state == state)
        self.assertEqual(in_warranty.usability_state, "usable")
        self.assertEqual(expired.usability_state, "unknown")
        self.assertEqual(failed.usability_state, "unusable")
