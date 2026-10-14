This module adds attributes to maintenance equipment and maintenance requests.

It also allows to set an alert period on a maintenance request. A daily
scheduled action creates a *Maintenance Alert* activity for the technician (or
the equipment technician if none is set) once the alert period before the
scheduled date is reached. The alert is dropped and sent again when the
scheduled date or the alert period is changed, and it is marked as done when the
request is completed.

Every internal user can read the equipment register and all maintenance
requests, regardless of the equipment and requests they follow. The standard
access rules only let a user see the equipment they follow and the requests they
own, follow or are assigned to, which leaves the Equipment and Maintenance
Requests menus mostly empty for anybody who is not an Equipment Manager.
Creating and editing equipment stays restricted to the Equipment Manager group,
and editing requests stays under the standard rules.
