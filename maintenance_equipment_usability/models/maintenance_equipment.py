# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.osv import expression


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
        tracking=True,
    )
    maintenance_exempt = fields.Boolean(
        string="Maintenance Not Required",
        tracking=True,
        help="If set, maintenance request results are ignored when computing "
        "usability: the equipment is usable as long as it is in the Operating "
        "status.",
    )
    warranty_date = fields.Date(tracking=True)
    usability_state = fields.Selection(
        selection=[
            ("unknown", "Unknown"),
            ("usable", "Usable"),
            ("unusable", "Unusable"),
        ],
        compute="_compute_usability_state",
        search="_search_usability_state",
        string="Usability",
    )
    usable_until = fields.Date(
        compute="_compute_usable_until",
        store=True,
        help="Last day the equipment is usable on the strength of its warranty "
        "or its latest passed maintenance result, whichever is later. Empty "
        "when neither applies or the latest result is Failed. The equipment "
        "must also be in the Operating status to be usable.",
    )
    latest_maintenance_result_request_id = fields.Many2one(
        comodel_name="maintenance.request",
        compute="_compute_latest_maintenance_result",
        store=True,
        string="Latest Result Request",
    )
    latest_maintenance_result_date = fields.Date(
        compute="_compute_latest_maintenance_result",
        store=True,
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
                ]
            )
        )
        # Rank on the date the result counts from (close date, else request
        # date), in Python: ordering on close_date in SQL would put requests
        # without one first.
        latest_by_equipment = {}
        for request in requests.sorted(
            lambda r: (
                r.close_date or r.request_date or date.min,
                r.request_date or date.min,
                r.id,
            ),
            reverse=True,
        ):
            latest_by_equipment.setdefault(request.equipment_id.id, request)
        for equipment in self:
            request = latest_by_equipment.get(equipment.id)
            equipment.latest_maintenance_result_request_id = request
            equipment.latest_maintenance_result_date = (
                (request.close_date or request.request_date) if request else False
            )

    @api.depends(
        "company_id.usability_validity_months",
        "latest_maintenance_result_request_id.company_id.usability_validity_months",
        "warranty_date",
        "latest_maintenance_result_request_id.maintenance_result",
        "latest_maintenance_result_date",
    )
    def _compute_usable_until(self):
        for equipment in self:
            request = equipment.latest_maintenance_result_request_id
            if request.maintenance_result == "failed":
                equipment.usable_until = False
                continue
            dates = []
            if equipment.warranty_date:
                dates.append(equipment.warranty_date)
            result_date = equipment.latest_maintenance_result_date
            if request and result_date:
                # Equipment without a company (shared across companies) takes
                # the period of the company of its latest result.
                company = equipment.company_id or request.company_id
                # Validity extends to the end of the target month.
                dates.append(
                    result_date
                    + relativedelta(months=company.usability_validity_months, day=31)
                )
            equipment.usable_until = max(dates) if dates else False

    @api.depends(
        "status",
        "scrap_date",
        "maintenance_exempt",
        "usable_until",
        "latest_maintenance_result_request_id",
    )
    def _compute_usability_state(self):
        today = fields.Date.context_today(self)
        for equipment in self:
            if equipment.status != "operating" or (
                equipment.scrap_date and equipment.scrap_date <= today
            ):
                # Scrapped equipment is unusable whatever its status says; a
                # future scrap date leaves it usable until that day.
                equipment.usability_state = "unusable"
            elif equipment.maintenance_exempt or (
                equipment.usable_until and equipment.usable_until >= today
            ):
                equipment.usability_state = "usable"
            elif equipment.latest_maintenance_result_request_id:
                equipment.usability_state = "unusable"
            else:
                equipment.usability_state = "unknown"

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
            return expression.FALSE_DOMAIN
        today = fields.Date.context_today(self)
        # Implicitly ANDed term lists, so they can be spliced together.
        operating = [
            ("status", "=", "operating"),
            "|",
            ("scrap_date", "=", False),
            ("scrap_date", ">", today),
        ]
        not_valid = [
            ("maintenance_exempt", "=", False),
            "|",
            ("usable_until", "=", False),
            ("usable_until", "<", today),
        ]
        has_result = ("latest_maintenance_result_request_id", "!=", False)
        no_result = ("latest_maintenance_result_request_id", "=", False)
        domains = {
            "usable": [
                *operating,
                "|",
                ("maintenance_exempt", "=", True),
                ("usable_until", ">=", today),
            ],
            "unknown": [*operating, *not_valid, no_result],
            "unusable": expression.OR(
                [
                    [("status", "!=", "operating")],
                    [("scrap_date", "<=", today)],
                    [has_result, *not_valid],
                ]
            ),
        }
        return expression.OR([domains[state] for state in states])
