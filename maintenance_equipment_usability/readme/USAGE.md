The equipment Status (Preparing, Operating, Idle, Disposal / Scrapped) gates
usability: only equipment in the Operating status can be usable. In any other
status the equipment is unusable regardless of its maintenance result.

When a maintenance request is completed (it reaches a done stage), set its
Maintenance Result to Passed or Failed. For equipment in the Operating status,
usability is then computed from the latest completed request by completion date:

- Failed result: the equipment is unusable.
- Passed result, within the grace period: the equipment is usable.
- Passed result, past the grace period: the equipment is unusable.
- No result yet: the equipment usability is unknown.

The grace period runs from the latest completed maintenance result date and
defaults to 12 months. Configure it in Settings > Maintenance > Usability
Grace Period (for example 13 or 14 months). Usability is evaluated from the
current date, so equipment becomes unusable automatically once the grace
period elapses.
