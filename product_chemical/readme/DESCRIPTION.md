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

* **Laws** — referenced by products.
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

## Chemical consumption

Consumption is tracked by moving the goods, so that the amount consumed is
whatever the stock move says it is. Configure it in two steps:

1. Flag the locations the substance is used up through — a production
   location, or an inventory adjustment location standing for a scrapping or a
   non-manufacturing issue — with **Chemical Consumption Location** on the
   location form. A virtual location is the usual choice; a physical bench
   works just as well.
2. Enable **Track Chemical Consumption** on the products whose consumption has
   to be followed. The flag is offered on chemical products only.

Issuing such a product out of stock into a consumption location then records
how much of each contained substance was consumed, one record per substance,
listed in the **Chemical Consumption** report. Moving it back out records the
same amounts with the opposite sign, so returning an unused remainder cancels
the consumption it was booked against.

| Move | Recorded as |
| --- | --- |
| Internal location → consumption location | consumption, positive |
| Consumption location → internal location | return, negative |
| Anything else | not recorded |

A move counts only when exactly one of its two sides is a consumption location
and the other one is internal, i.e. holds the stock the substance is taken
from or returned to. The consumption location itself may be of any kind, which
is what lets a virtual one be used. Receipts, deliveries and ordinary internal
transfers are deliberately left out: they relocate the substance
without using any of it, and the amount held at each location is already
reported by **Chemicals by Location**. Amounts are converted into the
aggregation unit in the same way as that report, so the two agree.

Unlike the on-hand report, these records are a snapshot: they keep the content
rate that applied when the move was validated, so revising the composition of a
product does not rewrite what was handled in the past. An inventory manager can
still correct a record from its form view when the composition was wrong at the
time, and the amount is recalculated from the corrected rate.

The **Update Chemical Amounts** action, available to inventory managers from
the stock move list and from the Chemical Consumption list, records the
consumption of moves that were validated before the module was installed, and
rebuilds them when the composition of a product was registered wrongly. The
rebuild replaces the records of the whole move, so a substance added to or
removed from the product is reflected too — which also means the manual
corrections made on those records are lost. Bear in mind that a rebuild applies
the composition registered *today*: it cannot restore a rate that was correct
at the time of the move and has legitimately changed since.
