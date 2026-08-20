This module adds chemical substance management to products. When the "Chemical"
flag on a product is enabled, a "Chemical" tab is shown that allows users to:

* Attach one or more applicable laws to the product (with optional major /
  minor category per law).
* Upload a risk assessment sheet (PDF).
* Register CAS Numbers contained in the product together with their content
  rate (%).
* Review the component amount per stock location, calculated from on-hand
  quantity multiplied by each CAS content rate. The amount is expressed in the
  stock unit of measure of the product, which is shown next to the quantity.
  As products are managed in different units of measure, no total across
  units is displayed; group the report by unit of measure to obtain
  meaningful subtotals.

Master data managed by this module:

* **Laws** — referenced by products; each law lists the products that use it.
* **Major / Minor categories** — organised under their parent law.
* **CAS Numbers** — reusable across products.

Products can be searched by CAS Number from the product search view.
