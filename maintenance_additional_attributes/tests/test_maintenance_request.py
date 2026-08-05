# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestMaintenanceRequest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stage_open = cls.env["maintenance.stage"].create(
            {"name": "Test Open", "sequence": 100}
        )
        cls.stage_done = cls.env["maintenance.stage"].create(
            {"name": "Test Done", "sequence": 110, "done": True}
        )
        cls.team = cls.env["maintenance.team"].create({"name": "Test Team"})
        cls.technician = cls.env["res.users"].create(
            {"name": "Test Technician", "login": "test_technician"}
        )
        cls.activity_type = cls.env.ref(
            "maintenance_additional_attributes.mail_act_maintenance_alert"
        )
        cls.close_date = fields.Date.to_date("2026-07-20")

    def _create_request(self, **vals):
        """Create a request that is due for an alert, unless overridden."""
        return self.env["maintenance.request"].create(
            {
                "name": "Test Request",
                "maintenance_team_id": self.team.id,
                "stage_id": self.stage_open.id,
                "user_id": self.technician.id,
                "schedule_date": fields.Datetime.now() + relativedelta(days=10),
                "alert_period": 1,
                "alert_period_unit": "month",
                **vals,
            }
        )

    def _run_cron(self, request):
        self.env["maintenance.request"]._cron_send_maintenance_alerts()
        return request.activity_ids.filtered(
            lambda activity: activity.activity_type_id == self.activity_type
        )

    def test_close_date_kept_before_completion(self):
        """The close date can be recorded while the request is still open."""
        self.assertEqual(
            self._create_request(close_date=self.close_date).close_date,
            self.close_date,
        )

    def test_close_date_kept_on_completion(self):
        """Completing the request must not overwrite the recorded date."""
        request = self._create_request(close_date=self.close_date)
        request.stage_id = self.stage_done
        self.assertEqual(request.close_date, self.close_date)

    def test_close_date_defaults_to_today_on_completion(self):
        """Without a recorded date, the standard behavior still applies."""
        request = self._create_request()
        request.stage_id = self.stage_done
        self.assertEqual(request.close_date, fields.Date.today())

    def test_alert_sent_once_within_period(self):
        request = self._create_request()
        self.assertTrue(self._run_cron(request))
        self.assertTrue(request.alert_sent)
        self.assertEqual(len(self._run_cron(request)), 1)

    def test_alert_not_sent_outside_period(self):
        request = self._create_request(
            schedule_date=fields.Datetime.now() + relativedelta(days=60)
        )
        self.assertFalse(self._run_cron(request))
        self.assertFalse(request.alert_sent)

    def test_alert_reset_on_schedule_date_change(self):
        request = self._create_request()
        self._run_cron(request)
        request.schedule_date = fields.Datetime.now() + relativedelta(days=60)
        self.assertFalse(request.alert_sent)
        self.assertFalse(
            request.activity_ids.filtered(
                lambda activity: activity.activity_type_id == self.activity_type
            )
        )

    def test_alert_assigned_to_technician(self):
        self.assertEqual(
            self._run_cron(self._create_request()).user_id, self.technician
        )

    def test_alert_falls_back_to_equipment_technician(self):
        """A technician assigned to the equipment after the request was
        created is not propagated by the standard compute."""
        equipment = self.env["maintenance.equipment"].create({"name": "Test Equipment"})
        request = self._create_request(equipment_id=equipment.id, user_id=False)
        equipment.technician_user_id = self.technician
        self.assertFalse(request.user_id)
        self.assertEqual(self._run_cron(request).user_id, self.technician)

    def test_alert_not_sent_without_technician(self):
        """The alert waits until a technician is assigned."""
        request = self._create_request(user_id=False)
        self.assertFalse(self._run_cron(request))
        self.assertFalse(request.alert_sent)
