# Copyright 2021 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    use_plt_paperformat = fields.Boolean("Use Product Label Template Paperformat")
    plt_paperformat_type = fields.Selection(
        selection=[("main", "Main")],
        string="Product Label Template Paperformat Type",
    )

    def get_paperformat(self):
        if self.use_plt_paperformat and self.env.context.get("plt_paperformat"):
            return self.env.context.get("plt_paperformat")
        return super().get_paperformat()

    @api.model
    def _get_product_for_active_rec(self, active_rec):
        """Return the product used to look up the product label template.

        Extend this method to support models other than ``stock.lot``.
        """
        if active_rec._name == "stock.lot":
            return active_rec.product_id
        return False

    def _get_plt_paperformat(self, res_ids, plt_paperformat_type):
        """Return the paperformat from the relevant product label template."""
        active_rec = self.env[self.model].browse(res_ids)[:1]
        if not active_rec:
            return False
        product = self._get_product_for_active_rec(active_rec)
        if not product:
            return False
        plt_rec = self.env["product.label.template"].search(
            [("product_id", "=", product.id)], limit=1
        )
        if not plt_rec:
            return False
        if plt_paperformat_type == "main":
            return plt_rec.paperformat_id

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.use_plt_paperformat and report.plt_paperformat_type:
            plt_paperformat = report._get_plt_paperformat(
                res_ids, report.plt_paperformat_type
            )
            if plt_paperformat:
                self = self.with_context(plt_paperformat=plt_paperformat)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
