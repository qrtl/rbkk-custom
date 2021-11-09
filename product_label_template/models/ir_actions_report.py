# Copyright 2021 Quartile Limited

from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    use_plt_paperformat = fields.Boolean("Use Product Label Template Paperformat")
    plt_paperformat_type = fields.Selection(
        selection=[("main", "Main"), ("qr", "QR Only")],
        string="Product Label Template Paperformat Type",
    )

    @api.model
    def get_paperformat(self):
        if self._context.get("plt_paperformat"):
            return self._context.get("plt_paperformat")
        return super().get_paperformat()

    @api.model
    def _get_product_for_active_rec(self, active_rec):
        """This method is expected to be extended by modules with the print function."""
        return False

    @api.model
    def _get_plt_paperformat(self, res_ids, plt_paperformat_type):
        """Return the paperformat from the relevant product label template."""
        active_rec = self.env[self.model].browse(res_ids)[:1]
        if not active_rec:
            return False
        product = self._get_product_for_active_rec(active_rec)
        if not product:
            return False
        plt_rec = self.env["product.label.template"].search(
            [("product_id", "=", product.id)]
        )[:1]
        if not plt_rec:
            return False
        if plt_paperformat_type == "main":
            return plt_rec.paperformat_id
        if plt_paperformat_type == "qr":
            return plt_rec.qr_paperformat_id

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        if self.use_plt_paperformat and self.plt_paperformat_type:
            plt_paperformat = self._get_plt_paperformat(
                res_ids, self.plt_paperformat_type
            )
            if plt_paperformat:
                self = self.with_context(plt_paperformat=plt_paperformat)
        return super().render_qweb_pdf(res_ids=res_ids, data=data)
