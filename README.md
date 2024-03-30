# Handling database schema migrations via Alembic
## Initialize in your project
`alembic init alembic`
## Configure alembic
Open the `alembic.ini` file and update the `sqlachemy.url` option with your database connection URL
Open the `alembic/env.py` file, add your model's MetaData object, and update the `target_metadata` variable accordingly
## Create a revision
`alembic revision --autogenerate -m "Initial migration"`
## Review the generated migration script
Open the generated migration script file and review the upgrade() and downgrade() functions. These functions define the steps to apply or revert the schema changes, respectively
## Apply the migration
`alembic upgrade head`