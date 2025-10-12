-- Database schema for SPM Project
-- This file contains the SQL commands to create the necessary tables for the project management system

-- Add archived field to existing tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- Comments table for tasks
CREATE TABLE IF NOT EXISTS task_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sub-tasks table
CREATE TABLE IF NOT EXISTS subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    parent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'completed', 'blocked')),
    assignee_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task files table
CREATE TABLE IF NOT EXISTS task_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(500) NOT NULL, -- Storage path
    original_filename VARCHAR(255) NOT NULL, -- Original filename
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    download_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_task_comments_task_id ON task_comments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_comments_user_id ON task_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_task_comments_created_at ON task_comments(created_at);

CREATE INDEX IF NOT EXISTS idx_subtasks_parent_task_id ON subtasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_subtasks_status ON subtasks(status);
CREATE INDEX IF NOT EXISTS idx_subtasks_created_at ON subtasks(created_at);

CREATE INDEX IF NOT EXISTS idx_task_files_task_id ON task_files(task_id);
CREATE INDEX IF NOT EXISTS idx_task_files_uploaded_by ON task_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_task_files_created_at ON task_files(created_at);

-- Create storage bucket for task files (run this in Supabase dashboard or via SQL)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('task-files', 'task-files', true);

-- Set up Row Level Security (RLS) policies
ALTER TABLE task_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE subtasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_files ENABLE ROW LEVEL SECURITY;

-- Comments policies
CREATE POLICY "Users can view comments for tasks they have access to" ON task_comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = task_comments.task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can create comments for tasks they have access to" ON task_comments
    FOR INSERT WITH CHECK (
        user_id = auth.uid() AND
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = task_comments.task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can delete their own comments" ON task_comments
    FOR DELETE USING (user_id = auth.uid());

-- Sub-tasks policies
CREATE POLICY "Users can view subtasks for tasks they have access to" ON subtasks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can create subtasks for tasks they have access to" ON subtasks
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can update subtasks for tasks they have access to" ON subtasks
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can delete subtasks for tasks they have access to" ON subtasks
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = subtasks.parent_task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

-- File policies
CREATE POLICY "Users can view files for tasks they have access to" ON task_files
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = task_files.task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can upload files for tasks they have access to" ON task_files
    FOR INSERT WITH CHECK (
        uploaded_by = auth.uid() AND
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = task_files.task_id
            AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
        )
    );

CREATE POLICY "Users can delete files they uploaded" ON task_files
    FOR DELETE USING (uploaded_by = auth.uid());
