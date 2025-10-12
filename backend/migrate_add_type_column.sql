-- Migration script to add type column to tasks table
-- Run this in your Supabase SQL editor

-- Add type column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'active';

-- Create index for better performance when filtering by type
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type);

-- Update any existing tasks to have type = 'active' (this is the default, but being explicit)
UPDATE tasks SET type = 'active' WHERE type IS NULL;

-- Add check constraint to ensure type is either 'active' or 'archived'
ALTER TABLE tasks ADD CONSTRAINT check_task_type CHECK (type IN ('active', 'archived'));

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'tasks' AND column_name = 'type';
