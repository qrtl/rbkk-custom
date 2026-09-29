Enter the **Acceptance Number** of each line in the *Operations* tab of the
transfer. It may be left empty, in which case the field is printed blank.

For a product with tracking the field is read-only there, and is entered per lot
in the *Detailed Operations* of the transfer instead; the line then shows the
summary of the numbers of its lots. For a product without tracking, a number
entered on the line is applied to its detailed operations.

Then go to *Inventory > Transfers*, select one or more transfers, and use *Print >
Acceptance Label*. Three labels are printed per sheet, and the labels of a
transfer stay together in the order of the selected transfers.

One label is printed per detailed operation, so confirm the transfer first:
the operations, and with them the labels, only exist from then on.

Cancelled lines are not printed. The arrival date stays blank as long as the
configured date field is empty, which is the case until the transfer is done
with the default setting.

The lot number and the expiration date are taken from the lot of the operation,
so they stay blank until the lot is assigned in the *Detailed Operations* of the
transfer. A line received in several lots prints one label per lot, each with
that lot's own number, acceptance number and expiration date. A lot without an
expiration date prints the date blank.

Transfers can be searched by acceptance number from the search bar of the
transfer list, and the numbers received under a lot are shown on the lot itself.
