from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _get_quants_action(self, domain=None, extend=False):
        action = super()._get_quants_action(domain=domain, extend=extend)
        if self.env.user.has_group("stock.group_stock_manager"):
            return action
        if not self.env.user.has_group(
            "stock_location_report_manager_layout.group_readonly_manager_layout"
        ):
            return action

        readonly_view = self.env.ref(
            "stock_location_report_manager_layout.view_stock_quant_tree_readonly_manager_layout"
        )
        action["view_id"] = readonly_view.id
        action["views"] = [(readonly_view.id, "list")] + [
            (view_id, view_type)
            for view_id, view_type in action.get("views", [])
            if view_type != "list"
        ]
        return action
