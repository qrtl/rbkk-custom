# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet.sheet"

    def button_add_line(self):
        for rec in self:
            if rec.add_line_project_id and not rec.add_line_task_id:
                raise UserError(_("Please select a task before adding a line."))
        return super().button_add_line()
