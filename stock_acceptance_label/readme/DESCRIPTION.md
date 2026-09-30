This module adds an acceptance label that is printed from transfers, three labels
per A4 portrait sheet (one per horizontal band of the sheet).

Each label shows the following rows, in the same layout:

- the product name;
- the acceptance number;
- the model number (product internal reference);
- the lot number the goods are received in, blank as long as no lot is
  assigned;
- the expiration date of that lot, blank when it has none;
- the arrival date (the effective date of the transfer, or any other date field
  selected in the settings);
- a status area with checkboxes to be ticked by hand, which can be edited in the
  settings;
- the product barcode (Code128).

One label is printed per detailed operation of the transfer, so a line received
in several lots prints a label per lot, each with its own acceptance number and
lot number. Several transfers can be selected at once so that all their labels
are printed in a single PDF.

The detailed operations are created when the transfer is confirmed, so a
transfer still in draft has nothing to print.

The printed acceptance number comes from `stock_acceptance_number`.
