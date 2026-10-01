# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplateChemicalDocument(models.Model):
    _name = "product.template.chemical.document"
    _description = "Product Chemical Document"
    _order = "sequence, id"

    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product",
        required=True,
        ondelete="cascade",
        index=True,
    )
    document_type = fields.Selection(
        [("sds", "SDS"), ("risk_assessment", "Risk Assessment Sheet")],
        string="Category",
        required=True,
        default="sds",
    )
    sequence = fields.Integer(default=10)
    file = fields.Binary(required=True, attachment=True)
    filename = fields.Char()
    is_pdf = fields.Boolean(string="PDF", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_is_pdf()
        return records

    def _update_is_pdf(self):
        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
                ("res_field", "=", "file"),
                ("mimetype", "=", "application/pdf"),
            ]
        )
        self.browse(attachments.mapped("res_id")).is_pdf = True

    def action_open(self):
        """Show the PDF file in a new browser tab.

        The browser only displays the file itself when it is served inline,
        which is what /web/content does without download=true.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{self._name}/{self.id}/file?filename_field=filename",
            "target": "new",
        }
