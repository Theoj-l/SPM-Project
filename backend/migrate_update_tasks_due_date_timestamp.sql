-- Migration script to update tasks table due_date column to TIMESTAMP
-- Run this in your Supabase SQL editor

-- Update the due_date column in tasks table to support time
ALTER TABLE tasks 
ALTER COLUMN due_date TYPE TIMESTAMP USING due_date::TIMESTAMP;

-- Add index for better performance on timestamp queries
CREATE INDEX IF NOT EXISTS idx_tasks_due_date_timestamp ON tasks(due_date);

-- Verify the table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'tasks' AND column_name = 'due_date';
