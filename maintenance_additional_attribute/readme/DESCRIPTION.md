This module adds attributes to maintenance equipment and maintenance requests.

It also allows to set an alert period on a maintenance request. A daily
scheduled action creates a *Maintenance Alert* activity for the technician (or
the owner if no technician is assigned) once the alert period before the
scheduled date is reached. The alert is dropped and sent again when the
scheduled date or the alert period is changed, and it is marked as done when the
request is completed.

Every internal user can read the equipment register, regardless of the equipment
they follow. The standard access rule only lets a user see the equipment they
follow, which leaves the Equipment menu empty for anybody who is not an
Equipment Manager. Creating and editing equipment stays restricted to the
Equipment Manager group.
