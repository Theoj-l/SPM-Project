-- Check if task_comments table exists and has data
-- Run this in your Supabase SQL editor

-- Check if table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'task_comments';

-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'task_comments' 
ORDER BY ordinal_position;

-- Check if there are any comments
SELECT COUNT(*) as comment_count FROM task_comments;

-- Show sample data if any exists
SELECT * FROM task_comments LIMIT 5;
