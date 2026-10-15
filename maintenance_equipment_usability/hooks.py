# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields


def post_init_hook(env):
    """Give equipment that exists before install a status matching its use.

    The status column is otherwise filled with its default, Preparing, which
    would make every piece of equipment already in service unusable.
    """
    equipments = env["maintenance.equipment"].with_context(active_test=False)
    today = fields.Date.context_today(equipments)
    # A future scrap date is planned: the equipment is still in service.
    equipments.search([("scrap_date", "<=", today)]).status = "scrapped"
    equipments.search(
        ["|", ("scrap_date", "=", False), ("scrap_date", ">", today)]
    ).status = "operating"
