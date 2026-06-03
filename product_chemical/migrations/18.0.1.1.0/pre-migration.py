# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# Replace the legacy product.chemical.cas master with the new
# product.chemical.substance master. The new master has a separate name field
# in addition to CAS No. and a default content rate, so we drop the legacy
# tables and let Odoo recreate them. Any existing line data is discarded; the
# previous schema was only used for early prototyping.


def migrate(cr, version):
    cr.execute("DROP TABLE IF EXISTS product_chemical_cas_line CASCADE")
    cr.execute("DROP TABLE IF EXISTS product_chemical_cas CASCADE")
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = 'product_chemical'
           AND model IN (
               'product.chemical.cas',
               'product.chemical.cas.line'
           )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_fields
         WHERE model IN (
             'product.chemical.cas',
             'product.chemical.cas.line'
         )
            OR relation IN (
             'product.chemical.cas',
             'product.chemical.cas.line'
         )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model
         WHERE model IN (
             'product.chemical.cas',
             'product.chemical.cas.line'
         )
        """
    )
