The settings of the label are in *Inventory > Configuration > Settings >
Acceptance Label*.

**Arrival Date** selects the date printed as the arrival date. Any date or
datetime field of the transfer or of its lines can be selected, including the
fields added by other modules, and datetime fields are converted to the user
time zone.

The effective date of the transfer (*Date of Transfer*) is used by default, and
also when the selected field is emptied or points to a field that does not exist
anymore.

**Status Area** holds the content of the status row, and can be edited freely.
It comes filled in with the default area, so that it only has to be adjusted:

```
□ Under Inspection
↓
□ Conforming or □ Rejected
```

Keep the area within a few lines: the label has a fixed height, and anything
that does not fit in its band is cut off. Emptying the setting restores the
default area, which follows the language of the printing user, while an area
entered here is printed as such in every language.
