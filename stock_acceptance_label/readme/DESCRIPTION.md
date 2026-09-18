This module adds an acceptance label that is printed from transfers, three labels
per A4 portrait sheet (one per horizontal band of the sheet).

Each label shows the following rows, in the same layout:

- the product name;
- the acceptance number;
- the model number (product internal reference);
- the lot number of the line, blank as long as no lot is assigned;
- the expiration date of that lot, blank when it has none;
- the arrival date (the effective date of the transfer, or any other date field
  selected in the settings);
- a status area with checkboxes to be ticked by hand, which can be edited in the
  settings;
- the product barcode (Code128).

One label is printed per transfer line, and several transfers can be selected at
once so that all their lines are printed in a single PDF.

It also adds an **Acceptance Number** field, which is where the printed
acceptance number comes from. The number is held by the detailed operations of
the transfer, so that a line received in several lots can be numbered per lot,
and the transfer line shows the summary of the numbers of its operations.

Each lot keeps the acceptance numbers it was received under, and a lot received
several times shows them all. They follow the receipts: a number corrected, or a
receipt cancelled after the fact, drops out of the lot.

Transfers can be searched by acceptance number.
