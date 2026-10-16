# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import new_test_user

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

    def _create_request(
        self, stage, result="none", request_date=None, close_date=None, equipment=None
    ):
        vals = {
            "name": f"Request {stage.name}",
            "equipment_id": (equipment or self.equipment).id,
            "stage_id": stage.id,
            "request_date": request_date or self.today,
            "maintenance_result": result,
        }
        if close_date:
            vals["close_date"] = close_date
        return self.env["maintenance.request"].create(vals)

    def test_usability_state_and_search(self):
        """Each scenario gets its computed state checked, and the search must
        return exactly the matching scenarios for every operator."""
        today = self.today
        tomorrow = today + relativedelta(days=1)
        yesterday = today - relativedelta(days=1)
        # Equipment values
        idle = {"status": "idle"}
        exempt = {"maintenance_exempt": True}
        warranty = {"warranty_date": today + relativedelta(months=1)}
        # Requests as (result, close date); no close date means not completed
        passed = ("passed", today - relativedelta(months=1))
        passed_expired = ("passed", today - relativedelta(months=13))
        failed = ("failed", today)
        pending = ("passed", None)
        scenarios = [
            ("no result", {}, None, "unknown"),
            ("result not completed", {}, pending, "unknown"),
            ("passed", {}, passed, "usable"),
            ("passed, expired", {}, passed_expired, "unusable"),
            ("failed", {}, failed, "unusable"),
            ("not operating", idle, passed, "unusable"),
            ("exempt, failed", exempt, failed, "usable"),
            ("exempt, no result", exempt, None, "usable"),
            ("exempt, not operating", {**exempt, **idle}, None, "unusable"),
            ("warranty until today", {"warranty_date": today}, None, "usable"),
            ("warranty expired", {"warranty_date": yesterday}, None, "unknown"),
            ("warranty, passed expired", warranty, passed_expired, "usable"),
            ("warranty, failed", warranty, failed, "unusable"),
            ("scrap planned", {"scrap_date": tomorrow}, passed, "usable"),
            ("scrapped", {"scrap_date": today}, passed, "unusable"),
            ("scrapped, exempt", {**exempt, "scrap_date": today}, None, "unusable"),
        ]
        Equipment = self.env["maintenance.equipment"]
        expected = {}
        for name, vals, request, state in scenarios:
            equipment = Equipment.create({"name": name, "status": "operating", **vals})
            if request:
                result, close_date = request
                stage = self.done_stage if close_date else self.open_stage
                self._create_request(
                    stage, result, close_date=close_date, equipment=equipment
                )
            with self.subTest(scenario=name):
                self.assertEqual(equipment.usability_state, state)
            expected[equipment] = state
        equipments = Equipment.concat(*expected)
        for operator, value, states in [
            ("=", "usable", {"usable"}),
            ("=", "unusable", {"unusable"}),
            ("=", "unknown", {"unknown"}),
            ("!=", "usable", {"unusable", "unknown"}),
            ("in", ["usable", "unknown"], {"usable", "unknown"}),
            ("not in", ["unknown"], {"usable", "unusable"}),
        ]:
            with self.subTest(operator=operator, value=value):
                found = Equipment.search(
                    [("id", "in", equipments.ids), ("usability_state", operator, value)]
                )
                matching = [e for e, state in expected.items() if state in states]
                self.assertEqual(found, Equipment.concat(*matching))

    def test_latest_result(self):
        """Latest by close date, else request date; archived requests ignored."""
        passed = self._create_request(
            self.done_stage,
            result="passed",
            close_date=self.today - relativedelta(months=1),
        )
        failed = self._create_request(
            self.done_stage, result="failed", close_date=self.today
        )
        self.assertEqual(self.equipment.latest_maintenance_result_request_id, failed)
        self.assertEqual(self.equipment.latest_maintenance_result_date, self.today)
        failed.archive = True
        self.assertEqual(self.equipment.latest_maintenance_result_request_id, passed)
        # A cleared close date ranks by request date, not first.
        old = self._create_request(
            self.done_stage,
            result="failed",
            request_date=self.today - relativedelta(months=6),
            close_date=self.today - relativedelta(months=6),
        )
        old.close_date = False
        self.assertEqual(self.equipment.latest_maintenance_result_request_id, passed)

    def test_usable_until(self):
        self.assertFalse(self.equipment.usable_until)
        close = fields.Date.to_date("2026-06-15")
        self._create_request(self.done_stage, result="passed", close_date=close)
        # 12 months from a 15 June result, extended to the end of the month.
        self.assertEqual(self.equipment.usable_until, fields.Date.to_date("2027-06-30"))
        # A later warranty expiration date wins.
        self.equipment.warranty_date = "2027-09-01"
        self.assertEqual(self.equipment.usable_until, fields.Date.to_date("2027-09-01"))
        # An earlier one does not shorten the result's validity.
        self.equipment.warranty_date = "2027-01-01"
        self.assertEqual(self.equipment.usable_until, fields.Date.to_date("2027-06-30"))
        # A failed result clears it, even under warranty.
        self.equipment.warranty_date = "2099-01-01"
        self._create_request(
            self.done_stage, result="failed", close_date=close + relativedelta(days=1)
        )
        self.assertFalse(self.equipment.usable_until)

    def test_validity_follows_company_setting(self):
        """The period of the equipment's company applies, else that of its
        latest result's company; usable_until follows changes to it."""
        close = self.today - relativedelta(months=13)
        self._create_request(self.done_stage, result="passed", close_date=close)
        self.assertEqual(self.equipment.usability_state, "unusable")
        self.env.company.usability_validity_months = 14
        self.assertEqual(
            self.equipment.usable_until, close + relativedelta(months=14, day=31)
        )
        self.assertEqual(self.equipment.usability_state, "usable")
        with self.assertRaises(ValidationError):
            self.env.company.usability_validity_months = 0
        company_b = self.env["res.company"].create(
            {"name": "Company B", "usability_validity_months": 24}
        )
        team_b = self.env["maintenance.team"].create(
            {"name": "Team B", "company_id": company_b.id}
        )
        shared = self.env["maintenance.equipment"].create(
            {"name": "Shared", "status": "operating", "company_id": False}
        )
        self.env["maintenance.request"].create(
            {
                "name": "Company B Request",
                "equipment_id": shared.id,
                "company_id": company_b.id,
                "maintenance_team_id": team_b.id,
                "stage_id": self.done_stage.id,
                "close_date": close,
                "maintenance_result": "passed",
            }
        )
        self.assertEqual(shared.usable_until, close + relativedelta(months=24, day=31))
        company_b.usability_validity_months = 6
        self.assertEqual(shared.usable_until, close + relativedelta(months=6, day=31))

    def test_result_required_on_completion(self):
        request = self._create_request(self.open_stage)
        with self.assertRaises(ValidationError):
            request.write({"stage_id": self.done_stage.id})
        with self.assertRaises(ValidationError):
            self._create_request(self.done_stage)
        request.write({"stage_id": self.done_stage.id, "maintenance_result": "passed"})
        with self.assertRaises(ValidationError):
            request.maintenance_result = "none"
        # Not required for exempt equipment, nor for requests without equipment.
        self.equipment.maintenance_exempt = True
        self._create_request(self.done_stage)
        self.env["maintenance.request"].create(
            {"name": "No equipment", "stage_id": self.done_stage.id}
        )

    def test_create_followup_request(self):
        request = self._create_request(
            self.done_stage, result="failed", close_date=self.today
        )
        company_b = self.env["res.company"].create({"name": "Company B"})
        self.env.user.company_ids |= company_b
        # The request's company is kept, not the current one.
        request.with_context(
            allowed_company_ids=[company_b.id, request.company_id.id]
        ).action_create_followup_request()
        followup = request.followup_request_ids
        self.assertEqual(followup.source_request_id, request)
        self.assertEqual(followup.equipment_id, self.equipment)
        self.assertEqual(followup.maintenance_type, "corrective")
        self.assertEqual(followup.company_id, request.company_id)

    def test_followup_request_only_once(self):
        """A second follow-up is refused, also for a user whom record rules
        hide the existing follow-up from."""
        user = new_test_user(self.env, login="mu_tech", groups="base.group_user")
        request = self._create_request(
            self.done_stage, result="failed", close_date=self.today
        )
        request.user_id = user
        # Created by another user: neither owned nor followed by the technician.
        request.action_create_followup_request()
        followup = request.followup_request_ids
        followup.message_unsubscribe(partner_ids=user.partner_id.ids)
        self.assertNotIn(user, followup.user_id | followup.owner_user_id)
        as_user = request.with_user(user)
        # Read from the database, as the form does: record rules filter the
        # follow-up out, while the sudo-computed flag still sees it.
        as_user.invalidate_recordset()
        values = as_user.read(["followup_request_ids", "has_followup_request"])[0]
        self.assertFalse(values["followup_request_ids"])
        self.assertTrue(values["has_followup_request"])
        with self.assertRaises(UserError):
            as_user.action_create_followup_request()
        # Nor can a follow-up be created from a request that did not fail.
        passed = self._create_request(
            self.done_stage, result="passed", close_date=self.today
        )
        with self.assertRaises(UserError):
            passed.action_create_followup_request()

    def test_close_date(self):
        """A recorded date is kept until reopening; none in the future."""
        recorded = self.today - relativedelta(days=3)
        request = self._create_request(self.open_stage, close_date=recorded)
        request.stage_id = self.env.ref("maintenance.stage_1")
        request.write({"stage_id": self.done_stage.id, "maintenance_result": "passed"})
        self.assertEqual(request.close_date, recorded)
        request.stage_id = self.open_stage
        self.assertFalse(request.close_date)
        request.stage_id = self.done_stage
        self.assertEqual(request.close_date, self.today)
        with self.assertRaises(ValidationError):
            request.close_date = self.today + relativedelta(days=1)

    def test_close_date_in_user_timezone(self):
        """Completing at 08:00 JST on 1 July (still 30 June in UTC) dates the
        result 1 July, so its validity runs to the end of the next July."""
        self.env.user.tz = "Asia/Tokyo"
        request = self._create_request(self.open_stage)
        with freeze_time(datetime(2026, 6, 30, 23, 0)):
            request.write(
                {"stage_id": self.done_stage.id, "maintenance_result": "passed"}
            )
            created = self._create_request(self.done_stage, result="passed")
        self.assertEqual(request.close_date, fields.Date.to_date("2026-07-01"))
        self.assertEqual(created.close_date, fields.Date.to_date("2026-07-01"))
        self.assertEqual(self.equipment.usable_until, fields.Date.to_date("2027-07-31"))
