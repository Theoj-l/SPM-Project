-- Check the actual structure of the subtasks table
-- Run this in your Supabase SQL editor

-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'subtasks' 
ORDER BY ordinal_position;

-- Check if there are any subtasks
SELECT COUNT(*) as subtask_count FROM subtasks;

-- Show sample data if any exists
SELECT * FROM subtasks LIMIT 3;
