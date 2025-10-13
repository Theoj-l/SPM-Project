-- Migration script to add missing fields to subtasks table
-- Run this in your Supabase SQL editor

-- Add missing columns to subtasks table
ALTER TABLE subtasks 
ADD COLUMN IF NOT EXISTS due_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS notes TEXT,
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subtasks_due_date ON subtasks(due_date);
CREATE INDEX IF NOT EXISTS idx_subtasks_tags ON subtasks USING GIN(tags);

-- Verify the table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'subtasks' 
ORDER BY ordinal_position;
