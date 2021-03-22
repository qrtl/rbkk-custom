# Copyright 2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ProductLabelReports(models.AbstractModel):
    _name = "report.product_label_template.product_label_reports"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_name = "product_label_template.product_label_reports"
        report = self.env["ir.actions.report"]._get_report_from_name(report_name)
        lots = self.env["mrp.production"].browse(docids).mapped("new_lot_id")
        paper_format = (
            lots.mapped("product_id")
            .mapped("product_label_template_ids")
            .mapped("paperformat_id")
        )
        report.paperformat_id = paper_format[0] if paper_format else False
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "lots": lots,
        }
