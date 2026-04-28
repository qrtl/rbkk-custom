This module adds a stored computed `Many2one` field (`analytic_plan_account_id`) to
models that carry an `analytic_distribution`. The field extracts the analytic account
belonging to a configurable analytic plan, enabling grouping and filtering by that
account directly on the model.

## How it works

A single mixin (`analytic.plan.account.mixin`) defines the field and compute logic.
Each model that inherits the mixin sets the class attribute
`_analytic_plan_config_param` to an `ir.config_parameter` key, which stores the ID
of the analytic plan to filter by. Because `analytic_plan_account_id` is stored, it
supports native group-by and search without custom queries.

## Configuration

Go to **Purchase > Configuration > Settings** and select the analytic plan to use
for purchase order lines under **Analytic Plan Field**.

## Extending to other models

Inherit the mixin and set `_analytic_plan_config_param`:

```python
class AccountMoveLine(models.Model):
    _inherit = ["account.move.line", "analytic.plan.account.mixin"]
    _analytic_plan_config_param = "analytic_plan_field.account_move_line.plan_id"
```

Then add a corresponding `Many2one` field to `res.config.settings` with the matching
`config_parameter` key.
