The equipment Status (Preparing, Operating, Idle, Retired, Scrapped) gates
usability: only equipment in the Operating status can be usable. In any other
status the equipment is unusable regardless of its maintenance result. Equipment
whose Scrap Date has been reached is unusable as well, whatever its status.

Equipment under a manufacturer warranty is usable until its Warranty Expiration
Date, as long as it is in the Operating status and its latest maintenance result
is not Failed. Once the warranty has expired, usability is computed as below, so
record the first maintenance result before that date to keep the equipment
usable.

Equipment that is not subject to maintenance can be flagged with Maintenance
Not Required. Its maintenance request results are then excluded from the
usability evaluation: the equipment is usable while it is in the Operating
status, and unusable in any other status.

Set the Maintenance Result to Passed or Failed before completing a maintenance
request (moving it to a done stage). Completing a request without a result is
blocked, unless its equipment is flagged Maintenance Not Required. For equipment
in the Operating status, usability is then computed from the latest completed
request by close date:

- Failed result: the equipment is unusable.
- Passed result, within the validity period: the equipment is usable.
- Passed result, past the validity period: the equipment is unusable.
- No result yet: the equipment usability is unknown.

The close date is the user's current date when the request is completed, unless
one was recorded beforehand, which is kept. It cannot be in the future, and it is
cleared when the request is reopened.

The validity period runs from the latest completed maintenance result date and
defaults to 12 months. Configure it in Settings > Maintenance > Usability
Validity Period (for example 13 or 14 months). Usability is evaluated from the
current date, so equipment becomes unusable automatically once the validity
period elapses.

The validity always extends to the end of the target month. For example, with a
result passed on 15 June and a 13-month validity period, the equipment stays
usable until 31 July of the following year and becomes unusable on 1 August.

The equipment form and list show this date as Usable Until: the later of the
warranty expiration date and the end of the validity period of the latest passed
result. It is empty when the latest result is Failed.
