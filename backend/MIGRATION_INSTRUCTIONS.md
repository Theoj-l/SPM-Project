# Database Migration Instructions

## Issue

The application is trying to use a `type` column in the `tasks` table that doesn't exist yet, causing the error:

```
column tasks.type does not exist
```

## Solution

You need to run a database migration to add the `type` column to your `tasks` table.

## Steps to Fix

### 1. Open Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to the **SQL Editor** section

### 2. Run the Migration

Copy and paste the following SQL command into the SQL editor and execute it:

```sql
-- Add type column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'active';

-- Create index for better performance when filtering by type
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type);

-- Update any existing tasks to have type = 'active' (this is the default, but being explicit)
UPDATE tasks SET type = 'active' WHERE type IS NULL;

-- Add check constraint to ensure type is either 'active' or 'archived'
ALTER TABLE tasks ADD CONSTRAINT check_task_type CHECK (type IN ('active', 'archived'));
```

### 3. Verify the Migration

Run this query to verify the column was added successfully:

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'tasks' AND column_name = 'type';
```

You should see a row with:

- `column_name`: type
- `data_type`: character varying
- `is_nullable`: YES
- `column_default`: active

### 4. Restart Your Backend

After running the migration, restart your backend server to ensure it picks up the database changes.

## Alternative: Use the Migration File

You can also use the provided migration file:

1. Open `backend/migrate_add_type_column.sql`
2. Copy the contents
3. Paste into Supabase SQL Editor
4. Execute

## What This Enables

After running this migration, the following features will work:

- ✅ Archive tasks by setting type to "archived"
- ✅ View archived tasks in the archive page
- ✅ Restore archived tasks by setting type to "active"
- ✅ Filter out archived tasks from active task lists
- ✅ All existing tasks will have type = "active" by default

## How It Works

- **Active Tasks**: `type = "active"` (default for new tasks)
- **Archived Tasks**: `type = "archived"` (when tasks are archived)
- **Filtering**: The system automatically filters by type to show only active tasks in project views
- **Archive Page**: Shows only tasks with `type = "archived"`

## Troubleshooting

If you encounter any issues:

1. Make sure you're running the SQL in the correct Supabase project
2. Check that you have the necessary permissions to alter tables
3. Verify the `tasks` table exists in your database
4. Check the Supabase logs for any error messages

## Next Steps

After the migration is complete:

1. The archive functionality will work immediately
2. All existing tasks will have `type = "active"` by default
3. You can start archiving tasks instead of deleting them
4. Visit `/archived` to see archived tasks
5. Use the archive/restore buttons to manage task lifecycle
