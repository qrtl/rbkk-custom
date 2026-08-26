This module adds chemical substance management to products. When the "Chemical"
flag on a product is enabled, a "Chemical" tab is shown that allows users to:

* Attach one or more applicable laws to the product (with optional major /
  minor category per law).
* Upload a risk assessment sheet (PDF).
* Register CAS Numbers contained in the product together with their content
  rate (%).
* Review the component amount per stock location, calculated from on-hand
  quantity multiplied by each CAS content rate.

Master data managed by this module:

* **Laws** — referenced by products; each law lists the products that use it.
* **Major / Minor categories** — organised under their parent law.
* **CAS Numbers** — reusable across products.

Products can be searched by CAS Number from the product search view.

## Aggregation units

Products holding the same substance are rarely measured in the same unit, so
component amounts have to be converted before they can be added up. Each unit
of measure category therefore carries a **Chemical Aggregation UoM**: component
amounts of every product in that category are converted into it, which keeps
each total expressed in a single unit and keeps amounts of a different kind
(weight versus volume) in separate totals.

Set it on the unit of measure category, for instance kilograms for *Weight* and
litres for *Volume*. Note that a coarse unit makes trace amounts round away in
the report — pick the smallest unit in use if the products are measured in
milligrams or microlitres.

Leaving a category without an aggregation unit turns conversion off for it: the
amounts are still listed, unconverted, but they no longer join the weight or
volume totals. That is what count-managed products need, since a percentage of a
piece count is not a meaningful quantity.

The **Chemicals by Location** report groups by aggregation unit first for this
reason, and offers an *Aggregated Only* filter to hide the categories that have
none.

## Chemical movements

Validating a stock move of a chemical product records how much of each
contained substance was moved, one record per substance, listed in the
**Chemical Movements** report. Amounts are converted into the aggregation unit
in the same way as the on-hand report, and are signed: positive for a receipt
into an internal location, negative for a delivery out of one. A move between
two internal locations is recorded as an internal transfer and left out of the
totals by default, since it changes no handled amount; a move that never
touches an internal location, such as a drop shipping, is not recorded at all.

Unlike the on-hand report, these records are a snapshot: they keep the content
rate that applied when the move was validated, so revising the composition of a
product does not rewrite what was handled in the past. An inventory manager can
still correct a record from its form view when the composition was wrong at the
time, and the amount is recalculated from the corrected rate.

The **Update Chemical Amounts** action, available to inventory managers from
the stock move list and from the Chemical Movements list, records the
movements of moves that were validated before the module was installed, and
rebuilds them when the composition of a product was registered wrongly. The
rebuild replaces the records of the whole move, so a substance added to or
removed from the product is reflected too — which also means the manual
corrections made on those records are lost. Bear in mind that a rebuild applies
the composition registered *today*: it cannot restore a rate that was correct
at the time of the move and has legitimately changed since.
