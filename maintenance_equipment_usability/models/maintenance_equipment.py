# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    status = fields.Selection(
        selection=[
            ("preparing", "Preparing"),
            ("operating", "Operating"),
            ("idle", "Idle"),
            ("retired", "Retired"),
            ("scrapped", "Scrapped"),
        ],
        default="preparing",
    )
    maintenance_exempt = fields.Boolean(
        string="Maintenance Not Required",
        help="If set, maintenance request results are ignored when computing "
        "usability: the equipment is usable as long as it is in the Operating "
        "status.",
    )
    usability_state = fields.Selection(
        selection=[
            ("unknown", "Unknown"),
            ("usable", "Usable"),
            ("unusable", "Unusable"),
        ],
        compute="_compute_usability",
        search="_search_usability_state",
        string="Usability",
    )
    latest_maintenance_result_request_id = fields.Many2one(
        comodel_name="maintenance.request",
        compute="_compute_latest_maintenance_result",
        store=True,
        readonly=True,
        string="Latest Result Request",
    )
    latest_maintenance_result_date = fields.Date(
        compute="_compute_latest_maintenance_result",
        store=True,
        readonly=True,
        string="Latest Result Date",
    )

    @api.depends(
        "maintenance_ids.close_date",
        "maintenance_ids.request_date",
        "maintenance_ids.stage_id.done",
        "maintenance_ids.maintenance_result",
        "maintenance_ids.archive",
    )
    def _compute_latest_maintenance_result(self):
        requests = (
            self.env["maintenance.request"]
            .sudo()
            .search(
                [
                    ("equipment_id", "in", self.ids),
                    ("stage_id.done", "=", True),
                    ("maintenance_result", "in", ("passed", "failed")),
                    ("archive", "=", False),
                ],
                order="equipment_id, close_date desc, request_date desc, id desc",
            )
        )
        latest_by_equipment = {}
        for request in requests:
            latest_by_equipment.setdefault(request.equipment_id.id, request)
        for equipment in self:
            request = latest_by_equipment.get(equipment.id)
            equipment.latest_maintenance_result_request_id = request
            equipment.latest_maintenance_result_date = (
                (request.close_date or request.request_date) if request else False
            )

    @api.depends(
        "company_id",
        "status",
        "maintenance_exempt",
        "latest_maintenance_result_request_id.maintenance_result",
        "latest_maintenance_result_date",
    )
    def _compute_usability(self):
        today = fields.Date.context_today(self)
        for equipment in self:
            if equipment.status != "operating":
                equipment.usability_state = "unusable"
                continue
            if equipment.maintenance_exempt:
                # Maintenance results are not evaluated for exempt equipment.
                equipment.usability_state = "usable"
                continue
            request = equipment.latest_maintenance_result_request_id
            result_date = equipment.latest_maintenance_result_date
            if not request or not result_date:
                equipment.usability_state = "unknown"
                continue
            if request.maintenance_result == "failed":
                equipment.usability_state = "unusable"
                continue
            company = equipment.company_id or self.env.company
            grace_months = company.usability_grace_period_months
            if today > result_date + relativedelta(months=grace_months, day=31):
                # Validity extends to the end of the target month.
                equipment.usability_state = "unusable"
            else:
                equipment.usability_state = "usable"

    def _search_usability_state(self, operator, value):
        all_states = ("unknown", "usable", "unusable")
        if operator == "=":
            states = [value] if value in all_states else []
        elif operator == "!=":
            states = [s for s in all_states if s != value]
        elif operator == "in":
            states = [s for s in value if s in all_states]
        elif operator == "not in":
            states = [s for s in all_states if s not in value]
        else:
            states = []
        if not states:
            return [("id", "=", False)]
        result = "latest_maintenance_result_request_id.maintenance_result"
        # Validity extends to the end of the target month, so the earliest
        # still-valid result date is the first day of its month.
        threshold = fields.Date.context_today(self).replace(day=1) - relativedelta(
            months=self.env.company.usability_grace_period_months
        )
        domains = {
            # unknown: operating and not exempt, but no completed result yet
            "unknown": [
                "&",
                ("status", "=", "operating"),
                "&",
                ("maintenance_exempt", "=", False),
                ("latest_maintenance_result_request_id", "=", False),
            ],
            # usable: operating and either exempt, or the latest result passed
            # within the grace period
            "usable": [
                "&",
                ("status", "=", "operating"),
                "|",
                ("maintenance_exempt", "=", True),
                "&",
                (result, "=", "passed"),
                ("latest_maintenance_result_date", ">=", threshold),
            ],
            # unusable: not operating, or not exempt with a failed result or a
            # passed result past the grace period
            "unusable": [
                "|",
                ("status", "!=", "operating"),
                "&",
                ("maintenance_exempt", "=", False),
                "|",
                (result, "=", "failed"),
                "&",
                (result, "=", "passed"),
                ("latest_maintenance_result_date", "<", threshold),
            ],
        }
        domain = domains[states[0]]
        for state in states[1:]:
            domain = ["|"] + domain + domains[state]
        return domain
