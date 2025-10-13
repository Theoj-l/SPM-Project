-- Migration script to add status constraint to tasks table
-- Run this in your Supabase SQL editor

-- Add check constraint to ensure status is one of the valid values
ALTER TABLE tasks ADD CONSTRAINT check_task_status CHECK (status IN ('todo', 'in_progress', 'completed', 'blocked'));

-- Verify the constraint was added
SELECT conname, contype, pg_get_constraintdef(oid) as definition
FROM pg_constraint 
WHERE conrelid = 'tasks'::regclass AND conname = 'check_task_status';
