-- Migration script to add comments, sub-tasks, and file upload support
-- Run this in your Supabase SQL editor

-- 1. Create task_comments table (with support for sub-comments)
CREATE TABLE IF NOT EXISTS task_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES task_comments(id) ON DELETE CASCADE, -- For sub-comments
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_task_comments_task_id ON task_comments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_comments_user_id ON task_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_task_comments_parent_id ON task_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_task_comments_created_at ON task_comments(created_at);

-- 2. Create subtasks table
CREATE TABLE IF NOT EXISTS subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'completed', 'blocked')),
    assigned UUID[] DEFAULT '{}', -- Array of user IDs (similar to tasks.assigned)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subtasks_parent_task_id ON subtasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_subtasks_status ON subtasks(status);
CREATE INDEX IF NOT EXISTS idx_subtasks_assigned ON subtasks USING GIN(assigned);

-- 3. Create task_files table
CREATE TABLE IF NOT EXISTS task_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path VARCHAR(500) NOT NULL, -- Path in Supabase Storage bucket
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_task_files_task_id ON task_files(task_id);
CREATE INDEX IF NOT EXISTS idx_task_files_user_id ON task_files(user_id);
CREATE INDEX IF NOT EXISTS idx_task_files_created_at ON task_files(created_at);

-- 4. Create updated_at trigger function (if it doesn't exist)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. Add updated_at triggers
CREATE TRIGGER update_task_comments_updated_at 
    BEFORE UPDATE ON task_comments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subtasks_updated_at 
    BEFORE UPDATE ON subtasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6. Add Row Level Security (RLS) policies
-- Enable RLS on all tables
ALTER TABLE task_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE subtasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_files ENABLE ROW LEVEL SECURITY;

-- Task comments policies
CREATE POLICY "Users can view comments for tasks they have access to" ON task_comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = task_comments.task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can create comments for tasks they have access to" ON task_comments
    FOR INSERT WITH CHECK (
        user_id::uuid = auth.uid() AND
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = task_comments.task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can update their own comments" ON task_comments
    FOR UPDATE USING (user_id::uuid = auth.uid());

-- Allow all authenticated users to delete comments (admin check will be handled in frontend)
CREATE POLICY "Users can delete comments" ON task_comments
    FOR DELETE USING (true);

-- Subtasks policies
CREATE POLICY "Users can view subtasks for tasks they have access to" ON subtasks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can create subtasks for tasks they have access to" ON subtasks
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can update subtasks for tasks they have access to" ON subtasks
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can delete subtasks for tasks they have access to" ON subtasks
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

-- Task files policies
CREATE POLICY "Users can view files for tasks they have access to" ON task_files
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = task_files.task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can upload files for tasks they have access to" ON task_files
    FOR INSERT WITH CHECK (
        user_id::uuid = auth.uid() AND
        EXISTS (
            SELECT 1 FROM tasks t
            LEFT JOIN project_members pm ON t.project_id = pm.project_id
            WHERE t.id = task_files.task_id
            AND (
                t.assigned @> ARRAY[auth.uid()::text] OR
                pm.user_id::uuid = auth.uid() OR
                EXISTS (SELECT 1 FROM projects p WHERE p.id = t.project_id AND p.owner_id::uuid = auth.uid())
            )
        )
    );

CREATE POLICY "Users can delete their own files" ON task_files
    FOR DELETE USING (user_id::uuid = auth.uid());

-- 7. Grant necessary permissions
GRANT ALL ON task_comments TO authenticated;
GRANT ALL ON subtasks TO authenticated;
GRANT ALL ON task_files TO authenticated;

-- 8. Create storage bucket policy for task_files bucket
-- Note: You'll need to run this in the Supabase dashboard under Storage > Policies
-- or use the Supabase client to create the bucket policy

-- Example bucket policy (run this in Supabase dashboard):
/*
{
  "bucket": "task_files",
  "policy": "Users can upload files for tasks they have access to",
  "definition": "bucket_id = 'task_files' AND auth.uid()::text = (storage.foldername(name))[1]",
  "check": "bucket_id = 'task_files' AND auth.uid()::text = (storage.foldername(name))[1]"
}
*/
